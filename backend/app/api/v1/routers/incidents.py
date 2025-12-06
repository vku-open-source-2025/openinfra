"""Incidents API router."""
from fastapi import APIRouter, Query, Depends, HTTPException, status
from typing import List, Optional
from app.domain.models.incident import (
    Incident, IncidentCreate, IncidentUpdate, IncidentCommentRequest
)
from app.domain.services.incident_service import IncidentService
from app.api.v1.dependencies import get_incident_service
from app.api.v1.middleware import get_current_user, get_optional_current_user
from app.domain.models.user import User
from app.domain.models.incident import ResolutionType

router = APIRouter()


@router.get("", response_model=List[Incident])
async def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    asset_id: Optional[str] = None,
    incident_service: IncidentService = Depends(get_incident_service)
):
    """List incidents with filtering, including asset information."""
    return await incident_service.list_incidents(
        skip, limit, status, severity, asset_id, None, populate_asset=True
    )


@router.post("", response_model=Incident, status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident_data: IncidentCreate,
    current_user: Optional[User] = Depends(get_optional_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Create a new incident (can be anonymous)."""
    reported_by = str(current_user.id) if current_user else None
    reporter_type = current_user.role.value if current_user else "citizen"
    return await incident_service.create_incident(incident_data, reported_by, reporter_type)


@router.get("/{incident_id}", response_model=Incident)
async def get_incident(
    incident_id: str,
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Get incident details."""
    return await incident_service.get_incident_by_id(incident_id)


@router.put("/{incident_id}", response_model=Incident)
async def update_incident(
    incident_id: str,
    updates: IncidentUpdate,
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Update incident."""
    return await incident_service.update_incident(incident_id, updates)


@router.post("/{incident_id}/acknowledge", response_model=Incident)
async def acknowledge_incident(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Acknowledge an incident."""
    return await incident_service.acknowledge_incident(incident_id, str(current_user.id))


@router.post("/{incident_id}/assign", response_model=Incident)
async def assign_incident(
    incident_id: str,
    assigned_to: str = Query(..., description="User ID to assign to"),
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Assign incident to a technician."""
    return await incident_service.assign_incident(incident_id, assigned_to, str(current_user.id))


@router.post("/{incident_id}/resolve", response_model=Incident)
async def resolve_incident(
    incident_id: str,
    resolution_notes: str = Query(..., description="Resolution notes"),
    resolution_type: ResolutionType = Query(..., description="Resolution type"),
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Resolve an incident."""
    return await incident_service.resolve_incident(
        incident_id,
        str(current_user.id),
        resolution_notes,
        resolution_type
    )


@router.post("/{incident_id}/comments", response_model=Incident)
async def add_comment(
    incident_id: str,
    comment: IncidentCommentRequest,
    current_user: Optional[User] = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Add comment to incident."""
    user_id = str(current_user.id) if current_user else None
    return await incident_service.add_comment(
        incident_id,
        comment.comment,
        user_id,
        comment.is_internal
    )


@router.post("/{incident_id}/upvote", response_model=Incident)
async def upvote_incident(
    incident_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Upvote or remove upvote from incident."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return await incident_service.upvote_incident(incident_id, str(current_user.id))


@router.post("/{incident_id}/create-maintenance", response_model=dict)
async def create_maintenance_from_incident(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Create a maintenance work order from incident."""
    maintenance_id = await incident_service.create_maintenance_from_incident(
        incident_id,
        str(current_user.id)
    )
    return {
        "incident_id": incident_id,
        "maintenance_id": maintenance_id,
        "message": "Maintenance work order created successfully"
    }


@router.post("/{incident_id}/approve-cost", response_model=Incident)
async def approve_incident_cost(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Approve maintenance cost and resolve incident."""
    # In a real app, check for ADMIN role here
    return await incident_service.approve_incident_resolution(
        incident_id,
        str(current_user.id)
    )
