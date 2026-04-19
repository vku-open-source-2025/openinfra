"""Geofences API router."""

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.v1.dependencies import get_geofence_service, get_hazard_layer_service
from app.api.v1.middleware import get_current_user
from app.domain.models.geofence import Geofence, GeofenceCreate, GeofenceUpdate
from app.domain.models.user import User, UserRole
from app.domain.services.geofence_service import GeofenceService
from app.domain.services.hazard_layer_service import HazardLayerService

router = APIRouter()


class GeofenceDryRunRequest(BaseModel):
    """Payload for geofence test execution."""

    hazard_layer_id: str


def _ensure_operator(user: User):
    """Allow only operators for geofence operations."""
    if user.role not in {UserRole.ADMIN, UserRole.TECHNICIAN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for geofence operations",
        )


@router.get("", response_model=List[Geofence])
async def list_geofences(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    service: GeofenceService = Depends(get_geofence_service),
):
    """List geofences."""
    _ensure_operator(current_user)
    return await service.list_geofences(skip=skip, limit=limit)


@router.get("/{geofence_id}", response_model=Geofence)
async def get_geofence(
    geofence_id: str,
    current_user: User = Depends(get_current_user),
    service: GeofenceService = Depends(get_geofence_service),
):
    """Get one geofence."""
    _ensure_operator(current_user)
    return await service.get_geofence_by_id(geofence_id)


@router.post("", response_model=Geofence, status_code=status.HTTP_201_CREATED)
async def create_geofence(
    payload: GeofenceCreate,
    current_user: User = Depends(get_current_user),
    service: GeofenceService = Depends(get_geofence_service),
):
    """Create geofence."""
    _ensure_operator(current_user)
    return await service.create_geofence(payload, created_by=str(current_user.id))


@router.put("/{geofence_id}", response_model=Geofence)
async def update_geofence(
    geofence_id: str,
    payload: GeofenceUpdate,
    current_user: User = Depends(get_current_user),
    service: GeofenceService = Depends(get_geofence_service),
):
    """Update geofence."""
    _ensure_operator(current_user)
    return await service.update_geofence(geofence_id, payload)


@router.delete("/{geofence_id}")
async def delete_geofence(
    geofence_id: str,
    current_user: User = Depends(get_current_user),
    service: GeofenceService = Depends(get_geofence_service),
):
    """Delete geofence."""
    _ensure_operator(current_user)
    deleted = await service.delete_geofence(geofence_id)
    return {"deleted": deleted}


@router.post("/{geofence_id}/test", response_model=Dict[str, int])
async def test_geofence(
    geofence_id: str,
    payload: GeofenceDryRunRequest,
    current_user: User = Depends(get_current_user),
    geofence_service: GeofenceService = Depends(get_geofence_service),
    hazard_service: HazardLayerService = Depends(get_hazard_layer_service),
):
    """Dry-run geofence trigger against one hazard record."""
    _ensure_operator(current_user)

    geofence = await geofence_service.get_geofence_by_id(geofence_id)
    if not geofence.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geofence is inactive",
        )

    hazard = await hazard_service.get_hazard_by_id(payload.hazard_layer_id)
    result = await geofence_service.check_and_trigger_hazard(hazard)
    return result
