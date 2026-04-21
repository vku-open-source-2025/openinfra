"""Emergency dispatch API router."""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.api.v1.dependencies import get_dispatch_service, get_user_service
from app.api.v1.middleware import get_current_user
from app.domain.models.dispatch_order import (
    DispatchAssignment,
    DispatchOrder,
    DispatchOrderCreate,
    DispatchOrderUpdate,
    DispatchStatus,
)
from app.domain.models.user import User, UserRole
from app.domain.services.dispatch_optimizer import optimize_dispatch_orders
from app.domain.services.dispatch_service import DispatchService
from app.domain.services.user_service import UserService
from app.middleware.request_id import get_or_create_request_id, merge_request_id_metadata

router = APIRouter()


class DispatchReoptimizeRequest(BaseModel):
    """Payload for manual dispatch optimization trigger."""

    max_orders: int = Field(default=200, ge=1, le=1000)
    force_reestimate_eta: bool = True


def _ensure_operator(user: User):
    """Allow only operators to manage dispatch workflows."""
    if user.role not in {UserRole.ADMIN, UserRole.TECHNICIAN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for dispatch operations",
        )


@router.get("", response_model=List[DispatchOrder])
async def list_dispatch_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    emergency_event_id: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    priority: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: DispatchService = Depends(get_dispatch_service),
):
    """List dispatch orders."""
    _ensure_operator(current_user)
    return await service.list_orders(
        skip=skip,
        limit=limit,
        emergency_event_id=emergency_event_id,
        status=status_filter,
        priority=priority,
    )


@router.get("/{order_id}", response_model=DispatchOrder)
async def get_dispatch_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    service: DispatchService = Depends(get_dispatch_service),
):
    """Get one dispatch order."""
    _ensure_operator(current_user)
    return await service.get_order_by_id(order_id)


@router.post("", response_model=DispatchOrder, status_code=status.HTTP_201_CREATED)
async def create_dispatch_order(
    request: Request,
    payload: DispatchOrderCreate,
    current_user: User = Depends(get_current_user),
    service: DispatchService = Depends(get_dispatch_service),
):
    """Create dispatch order from emergency operation panel."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    payload = payload.model_copy(
        update={"metadata": merge_request_id_metadata(payload.metadata, request_id)}
    )
    return await service.create_order(
        payload,
        assigned_by=str(current_user.id),
        request_id=request_id,
    )


@router.put("/{order_id}", response_model=DispatchOrder)
async def update_dispatch_order(
    request: Request,
    order_id: str,
    payload: DispatchOrderUpdate,
    current_user: User = Depends(get_current_user),
    service: DispatchService = Depends(get_dispatch_service),
):
    """Update dispatch order."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    payload = payload.model_copy(
        update={"metadata": merge_request_id_metadata(payload.metadata, request_id)}
    )
    return await service.update_order(
        order_id,
        payload,
        updated_by=str(current_user.id),
        request_id=request_id,
    )


@router.post("/{order_id}/assign", response_model=DispatchOrder)
async def assign_dispatch_order(
    request: Request,
    order_id: str,
    current_user: User = Depends(get_current_user),
    service: DispatchService = Depends(get_dispatch_service),
):
    """Mark dispatch order as assigned and started."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    return await service.assign_order(
        order_id,
        updated_by=str(current_user.id),
        request_id=request_id,
    )


@router.post("/{order_id}/complete", response_model=DispatchOrder)
async def complete_dispatch_order(
    request: Request,
    order_id: str,
    current_user: User = Depends(get_current_user),
    service: DispatchService = Depends(get_dispatch_service),
):
    """Mark dispatch order as completed."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    return await service.complete_order(
        order_id,
        updated_by=str(current_user.id),
        request_id=request_id,
    )


@router.post("/optimize", response_model=Dict[str, object])
async def optimize_dispatch_orders_manually(
    payload: DispatchReoptimizeRequest,
    current_user: User = Depends(get_current_user),
):
    """Run dispatch optimizer v2 manually from command center."""
    _ensure_operator(current_user)
    return await optimize_dispatch_orders(
        triggered_by=f"manual:{current_user.role.value}",
        max_orders=payload.max_orders,
        force_reestimate_eta=payload.force_reestimate_eta,
    )


class DispatchApproveRequest(BaseModel):
    """Payload for approve-and-assign action."""

    user_id: str = Field(min_length=1)
    notes: Optional[str] = None


@router.post("/{order_id}/approve", response_model=DispatchOrder)
async def approve_dispatch_order(
    request: Request,
    order_id: str,
    payload: DispatchApproveRequest,
    current_user: User = Depends(get_current_user),
    service: DispatchService = Depends(get_dispatch_service),
    user_service: UserService = Depends(get_user_service),
):
    """Approve a pending task by assigning it to a volunteer/technician."""
    _ensure_operator(current_user)
    assignee = await user_service.get_user_by_id(payload.user_id)
    if assignee.role not in {UserRole.VOLUNTEER, UserRole.TECHNICIAN, UserRole.ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignee must be a volunteer, technician, or admin user",
        )

    request_id = get_or_create_request_id(request)
    update_payload = DispatchOrderUpdate(
        status=DispatchStatus.ASSIGNED,
        assignments=[
            DispatchAssignment(
                assigned_user_id=payload.user_id,
                role=assignee.role.value,
                notes=payload.notes,
            )
        ],
    )
    return await service.update_order(
        order_id,
        update_payload,
        updated_by=str(current_user.id),
        request_id=request_id,
    )


@router.post("/{order_id}/reject", response_model=DispatchOrder)
async def reject_dispatch_order(
    request: Request,
    order_id: str,
    current_user: User = Depends(get_current_user),
    service: DispatchService = Depends(get_dispatch_service),
):
    """Reject a pending task — cancels the dispatch order."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    return await service.update_order(
        order_id,
        DispatchOrderUpdate(status=DispatchStatus.CANCELED),
        updated_by=str(current_user.id),
        request_id=request_id,
    )
