"""Dispatch order repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.dispatch_order import DispatchOrder


class DispatchOrderRepository(ABC):
    """Dispatch order repository interface."""

    @abstractmethod
    async def create(self, payload: dict) -> DispatchOrder:
        """Create a new dispatch order."""
        pass

    @abstractmethod
    async def find_by_id(self, order_id: str) -> Optional[DispatchOrder]:
        """Find dispatch order by id."""
        pass

    @abstractmethod
    async def update(self, order_id: str, updates: dict) -> Optional[DispatchOrder]:
        """Update dispatch order by id."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List[DispatchOrder]:
        """List dispatch orders with filtering."""
        pass
