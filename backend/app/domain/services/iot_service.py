"""IoT service for sensor management and data ingestion."""
from typing import Optional, List
from datetime import datetime
from app.domain.models.iot_sensor import IoTSensor, IoTSensorCreate, IoTSensorUpdate, SensorReading
from app.domain.models.alert import Alert, AlertSeverity, AlertStatus, AlertSourceType
from app.domain.repositories.iot_repository import IoTSensorRepository
from app.domain.repositories.sensor_data_repository import SensorDataRepository
from app.domain.services.alert_service import AlertService
from app.core.exceptions import ConflictError, NotFoundError
import logging
import uuid

logger = logging.getLogger(__name__)


class IoTService:
    """IoT service for sensor management."""

    def __init__(
        self,
        sensor_repository: IoTSensorRepository,
        data_repository: SensorDataRepository,
        alert_service: Optional[AlertService] = None
    ):
        self.sensor_repository = sensor_repository
        self.data_repository = data_repository
        self.alert_service = alert_service

    async def register_sensor(
        self,
        sensor_data: IoTSensorCreate,
        created_by: Optional[str] = None
    ) -> IoTSensor:
        """Register a new IoT sensor."""
        # Check if sensor_code exists
        existing = await self.sensor_repository.find_by_code(sensor_data.sensor_code)
        if existing:
            raise ConflictError(f"Sensor code '{sensor_data.sensor_code}' already exists")

        sensor_dict = sensor_data.dict(exclude_unset=True)
        sensor_dict["created_by"] = created_by
        sensor_dict["status"] = "offline"

        sensor = await self.sensor_repository.create(sensor_dict)
        logger.info(f"Registered sensor: {sensor.sensor_code}")
        return sensor

    async def ingest_sensor_reading(
        self,
        sensor_id: str,
        value: float,
        timestamp: Optional[datetime] = None,
        metadata: Optional[dict] = None
    ) -> SensorReading:
        """Ingest a sensor reading and check thresholds."""
        sensor = await self.sensor_repository.find_by_id(sensor_id)
        if not sensor:
            raise NotFoundError("Sensor", sensor_id)

        if timestamp is None:
            timestamp = datetime.utcnow()

        # Check thresholds and generate alert if needed
        alert = None
        if sensor.thresholds:
            alert = self._check_thresholds(sensor, value)
            if alert and self.alert_service:
                await self.alert_service.create_alert(alert)

        # Determine reading status
        status = "normal"
        threshold_exceeded = False
        if alert:
            if alert.severity == AlertSeverity.CRITICAL or alert.severity == AlertSeverity.EMERGENCY:
                status = "critical"
            else:
                status = "warning"
            threshold_exceeded = True

        # Create reading
        reading_dict = {
            "sensor_id": sensor_id,
            "asset_id": sensor.asset_id,
            "timestamp": timestamp,
            "value": value,
            "unit": sensor.measurement_unit,
            "status": status,
            "threshold_exceeded": threshold_exceeded,
            "metadata": metadata or {}
        }

        reading = await self.data_repository.create(reading_dict)

        # Update sensor last_seen and last_reading
        await self.sensor_repository.update_last_seen(sensor_id, timestamp)
        await self.sensor_repository.update(
            sensor_id,
            {
                "last_reading": {
                    "value": value,
                    "timestamp": timestamp.isoformat(),
                    "status": status
                }
            }
        )

        return reading

    def _check_thresholds(
        self,
        sensor: IoTSensor,
        value: float
    ) -> Optional[Alert]:
        """Check if value exceeds thresholds and create alert if needed."""
        if not sensor.thresholds:
            return None

        thresholds = sensor.thresholds

        # Check critical thresholds
        if thresholds.critical_max is not None and value >= thresholds.critical_max:
            return Alert(
                alert_code=f"ALERT-{uuid.uuid4().hex[:8].upper()}",
                source_type=AlertSourceType.SENSOR,
                sensor_id=str(sensor.id),
                asset_id=sensor.asset_id,
                type="threshold_exceeded",
                severity=AlertSeverity.CRITICAL,
                title=f"Critical threshold exceeded for {sensor.sensor_code}",
                message=f"Value {value} {sensor.measurement_unit} exceeds critical maximum {thresholds.critical_max}",
                trigger_value=value,
                threshold_value=thresholds.critical_max,
                condition="greater_than"
            )

        if thresholds.critical_min is not None and value <= thresholds.critical_min:
            return Alert(
                alert_code=f"ALERT-{uuid.uuid4().hex[:8].upper()}",
                source_type=AlertSourceType.SENSOR,
                sensor_id=str(sensor.id),
                asset_id=sensor.asset_id,
                type="threshold_exceeded",
                severity=AlertSeverity.CRITICAL,
                title=f"Critical threshold exceeded for {sensor.sensor_code}",
                message=f"Value {value} {sensor.measurement_unit} below critical minimum {thresholds.critical_min}",
                trigger_value=value,
                threshold_value=thresholds.critical_min,
                condition="less_than"
            )

        # Check warning thresholds
        if thresholds.warning_max is not None and value >= thresholds.warning_max:
            return Alert(
                alert_code=f"ALERT-{uuid.uuid4().hex[:8].upper()}",
                source_type=AlertSourceType.SENSOR,
                sensor_id=str(sensor.id),
                asset_id=sensor.asset_id,
                type="threshold_exceeded",
                severity=AlertSeverity.WARNING,
                title=f"Warning threshold exceeded for {sensor.sensor_code}",
                message=f"Value {value} {sensor.measurement_unit} exceeds warning maximum {thresholds.warning_max}",
                trigger_value=value,
                threshold_value=thresholds.warning_max,
                condition="greater_than"
            )

        if thresholds.warning_min is not None and value <= thresholds.warning_min:
            return Alert(
                alert_code=f"ALERT-{uuid.uuid4().hex[:8].upper()}",
                source_type=AlertSourceType.SENSOR,
                sensor_id=str(sensor.id),
                asset_id=sensor.asset_id,
                type="threshold_exceeded",
                severity=AlertSeverity.WARNING,
                title=f"Warning threshold exceeded for {sensor.sensor_code}",
                message=f"Value {value} {sensor.measurement_unit} below warning minimum {thresholds.warning_min}",
                trigger_value=value,
                threshold_value=thresholds.warning_min,
                condition="less_than"
            )

        return None

    async def get_sensor_by_id(self, sensor_id: str) -> IoTSensor:
        """Get sensor by ID."""
        sensor = await self.sensor_repository.find_by_id(sensor_id)
        if not sensor:
            raise NotFoundError("Sensor", sensor_id)
        return sensor

    async def update_sensor(
        self,
        sensor_id: str,
        updates: IoTSensorUpdate
    ) -> IoTSensor:
        """Update sensor configuration."""
        update_dict = updates.dict(exclude_unset=True)
        updated_sensor = await self.sensor_repository.update(sensor_id, update_dict)
        if not updated_sensor:
            raise NotFoundError("Sensor", sensor_id)
        return updated_sensor

    async def list_sensors(
        self,
        skip: int = 0,
        limit: int = 100,
        asset_id: Optional[str] = None,
        sensor_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[IoTSensor]:
        """List sensors with filtering."""
        return await self.sensor_repository.list(skip, limit, asset_id, sensor_type, status)

    async def get_sensor_readings(
        self,
        sensor_id: str,
        from_time: datetime,
        to_time: datetime,
        limit: int = 1000
    ) -> List[SensorReading]:
        """Get sensor readings in time range."""
        return await self.data_repository.get_readings(sensor_id, from_time, to_time, limit)

    async def get_sensor_statistics(
        self,
        sensor_id: str,
        from_time: datetime,
        to_time: datetime,
        granularity: str = "hour"
    ) -> dict:
        """Get aggregated sensor statistics."""
        aggregated = await self.data_repository.aggregate_readings(
            sensor_id, from_time, to_time, granularity
        )

        if not aggregated:
            return {
                "sensor_id": sensor_id,
                "from_time": from_time.isoformat(),
                "to_time": to_time.isoformat(),
                "granularity": granularity,
                "data": [],
                "statistics": {}
            }

        # Calculate overall statistics
        all_values = [d["avg"] for d in aggregated]
        return {
            "sensor_id": sensor_id,
            "from_time": from_time.isoformat(),
            "to_time": to_time.isoformat(),
            "granularity": granularity,
            "data": aggregated,
            "statistics": {
                "min": min(all_values),
                "max": max(all_values),
                "avg": sum(all_values) / len(all_values),
                "count": len(aggregated)
            }
        }

    async def batch_ingest_readings(
        self,
        readings: List[dict]
    ) -> dict:
        """Batch ingest multiple sensor readings."""
        processed = 0
        alerts_triggered = 0

        for reading_data in readings:
            try:
                sensor_id = reading_data.get("sensor_id")
                value = reading_data.get("value")
                timestamp = reading_data.get("timestamp")
                metadata = reading_data.get("metadata")

                if timestamp:
                    if isinstance(timestamp, str):
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

                reading = await self.ingest_sensor_reading(
                    sensor_id,
                    value,
                    timestamp,
                    metadata
                )
                processed += 1

                # Check if alert was triggered (simplified check)
                if reading.threshold_exceeded:
                    alerts_triggered += 1
            except Exception as e:
                logger.error(f"Error processing reading: {e}")
                continue

        return {
            "processed": processed,
            "alerts_triggered": alerts_triggered,
            "total": len(readings)
        }
