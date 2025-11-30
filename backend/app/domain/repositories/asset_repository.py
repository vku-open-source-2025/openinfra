"""Asset repository interface."""
from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.models.asset import Asset


class AssetRepository(ABC):
    """Asset repository interface."""

    @abstractmethod
    async def create(self, asset_data: dict) -> Asset:
        """Create a new asset."""
        pass

    @abstractmethod
    async def find_by_id(self, asset_id: str) -> Optional[Asset]:
        """Find asset by ID."""
        pass

    @abstractmethod
    async def find_by_code(self, asset_code: str) -> Optional[Asset]:
        """Find asset by code."""
        pass

    @abstractmethod
    async def update(self, asset_id: str, updates: dict) -> Optional[Asset]:
        """Update asset."""
        pass

    @abstractmethod
    async def delete(self, asset_id: str) -> bool:
        """Delete asset (soft delete)."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None
    ) -> List[Asset]:
        """List assets with pagination and filtering."""
        pass

    @abstractmethod
    async def add_attachment(
        self,
        asset_id: str,
        attachment: dict
    ) -> bool:
        """Add attachment to asset."""
        pass

    @abstractmethod
    async def remove_attachment(
        self,
        asset_id: str,
        attachment_url: str
    ) -> bool:
        """Remove attachment from asset."""
        pass
