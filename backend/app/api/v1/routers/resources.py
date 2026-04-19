"""Emergency resources API router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from app.api.v1.dependencies import get_resource_service
from app.api.v1.middleware import get_current_user
from app.domain.models.resource_unit import ResourceStatus, ResourceUnit, ResourceUnitCreate, ResourceUnitUpdate
from app.domain.models.user import User, UserRole
from app.domain.services.resource_service import ResourceService
from app.middleware.request_id import get_or_create_request_id, merge_request_id_metadata

router = APIRouter()


class ResourceStatusRequest(BaseModel):
    """Payload for quick resource status update."""

    status: ResourceStatus


def _ensure_operator(user: User):
    """Allow only operators to manage resources."""
    if user.role not in {UserRole.ADMIN, UserRole.TECHNICIAN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for resource operations",
        )


@router.get("", response_model=List[ResourceUnit])
async def list_resources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    resource_type: Optional[str] = Query(default=None),
    district: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: ResourceService = Depends(get_resource_service),
):
    """List resource units with optional filtering."""
    _ensure_operator(current_user)
    return await service.list_resources(
        skip=skip,
        limit=limit,
        status=status_filter,
        resource_type=resource_type,
        district=district,
    )


@router.get("/{resource_id}", response_model=ResourceUnit)
async def get_resource(
    resource_id: str,
    current_user: User = Depends(get_current_user),
    service: ResourceService = Depends(get_resource_service),
):
    """Get one resource unit."""
    _ensure_operator(current_user)
    return await service.get_resource_by_id(resource_id)


@router.post("", response_model=ResourceUnit, status_code=status.HTTP_201_CREATED)
async def create_resource(
    request: Request,
    payload: ResourceUnitCreate,
    current_user: User = Depends(get_current_user),
    service: ResourceService = Depends(get_resource_service),
):
    """Create resource unit."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    payload = payload.model_copy(
        update={"metadata": merge_request_id_metadata(payload.metadata, request_id)}
    )
    return await service.create_resource(payload, request_id=request_id)


@router.put("/{resource_id}", response_model=ResourceUnit)
async def update_resource(
    request: Request,
    resource_id: str,
    payload: ResourceUnitUpdate,
    current_user: User = Depends(get_current_user),
    service: ResourceService = Depends(get_resource_service),
):
    """Update resource unit."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    payload = payload.model_copy(
        update={"metadata": merge_request_id_metadata(payload.metadata, request_id)}
    )
    return await service.update_resource(
        resource_id,
        payload,
        request_id=request_id,
    )


@router.post("/{resource_id}/status", response_model=ResourceUnit)
async def set_resource_status(
    request: Request,
    resource_id: str,
    payload: ResourceStatusRequest,
    current_user: User = Depends(get_current_user),
    service: ResourceService = Depends(get_resource_service),
):
    """Set resource availability status."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    return await service.set_resource_status(
        resource_id,
        payload.status,
        request_id=request_id,
    )
