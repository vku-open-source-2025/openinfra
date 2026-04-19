"""Resource unit repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.resource_unit import ResourceUnit


class ResourceUnitRepository(ABC):
    """Resource unit repository interface."""

    @abstractmethod
    async def create(self, payload: dict) -> ResourceUnit:
        """Create a new resource unit."""
        pass

    @abstractmethod
    async def find_by_id(self, resource_id: str) -> Optional[ResourceUnit]:
        """Find resource unit by id."""
        pass

    @abstractmethod
    async def update(self, resource_id: str, updates: dict) -> Optional[ResourceUnit]:
        """Update resource unit by id."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        resource_type: Optional[str] = None,
        district: Optional[str] = None,
    ) -> List[ResourceUnit]:
        """List resource units with filtering."""
        pass
