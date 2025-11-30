"""Maintenance repository interface."""
from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.models.maintenance import Maintenance


class MaintenanceRepository(ABC):
    """Maintenance repository interface."""

    @abstractmethod
    async def create(self, maintenance_data: dict) -> Maintenance:
        """Create a new maintenance record."""
        pass

    @abstractmethod
    async def find_by_id(self, maintenance_id: str) -> Optional[Maintenance]:
        """Find maintenance by ID."""
        pass

    @abstractmethod
    async def find_by_work_order_number(self, work_order_number: str) -> Optional[Maintenance]:
        """Find maintenance by work order number."""
        pass

    @abstractmethod
    async def update(self, maintenance_id: str, updates: dict) -> Optional[Maintenance]:
        """Update maintenance record."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        asset_id: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Maintenance]:
        """List maintenance records with filtering."""
        pass

    @abstractmethod
    async def find_upcoming(self, days: int = 7) -> List[Maintenance]:
        """Find upcoming maintenance records."""
        pass
