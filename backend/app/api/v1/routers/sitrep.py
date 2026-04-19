"""Emergency SITREP API router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.v1.dependencies import get_sitrep_service
from app.api.v1.middleware import get_current_user
from app.domain.models.sitrep import Sitrep, SitrepCreate, SitrepDelta, SitrepUpdate
from app.domain.models.user import User, UserRole
from app.domain.services.sitrep_service import SitrepService
from app.middleware.request_id import get_or_create_request_id, merge_request_id_metadata

router = APIRouter()


def _ensure_operator(user: User):
    """Allow only operators to manage sitrep workflows."""
    if user.role not in {UserRole.ADMIN, UserRole.TECHNICIAN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for SITREP operations",
        )


@router.get("", response_model=List[Sitrep])
async def list_sitreps(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    emergency_event_id: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    service: SitrepService = Depends(get_sitrep_service),
):
    """List sitreps."""
    _ensure_operator(current_user)
    return await service.list_sitreps(
        skip=skip,
        limit=limit,
        emergency_event_id=emergency_event_id,
        status=status_filter,
    )


@router.get("/{sitrep_id}", response_model=Sitrep)
async def get_sitrep(
    sitrep_id: str,
    current_user: User = Depends(get_current_user),
    service: SitrepService = Depends(get_sitrep_service),
):
    """Get one sitrep."""
    _ensure_operator(current_user)
    return await service.get_sitrep_by_id(sitrep_id)


@router.post("", response_model=Sitrep, status_code=status.HTTP_201_CREATED)
async def create_sitrep(
    request: Request,
    payload: SitrepCreate,
    current_user: User = Depends(get_current_user),
    service: SitrepService = Depends(get_sitrep_service),
):
    """Create a sitrep draft."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    payload = payload.model_copy(
        update={"metadata": merge_request_id_metadata(payload.metadata, request_id)}
    )
    return await service.create_sitrep(
        payload,
        created_by=str(current_user.id),
        request_id=request_id,
    )


@router.put("/{sitrep_id}", response_model=Sitrep)
async def update_sitrep(
    request: Request,
    sitrep_id: str,
    payload: SitrepUpdate,
    current_user: User = Depends(get_current_user),
    service: SitrepService = Depends(get_sitrep_service),
):
    """Update sitrep snapshot and metadata."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    payload = payload.model_copy(
        update={"metadata": merge_request_id_metadata(payload.metadata, request_id)}
    )
    return await service.update_sitrep(
        sitrep_id,
        payload,
        request_id=request_id,
    )


@router.post("/{sitrep_id}/delta", response_model=Sitrep)
async def append_sitrep_delta(
    sitrep_id: str,
    payload: SitrepDelta,
    current_user: User = Depends(get_current_user),
    service: SitrepService = Depends(get_sitrep_service),
):
    """Append one timeline delta in sitrep."""
    _ensure_operator(current_user)
    return await service.append_delta(sitrep_id, payload)


@router.post("/{sitrep_id}/publish", response_model=Sitrep)
async def publish_sitrep(
    request: Request,
    sitrep_id: str,
    current_user: User = Depends(get_current_user),
    service: SitrepService = Depends(get_sitrep_service),
):
    """Publish sitrep for command center sharing."""
    _ensure_operator(current_user)
    request_id = get_or_create_request_id(request)
    return await service.publish_sitrep(
        sitrep_id,
        published_by=str(current_user.id),
        request_id=request_id,
    )
