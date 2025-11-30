"""Alert repository interface."""
from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.models.alert import Alert


class AlertRepository(ABC):
    """Alert repository interface."""

    @abstractmethod
    async def create(self, alert_data: dict) -> Alert:
        """Create a new alert."""
        pass

    @abstractmethod
    async def find_by_id(self, alert_id: str) -> Optional[Alert]:
        """Find alert by ID."""
        pass

    @abstractmethod
    async def update(self, alert_id: str, updates: dict) -> Optional[Alert]:
        """Update alert."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        asset_id: Optional[str] = None
    ) -> List[Alert]:
        """List alerts with filtering."""
        pass
