"""Geofence repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from app.domain.models.geofence import Geofence
from app.domain.models.geofence_alert_event import GeofenceAlertEvent


class GeofenceRepository(ABC):
    """Geofence repository interface."""

    @abstractmethod
    async def create(self, payload: dict) -> Geofence:
        """Create a new geofence."""
        pass

    @abstractmethod
    async def find_by_id(self, geofence_id: str) -> Optional[Geofence]:
        """Find geofence by id."""
        pass

    @abstractmethod
    async def update(self, geofence_id: str, updates: dict) -> Optional[Geofence]:
        """Update geofence by id."""
        pass

    @abstractmethod
    async def delete(self, geofence_id: str) -> bool:
        """Delete geofence by id."""
        pass

    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> List[Geofence]:
        """List geofences."""
        pass

    @abstractmethod
    async def list_active(self) -> List[Geofence]:
        """List active geofences."""
        pass

    @abstractmethod
    async def find_matching_hazard(
        self,
        hazard_geometry: Optional[dict],
        district: Optional[str] = None,
        ward: Optional[str] = None,
    ) -> List[Geofence]:
        """Find geofences matching hazard location context."""
        pass

    @abstractmethod
    async def has_recent_alert(
        self,
        geofence_id: str,
        hazard_layer_id: str,
        since: datetime,
    ) -> bool:
        """Check if alert was already triggered recently."""
        pass

    @abstractmethod
    async def create_alert_event(self, payload: dict) -> GeofenceAlertEvent:
        """Create geofence alert event audit row."""
        pass
