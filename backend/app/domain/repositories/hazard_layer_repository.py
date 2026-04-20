"""Hazard layer repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from app.domain.models.hazard_layer import HazardLayer


class HazardLayerRepository(ABC):
    """Hazard layer repository interface."""

    @abstractmethod
    async def create(self, payload: dict) -> HazardLayer:
        """Create a hazard layer record."""
        pass

    @abstractmethod
    async def find_by_id(self, hazard_db_id: str) -> Optional[HazardLayer]:
        """Find hazard by database id."""
        pass

    @abstractmethod
    async def find_by_source_hazard_id(
        self,
        source: str,
        hazard_id: str,
    ) -> Optional[HazardLayer]:
        """Find hazard by source + source hazard id."""
        pass

    @abstractmethod
    async def update(self, hazard_db_id: str, updates: dict) -> Optional[HazardLayer]:
        """Update hazard by database id."""
        pass

    @abstractmethod
    async def bulk_upsert(self, payloads: List[dict]) -> Dict[str, int]:
        """Bulk upsert hazards by source + hazard_id."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        source: Optional[str] = None,
        district: Optional[str] = None,
        ward: Optional[str] = None,
    ) -> List[HazardLayer]:
        """List hazards with optional filtering."""
        pass

    @abstractmethod
    async def list_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int,
        limit: int = 100,
    ) -> List[HazardLayer]:
        """List hazards near a coordinate."""
        pass

    @abstractmethod
    async def list_in_polygon(self, polygon: dict, limit: int = 500) -> List[HazardLayer]:
        """List hazards inside a polygon geometry."""
        pass

    @abstractmethod
    async def list_recent(
        self,
        window_start: datetime,
        limit: int = 50,
        active_only: bool = True,
    ) -> List[HazardLayer]:
        """List recent hazards detected after ``window_start``."""
        pass

    @abstractmethod
    async def deactivate_expired(self, cutoff: Optional[datetime] = None) -> int:
        """Deactivate expired hazards and return updated count."""
        pass
