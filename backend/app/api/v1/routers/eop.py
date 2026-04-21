"""Emergency operation plan API router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.api.v1.dependencies import get_dispatch_service, get_eop_service
from app.api.v1.middleware import get_current_user
from app.domain.models.dispatch_order import DispatchOrder
from app.domain.models.eop_plan import (
    EOPGenerateRequest,
    EOPMarkdownUpdate,
    EOPPlan,
    EOPPlanCreate,
    EOPPlanUpdate,
)
from app.domain.models.user import User, UserRole
from app.domain.services.dispatch_service import DispatchService
from app.domain.services.eop_service import EOPService
from app.middleware.request_id import get_or_create_request_id, merge_request_id_metadata

router = APIRouter()


class ApproveEOPRequest(BaseModel):
    """Payload for EOP approval action."""

    review_notes: Optional[str] = Field(default=None, max_length=2000)


def _ensure_operator(user: User):
    """Allow only operators to manage EOP workflows."""
    if user.role not in {UserRole.ADMIN, UserRole.TECHNICIAN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for EOP operations",
        )


@router.get("", response_model=List[EOPPlan])
async def list_eop_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    emergency_event_id: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    service: EOPService = Depends(get_eop_service),
):
    """List EOP plans for command center operators."""
    _ensure_operator(current_user)
    return await service.list_plans(
        skip=skip,
        limit=limit,
        emergency_event_id=emergency_event_id,
        status=status_filter,
    )


@router.get("/{plan_id}", response_model=EOPPlan)
async def get_eop_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    service: EOPService = Depends(get_eop_service),
):
    """Get one EOP plan by id."""
    _ensure_operator(current_user)
    return await service.get_plan_by_id(plan_id)


@router.post("", response_model=EOPPlan, status_code=status.HTTP_201_CREATED)
async def create_eop_plan(
    request: Request,
    payload: EOPPlanCreate,
    current_user: User = Depends(get_current_user),
    service: EOPService = Depends(get_eop_service),
):
    """Create a new EOP draft."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    payload = payload.model_copy(
        update={"metadata": merge_request_id_metadata(payload.metadata, request_id)}
    )
    return await service.create_plan(
        payload,
        created_by=str(current_user.id),
        request_id=request_id,
    )


@router.post("/generate-draft", response_model=EOPPlan, status_code=status.HTTP_201_CREATED)
async def generate_eop_draft(
    request: Request,
    payload: EOPGenerateRequest,
    current_user: User = Depends(get_current_user),
    service: EOPService = Depends(get_eop_service),
):
    """Generate AI-assisted EOP draft from emergency context."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    return await service.generate_draft(
        emergency_event_id=payload.emergency_event_id,
        generated_by=str(current_user.id),
        additional_context=payload.additional_context,
        force_new_version=payload.force_new_version,
        request_id=request_id,
    )


@router.put("/{plan_id}", response_model=EOPPlan)
async def update_eop_plan(
    request: Request,
    plan_id: str,
    payload: EOPPlanUpdate,
    current_user: User = Depends(get_current_user),
    service: EOPService = Depends(get_eop_service),
):
    """Update an existing EOP plan."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    payload = payload.model_copy(
        update={"metadata": merge_request_id_metadata(payload.metadata, request_id)}
    )
    return await service.update_plan(
        plan_id,
        payload,
        updated_by=str(current_user.id),
        request_id=request_id,
    )


@router.post("/{plan_id}/approve", response_model=EOPPlan)
async def approve_eop_plan(
    plan_id: str,
    payload: ApproveEOPRequest,
    current_user: User = Depends(get_current_user),
    service: EOPService = Depends(get_eop_service),
):
    """Approve an EOP plan."""
    _ensure_operator(current_user)
    return await service.approve_plan(
        plan_id,
        approved_by=str(current_user.id),
        review_notes=payload.review_notes,
    )


@router.post("/{plan_id}/publish", response_model=EOPPlan)
async def publish_eop_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    service: EOPService = Depends(get_eop_service),
):
    """Publish an approved EOP plan."""
    _ensure_operator(current_user)
    return await service.publish_plan(plan_id, published_by=str(current_user.id))


@router.patch("/{plan_id}/markdown", response_model=EOPPlan)
async def update_eop_markdown(
    plan_id: str,
    payload: EOPMarkdownUpdate,
    current_user: User = Depends(get_current_user),
    service: EOPService = Depends(get_eop_service),
):
    """Update the free-form markdown body of an EOP plan (coordinator edits)."""
    _ensure_operator(current_user)
    return await service.update_markdown(
        plan_id,
        markdown_body=payload.markdown_body,
        review_notes=payload.review_notes,
        updated_by=str(current_user.id),
    )


class EOPSubmitResponse(BaseModel):
    """Response of the submit-for-tasks action."""

    plan_id: str
    task_source: str
    orders: List[DispatchOrder]


@router.post("/{plan_id}/submit", response_model=EOPSubmitResponse)
async def submit_eop_for_tasks(
    request: Request,
    plan_id: str,
    current_user: User = Depends(get_current_user),
    service: EOPService = Depends(get_eop_service),
    dispatch_service: DispatchService = Depends(get_dispatch_service),
):
    """Submit edited EOP markdown, generate tasks via LLM, and create dispatch orders."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    result = await service.submit_for_tasks(
        plan_id,
        dispatch_service=dispatch_service,
        submitted_by=str(current_user.id),
        request_id=request_id,
    )
    return EOPSubmitResponse(**result)
