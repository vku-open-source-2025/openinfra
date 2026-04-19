"""After-action reports API router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.v1.dependencies import get_after_action_report_service
from app.api.v1.middleware import get_current_user
from app.domain.models.after_action_report import (
    AfterActionGenerateRequest,
    AfterActionReport,
    AfterActionReportUpdate,
)
from app.domain.models.user import User, UserRole
from app.domain.services.after_action_report_service import AfterActionReportService
from app.middleware.request_id import get_or_create_request_id, merge_request_id_metadata

router = APIRouter()


def _ensure_operator(user: User):
    """Allow only operators for after-action report workflows."""
    if user.role not in {UserRole.ADMIN, UserRole.TECHNICIAN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for after-action operations",
        )


@router.get("", response_model=List[AfterActionReport])
async def list_after_action_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=300),
    emergency_event_id: Optional[str] = Query(default=None, alias="event_id"),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    service: AfterActionReportService = Depends(get_after_action_report_service),
):
    """List after-action reports."""
    _ensure_operator(current_user)
    return await service.list_reports(
        skip=skip,
        limit=limit,
        emergency_event_id=emergency_event_id,
        status=status_filter,
    )


@router.get("/{report_id}", response_model=AfterActionReport)
async def get_after_action_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    service: AfterActionReportService = Depends(get_after_action_report_service),
):
    """Get one after-action report."""
    _ensure_operator(current_user)
    return await service.get_report_by_id(report_id)


@router.post("/generate", response_model=AfterActionReport, status_code=status.HTTP_201_CREATED)
async def generate_after_action_report(
    request: Request,
    payload: AfterActionGenerateRequest,
    current_user: User = Depends(get_current_user),
    service: AfterActionReportService = Depends(get_after_action_report_service),
):
    """Generate after-action report for one emergency event."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    payload = payload.model_copy(
        update={"metadata": merge_request_id_metadata(payload.metadata, request_id)}
    )
    return await service.generate_for_event(
        payload,
        generated_by=str(current_user.id),
        request_id=request_id,
    )


@router.put("/{report_id}", response_model=AfterActionReport)
async def update_after_action_report(
    request: Request,
    report_id: str,
    payload: AfterActionReportUpdate,
    current_user: User = Depends(get_current_user),
    service: AfterActionReportService = Depends(get_after_action_report_service),
):
    """Update draft after-action report."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    payload = payload.model_copy(
        update={"metadata": merge_request_id_metadata(payload.metadata, request_id)}
    )
    return await service.update_report(
        report_id,
        payload,
        updated_by=str(current_user.id),
        request_id=request_id,
    )


@router.post("/{report_id}/publish", response_model=AfterActionReport)
async def publish_after_action_report(
    request: Request,
    report_id: str,
    current_user: User = Depends(get_current_user),
    service: AfterActionReportService = Depends(get_after_action_report_service),
):
    """Publish after-action report."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    return await service.publish_report(
        report_id,
        published_by=str(current_user.id),
        request_id=request_id,
    )
