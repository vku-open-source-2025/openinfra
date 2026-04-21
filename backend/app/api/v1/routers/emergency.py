"""Emergency command-center API router."""

from datetime import datetime
import logging
from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi import Request
from pydantic import BaseModel, Field

from app.api.v1.dependencies import get_after_action_report_service, get_emergency_service
from app.core.config import settings
from app.domain.models.after_action_report import AfterActionGenerateRequest
from app.api.v1.middleware import get_current_user
from app.domain.models.emergency import (
    EmergencyEvent,
    EmergencyEventCreate,
    EmergencyEventUpdate,
    EmergencyStatus,
)
from app.domain.models.user import User, UserRole
from app.domain.services.after_action_report_service import AfterActionReportService
from app.domain.services.emergency_service import EmergencyService
from app.middleware.request_id import get_or_create_request_id, merge_request_id_metadata

router = APIRouter()
logger = logging.getLogger(__name__)


class ResolveEmergencyRequest(BaseModel):
    """Request payload for resolving an emergency event."""

    resolution_note: Optional[str] = Field(default=None, max_length=1000)


class SosconnStatusResponse(BaseModel):
    """SOSConn llm-service health and configuration status."""

    provider: str = "github-copilot"
    configured: bool = False
    reachable: bool = False
    model: Optional[str] = None
    detail: Optional[str] = None
    checked_at: datetime
    base_url: str


class SosTimelineItemResponse(BaseModel):
    """SOS-linked event item for command center timeline."""

    event_id: str
    event_code: Optional[str] = None
    title: str
    severity: str
    status: str
    created_at: datetime
    source_ref: Optional[str] = None
    sla_breach_count: int = 0
    last_update: datetime


def _ensure_operator(user: User):
    """Allow only admin and technician roles for emergency actions."""
    if user.role not in {UserRole.ADMIN, UserRole.TECHNICIAN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for emergency operations",
        )


def _extract_sos_source_ref(event_doc: dict) -> Optional[str]:
    """Get the best available upstream SOS reference for timeline display."""
    metadata = event_doc.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    candidates = (
        metadata.get("source_ref"),
        metadata.get("sos_report_id"),
        event_doc.get("_contrib_sos_id"),
        metadata.get("request_id"),
        metadata.get("external_ref"),
    )
    for candidate in candidates:
        if candidate:
            return str(candidate)
    return None


@router.get("/sosconn/status", response_model=SosconnStatusResponse)
async def get_sosconn_status(
    current_user: User = Depends(get_current_user),
):
    """Get llm-service status used by SOSConn command workflows."""
    _ensure_operator(current_user)

    base_url = settings.SOSCONN_LLM_BASE_URL.rstrip("/")
    target_url = f"{base_url}/api/v1/ai/status"
    checked_at = datetime.utcnow()

    try:
        async with httpx.AsyncClient(timeout=settings.SOSCONN_LLM_TIMEOUT_SECONDS) as client:
            response = await client.get(target_url)
            response.raise_for_status()

        payload = response.json() if response.content else {}
        return SosconnStatusResponse(
            provider=str(payload.get("provider") or "github-copilot"),
            configured=bool(payload.get("configured")),
            reachable=True,
            model=payload.get("model"),
            checked_at=checked_at,
            base_url=base_url,
        )
    except httpx.HTTPStatusError as exc:
        detail = f"llm-service returned {exc.response.status_code}"
    except Exception as exc:
        detail = str(exc)

    return SosconnStatusResponse(
        provider="github-copilot",
        configured=False,
        reachable=False,
        detail=detail,
        checked_at=checked_at,
        base_url=base_url,
    )


@router.get("/sos/timeline", response_model=List[SosTimelineItemResponse])
async def get_sos_timeline(
    limit: int = Query(30, ge=1, le=200),
    current_user: User = Depends(get_current_user),
):
    """Return recent SOS-linked emergency events for command center timeline."""
    _ensure_operator(current_user)

    from app.infrastructure.database.mongodb import get_database

    db = await get_database()
    emergency_collection = db["emergency_events"]
    sla_collection = db["emergency_sla_breaches"]

    sos_query = {
        "$or": [
            {"source": "sosconn"},
            {"metadata.sos_report_id": {"$exists": True, "$ne": None}},
            {"_contrib_sos_id": {"$exists": True, "$ne": None}},
        ]
    }

    cursor = (
        emergency_collection.find(
            sos_query,
            {
                "_id": 1,
                "event_code": 1,
                "title": 1,
                "severity": 1,
                "status": 1,
                "created_at": 1,
                "updated_at": 1,
                "metadata": 1,
                "_contrib_sos_id": 1,
            },
        )
        .sort([("updated_at", -1), ("created_at", -1)])
        .limit(limit)
    )
    event_docs = await cursor.to_list(length=limit)

    event_ids: List[str] = []
    for event_doc in event_docs:
        event_id = event_doc.get("_id")
        if event_id is not None:
            event_ids.append(str(event_id))

    sla_breach_counts: Dict[str, int] = {}
    if event_ids:
        pipeline = [
            {"$match": {"event_id": {"$in": event_ids}}},
            {"$group": {"_id": "$event_id", "count": {"$sum": 1}}},
        ]
        async for row in sla_collection.aggregate(pipeline):
            row_id = row.get("_id")
            if row_id is not None:
                sla_breach_counts[str(row_id)] = int(row.get("count") or 0)

    timeline_items: List[SosTimelineItemResponse] = []
    for event_doc in event_docs:
        raw_event_id = event_doc.get("_id")
        if raw_event_id is None:
            continue

        event_id = str(raw_event_id)
        created_at = event_doc.get("created_at") or event_doc.get("updated_at") or datetime.utcnow()
        last_update = event_doc.get("updated_at") or created_at

        timeline_items.append(
            SosTimelineItemResponse(
                event_id=event_id,
                event_code=event_doc.get("event_code"),
                title=str(event_doc.get("title") or f"SOS Event {event_id}"),
                severity=str(event_doc.get("severity") or "unknown"),
                status=str(event_doc.get("status") or "unknown"),
                created_at=created_at,
                source_ref=_extract_sos_source_ref(event_doc),
                sla_breach_count=sla_breach_counts.get(event_id, 0),
                last_update=last_update,
            )
        )

    return timeline_items


