"""Situation report repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.sitrep import Sitrep, SitrepDelta


class SitrepRepository(ABC):
    """SITREP repository interface."""

    @abstractmethod
    async def create(self, payload: dict) -> Sitrep:
        """Create a new situation report."""
        pass

    @abstractmethod
    async def find_by_id(self, sitrep_id: str) -> Optional[Sitrep]:
        """Find sitrep by id."""
        pass

    @abstractmethod
    async def update(self, sitrep_id: str, updates: dict) -> Optional[Sitrep]:
        """Update sitrep by id."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Sitrep]:
        """List sitreps with filtering."""
        pass

    @abstractmethod
    async def append_delta(self, sitrep_id: str, delta: SitrepDelta) -> Optional[Sitrep]:
        """Append timeline delta and return updated sitrep."""
        pass
