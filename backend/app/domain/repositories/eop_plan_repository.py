"""EOP plan repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.eop_plan import EOPPlan


class EOPPlanRepository(ABC):
    """EOP plan repository interface."""

    @abstractmethod
    async def create(self, payload: dict) -> EOPPlan:
        """Create a new EOP plan."""
        pass

    @abstractmethod
    async def find_by_id(self, plan_id: str) -> Optional[EOPPlan]:
        """Find EOP plan by id."""
        pass

    @abstractmethod
    async def update(self, plan_id: str, updates: dict) -> Optional[EOPPlan]:
        """Update EOP plan by id."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[EOPPlan]:
        """List EOP plans with filtering."""
        pass