class PublicEmergencyEvent(BaseModel):
    """Safe subset of an emergency event for public/citizen consumption."""

    id: str
    title: str
    event_type: str
    severity: str
    status: str
    location: Optional[Dict[str, Optional[str]]] = None
    geometry: Optional[Dict[str, object]] = None
    started_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


@router.get("/public", response_model=List[PublicEmergencyEvent])
async def list_public_emergency_events(
    limit: int = Query(50, ge=1, le=200),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Citizen-facing list of active emergency events — no auth required.

    Returns a safe subset (title, type, severity, location, geometry, timestamps).
    Internal fields (created_by, tags, estimated_impact, metadata) are hidden.
    """
    events = await emergency_service.list_events(
        skip=0,
        limit=limit,
        status=EmergencyStatus.ACTIVE.value,
    )
    items: List[PublicEmergencyEvent] = []
    for event in events:
        loc_payload: Optional[Dict[str, Optional[str]]] = None
        geometry: Optional[Dict[str, object]] = None
        if event.location is not None:
            loc_payload = {
                "address": event.location.address,
                "ward": event.location.ward,
                "district": event.location.district,
                "city": event.location.city,
            }
            if event.location.geometry:
                geometry = dict(event.location.geometry)
        items.append(
            PublicEmergencyEvent(
                id=str(event.id),
                title=event.title,
                event_type=event.event_type.value,
                severity=event.severity.value,
                status=event.status.value,
                location=loc_payload,
                geometry=geometry,
                started_at=event.started_at,
                created_at=event.created_at,
            )
        )
    return items


@router.get("", response_model=List[EmergencyEvent])
async def list_emergencies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    severity: Optional[str] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None, description="Search by title/code"),
    current_user: User = Depends(get_current_user),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """List emergency events for command center users."""
    _ensure_operator(current_user)
    return await emergency_service.list_events(
        skip=skip,
        limit=limit,
        status=status_filter,
        severity=severity,
        event_type=event_type,
        query_text=q,
    )


@router.get("/{event_id}", response_model=EmergencyEvent)
async def get_emergency_by_id(
    event_id: str,
    current_user: User = Depends(get_current_user),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Get a specific emergency event."""
    _ensure_operator(current_user)
    return await emergency_service.get_event_by_id(event_id)


@router.post("", response_model=EmergencyEvent, status_code=status.HTTP_201_CREATED)
async def create_emergency(
    request: Request,
    payload: EmergencyEventCreate,
    current_user: User = Depends(get_current_user),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Create a new emergency event."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    payload = payload.model_copy(
        update={"metadata": merge_request_id_metadata(payload.metadata, request_id)}
    )
    return await emergency_service.create_event(
        payload,
        created_by=str(current_user.id),
        request_id=request_id,
    )


@router.put("/{event_id}", response_model=EmergencyEvent)
async def update_emergency(
    request: Request,
    event_id: str,
    updates: EmergencyEventUpdate,
    current_user: User = Depends(get_current_user),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Update an existing emergency event."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    updates = updates.model_copy(
        update={"metadata": merge_request_id_metadata(updates.metadata, request_id)}
    )
    return await emergency_service.update_event(
        event_id,
        updates,
        updated_by=str(current_user.id),
        request_id=request_id,
    )


@router.post("/{event_id}/resolve", response_model=EmergencyEvent)
async def resolve_emergency(
    request: Request,
    event_id: str,
    payload: ResolveEmergencyRequest,
    current_user: User = Depends(get_current_user),
    emergency_service: EmergencyService = Depends(get_emergency_service),
    after_action_service: AfterActionReportService = Depends(get_after_action_report_service),
):
    """Resolve an emergency event from command center."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    resolved = await emergency_service.resolve_event(
        event_id,
        resolution_note=payload.resolution_note,
        updated_by=str(current_user.id),
        request_id=request_id,
    )

    # Do not block resolve flow if report generation fails.
    try:
        await after_action_service.generate_for_event(
            AfterActionGenerateRequest(
                emergency_event_id=event_id,
                metadata=merge_request_id_metadata(
                    {"auto_generated_on_resolve": True},
                    request_id,
                ),
            ),
            generated_by=str(current_user.id),
        )
    except Exception:
        logger.exception("Failed to auto-generate after-action report for event %s", event_id)

    return resolved
