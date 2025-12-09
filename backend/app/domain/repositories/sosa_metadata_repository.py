"""SOSA Metadata repository interface."""
from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.models.sosa_metadata import SensorMetadata


class SensorMetadataRepository(ABC):
    """Repository interface for SOSA Sensor Metadata."""

    @abstractmethod
    async def create(self, metadata: dict) -> SensorMetadata:
        """Create sensor metadata entry."""
        pass

    @abstractmethod
    async def find_by_sensor_id(self, sensor_id: str) -> Optional[SensorMetadata]:
        """Find metadata by sensor ID (same as _id)."""
        pass

    @abstractmethod
    async def find_by_feature_of_interest(self, feature_id: str) -> List[SensorMetadata]:
        """Find all sensors observing a specific feature (asset)."""
        pass

    @abstractmethod
    async def find_by_observable_property(self, property_uri: str) -> List[SensorMetadata]:
        """Find all sensors measuring a specific property."""
        pass

    @abstractmethod
    async def find_by_platform(self, platform_id: str) -> List[SensorMetadata]:
        """Find all sensors on a platform."""
        pass

    @abstractmethod
    async def update(self, sensor_id: str, updates: dict) -> Optional[SensorMetadata]:
        """Update sensor metadata."""
        pass

    @abstractmethod
    async def delete(self, sensor_id: str) -> bool:
        """Delete sensor metadata."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        observes: Optional[str] = None,
        feature_id: Optional[str] = None
    ) -> List[SensorMetadata]:
        """List sensor metadata with filtering."""
        pass

    @abstractmethod
    async def exists(self, sensor_id: str) -> bool:
        """Check if metadata exists for sensor."""
        pass

    @abstractmethod
    async def bulk_create(self, metadata_list: List[dict]) -> int:
        """Bulk create metadata entries. Returns count of created entries."""
        pass
