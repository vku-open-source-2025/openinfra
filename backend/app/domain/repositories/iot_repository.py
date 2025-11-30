"""IoT Sensor repository interface."""
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from app.domain.models.iot_sensor import IoTSensor


class IoTSensorRepository(ABC):
    """IoT Sensor repository interface."""

    @abstractmethod
    async def create(self, sensor_data: dict) -> IoTSensor:
        """Create a new sensor."""
        pass

    @abstractmethod
    async def find_by_id(self, sensor_id: str) -> Optional[IoTSensor]:
        """Find sensor by ID."""
        pass

    @abstractmethod
    async def find_by_code(self, sensor_code: str) -> Optional[IoTSensor]:
        """Find sensor by code."""
        pass

    @abstractmethod
    async def update(self, sensor_id: str, updates: dict) -> Optional[IoTSensor]:
        """Update sensor."""
        pass

    @abstractmethod
    async def delete(self, sensor_id: str) -> bool:
        """Delete sensor."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        asset_id: Optional[str] = None,
        sensor_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[IoTSensor]:
        """List sensors with filtering."""
        pass

    @abstractmethod
    async def update_last_seen(self, sensor_id: str, timestamp: datetime) -> bool:
        """Update sensor last seen timestamp."""
        pass

    @abstractmethod
    async def find_offline_sensors(self, threshold_minutes: int = 15) -> List[IoTSensor]:
        """Find sensors that haven't reported in threshold minutes."""
        pass
