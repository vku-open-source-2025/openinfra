"""Sensor data repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from app.domain.models.iot_sensor import SensorReading


class SensorDataRepository(ABC):
    """Sensor data repository interface."""

    @abstractmethod
    async def create(self, reading_data: dict) -> SensorReading:
        """Create a new sensor reading."""
        pass

    @abstractmethod
    async def get_readings(
        self,
        sensor_id: str,
        from_time: datetime,
        to_time: datetime,
        limit: int = 1000
    ) -> List[SensorReading]:
        """Get sensor readings in time range."""
        pass

    @abstractmethod
    async def aggregate_readings(
        self,
        sensor_id: str,
        from_time: datetime,
        to_time: datetime,
        granularity: str = "hour"  # "minute" | "hour" | "day"
    ) -> List[dict]:
        """Aggregate sensor readings."""
        pass
