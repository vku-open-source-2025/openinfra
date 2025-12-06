"""Incident repository interface."""
from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.models.incident import Incident


class IncidentRepository(ABC):
    """Incident repository interface."""

    @abstractmethod
    async def create(self, incident_data: dict) -> Incident:
        """Create a new incident."""
        pass

    @abstractmethod
    async def find_by_id(self, incident_id: str, populate_asset: bool = False) -> Optional[Incident]:
        """Find incident by ID."""
        pass

    @abstractmethod
    async def find_by_number(self, incident_number: str) -> Optional[Incident]:
        """Find incident by number."""
        pass

    @abstractmethod
    async def update(self, incident_id: str, updates: dict) -> Optional[Incident]:
        """Update incident."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        asset_id: Optional[str] = None,
        reported_by: Optional[str] = None,
        populate_asset: bool = False
    ) -> List[Incident]:
        """List incidents with filtering."""
        pass

    @abstractmethod
    async def add_comment(self, incident_id: str, comment: dict) -> bool:
        """Add comment to incident."""
        pass

    @abstractmethod
    async def upvote(self, incident_id: str, user_id: str) -> bool:
        """Upvote an incident."""
        pass
