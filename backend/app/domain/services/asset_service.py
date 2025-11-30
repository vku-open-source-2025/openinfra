"""Asset domain service."""
from typing import Optional, List
from datetime import datetime
from app.domain.models.asset import Asset, AssetCreate, AssetUpdate
from app.domain.repositories.asset_repository import AssetRepository
from app.domain.services.audit_service import AuditService
from app.core.exceptions import ConflictError, NotFoundError
import logging

logger = logging.getLogger(__name__)


class AssetService:
    """Asset service for business logic."""

    def __init__(
        self,
        asset_repository: AssetRepository,
        audit_service: Optional[AuditService] = None
    ):
        self.repository = asset_repository
        self.audit_service = audit_service

    async def create_asset(
        self,
        asset_data: AssetCreate,
        created_by: Optional[str] = None
    ) -> Asset:
        """Create a new asset."""
        # Check if asset_code exists
        existing = await self.repository.find_by_code(asset_data.asset_code)
        if existing:
            raise ConflictError(f"Asset code '{asset_data.asset_code}' already exists")

        # Convert to dict
        asset_dict = asset_data.dict(exclude_unset=True)
        asset_dict["created_by"] = created_by

        # Create asset
        asset = await self.repository.create(asset_dict)

        # Log creation
        if self.audit_service:
            await self.audit_service.log_change(
                resource_type="asset",
                resource_id=str(asset.id),
                action="create",
                user_id=created_by,
                description=f"Created asset {asset.asset_code}"
            )

        logger.info(f"Created asset: {asset.asset_code}")
        return asset

    async def get_asset_by_id(self, asset_id: str) -> Asset:
        """Get asset by ID."""
        asset = await self.repository.find_by_id(asset_id)
        if not asset:
            raise NotFoundError("Asset", asset_id)
        return asset

    async def update_asset(
        self,
        asset_id: str,
        updates: AssetUpdate,
        updated_by: Optional[str] = None
    ) -> Asset:
        """Update asset with audit trail."""
        # Get current asset state
        current_asset = await self.get_asset_by_id(asset_id)

        # Prepare updates
        update_dict = updates.dict(exclude_unset=True)
        update_dict["updated_by"] = updated_by

        # Update asset
        updated_asset = await self.repository.update(asset_id, update_dict)
        if not updated_asset:
            raise NotFoundError("Asset", asset_id)

        # Log changes
        if self.audit_service:
            changes = {
                "before": current_asset.dict(exclude={"id", "created_at", "updated_at"}),
                "after": updated_asset.dict(exclude={"id", "created_at", "updated_at"})
            }
            await self.audit_service.log_change(
                resource_type="asset",
                resource_id=asset_id,
                action="update",
                user_id=updated_by,
                changes=changes,
                description=f"Updated asset {updated_asset.asset_code}"
            )

        return updated_asset

    async def delete_asset(
        self,
        asset_id: str,
        deleted_by: Optional[str] = None
    ) -> bool:
        """Delete asset (soft delete)."""
        asset = await self.get_asset_by_id(asset_id)
        result = await self.repository.delete(asset_id)

        if result and self.audit_service:
            await self.audit_service.log_change(
                resource_type="asset",
                resource_id=asset_id,
                action="delete",
                user_id=deleted_by,
                description=f"Deleted asset {asset.asset_code}"
            )

        return result

    async def list_assets(
        self,
        skip: int = 0,
        limit: int = 100,
        feature_type: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Asset]:
        """List assets with filtering."""
        filters = {}
        if feature_type:
            filters["feature_type"] = feature_type
        if status:
            filters["status"] = status
        if category:
            filters["category"] = category

        return await self.repository.list(skip, limit, filters)

    async def add_attachment(
        self,
        asset_id: str,
        file_url: str,
        file_name: str,
        file_type: str,
        uploaded_by: str
    ) -> Asset:
        """Add attachment to asset."""
        asset = await self.get_asset_by_id(asset_id)

        attachment = {
            "file_name": file_name,
            "file_url": file_url,
            "file_type": file_type,
            "uploaded_at": datetime.utcnow(),
            "uploaded_by": uploaded_by
        }

        await self.repository.add_attachment(asset_id, attachment)

        # Log change
        if self.audit_service:
            await self.audit_service.log_change(
                resource_type="asset",
                resource_id=asset_id,
                action="update",
                user_id=uploaded_by,
                description=f"Added attachment {file_name} to asset {asset.asset_code}"
            )

        return await self.get_asset_by_id(asset_id)

    async def remove_attachment(
        self,
        asset_id: str,
        attachment_url: str,
        removed_by: str
    ) -> Asset:
        """Remove attachment from asset."""
        asset = await self.get_asset_by_id(asset_id)
        await self.repository.remove_attachment(asset_id, attachment_url)

        # Log change
        if self.audit_service:
            await self.audit_service.log_change(
                resource_type="asset",
                resource_id=asset_id,
                action="update",
                user_id=removed_by,
                description=f"Removed attachment from asset {asset.asset_code}"
            )

        return await self.get_asset_by_id(asset_id)

    async def get_asset_history(
        self,
        asset_id: str,
        limit: int = 100
    ) -> List:
        """Get asset change history."""
        if not self.audit_service:
            return []
        return await self.audit_service.get_resource_history("asset", asset_id, limit)
