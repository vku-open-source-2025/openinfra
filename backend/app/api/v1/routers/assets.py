"""Assets API router."""
from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File
from typing import List, Optional
from app.domain.models.asset import Asset, AssetCreate, AssetUpdate
from app.domain.services.asset_service import AssetService
from app.domain.services.audit_service import AuditService
from app.infrastructure.storage.storage_service import StorageService
from app.infrastructure.storage.local_storage import LocalStorageService
from app.api.v1.dependencies import get_asset_service, get_audit_service, get_storage_service
from app.api.v1.middleware import get_current_user
from app.domain.models.user import User

router = APIRouter()


@router.post("/", response_model=Asset)
async def create_asset(
    asset: AssetCreate,
    current_user: User = Depends(get_current_user),
    asset_service: AssetService = Depends(get_asset_service)
):
    """Create a new infrastructure asset."""
    return await asset_service.create_asset(asset, created_by=str(current_user.id))


@router.get("/", response_model=List[Asset])
async def list_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    feature_type: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    asset_service: AssetService = Depends(get_asset_service)
):
    """List all assets with pagination and filtering."""
    return await asset_service.list_assets(skip, limit, feature_type, status, category)


@router.get("/{id}", response_model=Asset)
async def get_asset(
    id: str,
    asset_service: AssetService = Depends(get_asset_service)
):
    """Get asset by ID."""
    return await asset_service.get_asset_by_id(id)


@router.put("/{id}", response_model=Asset)
async def update_asset(
    id: str,
    asset_update: AssetUpdate,
    current_user: User = Depends(get_current_user),
    asset_service: AssetService = Depends(get_asset_service)
):
    """Update asset."""
    return await asset_service.update_asset(id, asset_update, updated_by=str(current_user.id))


@router.delete("/{id}")
async def delete_asset(
    id: str,
    current_user: User = Depends(get_current_user),
    asset_service: AssetService = Depends(get_asset_service)
):
    """Delete asset (soft delete)."""
    await asset_service.delete_asset(id, deleted_by=str(current_user.id))
    return {"message": "Asset deleted successfully"}


@router.get("/{id}/history")
async def get_asset_history(
    id: str,
    limit: int = Query(100, ge=1, le=500),
    asset_service: AssetService = Depends(get_asset_service)
):
    """Get asset change history."""
    history = await asset_service.get_asset_history(id, limit)
    return {"data": history, "count": len(history)}


@router.post("/{id}/photos", response_model=Asset)
async def upload_asset_photo(
    id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    asset_service: AssetService = Depends(get_asset_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Upload photo for asset."""
    # Upload file
    file_url = await storage_service.upload_file(
        file,
        bucket="assets",
        prefix=f"{id}/photos/"
    )

    # Add attachment to asset
    return await asset_service.add_attachment(
        id,
        file_url,
        file.filename or "photo",
        file.content_type or "image/jpeg",
        str(current_user.id)
    )


@router.post("/{id}/attachments", response_model=Asset)
async def upload_asset_attachment(
    id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    asset_service: AssetService = Depends(get_asset_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Upload document attachment for asset."""
    # Upload file
    file_url = await storage_service.upload_file(
        file,
        bucket="assets",
        prefix=f"{id}/attachments/"
    )

    # Add attachment to asset
    return await asset_service.add_attachment(
        id,
        file_url,
        file.filename or "attachment",
        file.content_type or "application/octet-stream",
        str(current_user.id)
    )


@router.delete("/{id}/attachments/{attachment_url:path}")
async def delete_asset_attachment(
    id: str,
    attachment_url: str,
    current_user: User = Depends(get_current_user),
    asset_service: AssetService = Depends(get_asset_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Delete attachment from asset."""
    # Remove from asset
    await asset_service.remove_attachment(id, attachment_url, str(current_user.id))

    # Delete file from storage
    await storage_service.delete_file(attachment_url)

    return {"message": "Attachment deleted successfully"}
