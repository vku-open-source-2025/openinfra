"""Maintenance API router."""
from fastapi import APIRouter, Query, Depends, HTTPException, UploadFile, File, status
from typing import List, Optional
from app.domain.models.maintenance import (
    Maintenance, MaintenanceCreate, MaintenanceUpdate,
    MaintenanceStartRequest, MaintenanceCompleteRequest
)
from app.domain.services.maintenance_service import MaintenanceService
from app.api.v1.dependencies import get_maintenance_service
from app.api.v1.middleware import get_current_user
from app.domain.models.user import User
from app.infrastructure.storage.storage_service import StorageService
from app.api.v1.dependencies import get_storage_service

router = APIRouter()


@router.get("", response_model=List[Maintenance])
async def list_maintenance(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    asset_id: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    priority: Optional[str] = None,
    maintenance_service: MaintenanceService = Depends(get_maintenance_service)
):
    """List maintenance records with filtering."""
    return await maintenance_service.list_maintenance(
        skip, limit, asset_id, status, assigned_to, priority
    )


@router.get("/upcoming", response_model=List[Maintenance])
async def get_upcoming_maintenance(
    days: int = Query(7, ge=1, le=30),
    maintenance_service: MaintenanceService = Depends(get_maintenance_service)
):
    """Get upcoming maintenance records."""
    return await maintenance_service.get_upcoming_maintenance(days)


@router.post("", response_model=Maintenance, status_code=status.HTTP_201_CREATED)
async def create_maintenance(
    maintenance_data: MaintenanceCreate,
    current_user: User = Depends(get_current_user),
    maintenance_service: MaintenanceService = Depends(get_maintenance_service)
):
    """Create a new maintenance work order."""
    return await maintenance_service.create_maintenance(
        maintenance_data,
        str(current_user.id)
    )


@router.get("/{maintenance_id}", response_model=Maintenance)
async def get_maintenance(
    maintenance_id: str,
    maintenance_service: MaintenanceService = Depends(get_maintenance_service)
):
    """Get maintenance details."""
    return await maintenance_service.get_maintenance_by_id(maintenance_id)


@router.put("/{maintenance_id}", response_model=Maintenance)
async def update_maintenance(
    maintenance_id: str,
    updates: MaintenanceUpdate,
    maintenance_service: MaintenanceService = Depends(get_maintenance_service)
):
    """Update maintenance record."""
    return await maintenance_service.update_maintenance(maintenance_id, updates)


@router.post("/{maintenance_id}/assign", response_model=Maintenance)
async def assign_maintenance(
    maintenance_id: str,
    assigned_to: str = Query(..., description="User ID to assign to"),
    current_user: User = Depends(get_current_user),
    maintenance_service: MaintenanceService = Depends(get_maintenance_service)
):
    """Assign maintenance to a technician."""
    return await maintenance_service.assign_maintenance(
        maintenance_id,
        assigned_to,
        str(current_user.id)
    )


@router.post("/{maintenance_id}/start", response_model=Maintenance)
async def start_maintenance(
    maintenance_id: str,
    start_request: MaintenanceStartRequest,
    current_user: User = Depends(get_current_user),
    maintenance_service: MaintenanceService = Depends(get_maintenance_service)
):
    """Start maintenance work."""
    return await maintenance_service.start_maintenance(
        maintenance_id,
        start_request,
        str(current_user.id)
    )


@router.post("/{maintenance_id}/complete", response_model=Maintenance)
async def complete_maintenance(
    maintenance_id: str,
    complete_request: MaintenanceCompleteRequest,
    current_user: User = Depends(get_current_user),
    maintenance_service: MaintenanceService = Depends(get_maintenance_service)
):
    """Complete maintenance work."""
    return await maintenance_service.complete_maintenance(
        maintenance_id,
        complete_request,
        str(current_user.id)
    )


@router.post("/{maintenance_id}/cancel", response_model=Maintenance)
async def cancel_maintenance(
    maintenance_id: str,
    cancellation_reason: str = Query(..., description="Reason for cancellation"),
    current_user: User = Depends(get_current_user),
    maintenance_service: MaintenanceService = Depends(get_maintenance_service)
):
    """Cancel maintenance work order."""
    return await maintenance_service.cancel_maintenance(
        maintenance_id,
        cancellation_reason,
        str(current_user.id)
    )


@router.post("/{maintenance_id}/photos", response_model=Maintenance)
async def upload_maintenance_photos(
    maintenance_id: str,
    photo_type: str = Query("after", regex="^(before|after)$"),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    maintenance_service: MaintenanceService = Depends(get_maintenance_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Upload photos for maintenance (before or after)."""
    photo_urls = []

    for file in files:
        # Save file
        file_path = f"maintenance/{maintenance_id}/{photo_type}/{file.filename}"
        file_url = await storage_service.upload_file(file_path, await file.read())
        photo_urls.append(file_url)

    return await maintenance_service.add_photos(maintenance_id, photo_urls, photo_type)


@router.get("/asset/{asset_id}", response_model=List[Maintenance])
async def get_asset_maintenance(
    asset_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    maintenance_service: MaintenanceService = Depends(get_maintenance_service)
):
    """Get maintenance records for an asset."""
    return await maintenance_service.list_maintenance(
        skip, limit, asset_id=asset_id, status=None, assigned_to=None, priority=None
    )
