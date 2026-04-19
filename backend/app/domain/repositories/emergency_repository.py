"""Emergency repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.emergency import EmergencyEvent


class EmergencyRepository(ABC):
    """Emergency repository interface."""

    @abstractmethod
    async def create(self, event_data: dict) -> EmergencyEvent:
        """Create a new emergency event."""
        pass

    @abstractmethod
    async def find_by_id(self, event_id: str) -> Optional[EmergencyEvent]:
        """Find event by ID."""
        pass

    @abstractmethod
    async def update(self, event_id: str, updates: dict) -> Optional[EmergencyEvent]:
        """Update event by ID."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        query_text: Optional[str] = None,
    ) -> List[EmergencyEvent]:
        """List emergency events with filtering."""
        pass
