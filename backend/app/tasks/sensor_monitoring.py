"""Celery tasks for IoT sensor monitoring."""
from app.celery_app import app as celery_app
from app.infrastructure.database.mongodb import get_database
from app.domain.services.alert_service import AlertService
from app.domain.services.iot_service import IoTService
from app.domain.models.alert import Alert, AlertSeverity, AlertSourceType
from app.infrastructure.database.repositories.mongo_iot_repository import MongoIoTSensorRepository
from app.infrastructure.database.repositories.mongo_sensor_data_repository import MongoSensorDataRepository
from app.infrastructure.database.repositories.mongo_alert_repository import MongoAlertRepository
from datetime import datetime, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)


@celery_app.task(name="check_sensor_offline_status")
async def check_sensor_offline_status():
    """Check for offline sensors and create alerts."""
    try:
        db = await get_database()
        sensor_repo = MongoIoTSensorRepository(db)
        alert_repo = MongoAlertRepository(db)
        alert_service = AlertService(alert_repo)

        # Find sensors offline for more than 15 minutes
        offline_sensors = await sensor_repo.find_offline_sensors(threshold_minutes=15)

        alerts_created = 0
        for sensor in offline_sensors:
            # Check if alert already exists for this sensor
            existing_alerts = await alert_repo.list(
                skip=0,
                limit=1,
                status="active",
                asset_id=sensor.asset_id
            )

            # Check if there's already an offline alert for this sensor
            has_offline_alert = any(
                a.sensor_id == str(sensor.id) and a.type == "sensor_offline"
                for a in existing_alerts
            )

            if not has_offline_alert:
                alert = Alert(
                    alert_code=f"ALERT-{uuid.uuid4().hex[:8].upper()}",
                    source_type=AlertSourceType.SENSOR,
                    sensor_id=str(sensor.id),
                    asset_id=sensor.asset_id,
                    type="sensor_offline",
                    severity=AlertSeverity.WARNING,
                    title=f"Sensor {sensor.sensor_code} is offline",
                    message=f"Sensor {sensor.sensor_code} has not reported data for more than 15 minutes. Last seen: {sensor.last_seen.isoformat() if sensor.last_seen else 'Never'}",
                    triggered_at=datetime.utcnow()
                )
                await alert_service.create_alert(alert)
                alerts_created += 1

        logger.info(f"Checked {len(offline_sensors)} offline sensors, created {alerts_created} alerts")
        return {"checked": len(offline_sensors), "alerts_created": alerts_created}
    except Exception as e:
        logger.error(f"Error checking sensor offline status: {e}")
        raise


@celery_app.task(name="aggregate_sensor_data_hourly")
async def aggregate_sensor_data_hourly():
    """Aggregate sensor data hourly (runs every hour)."""
    try:
        db = await get_database()
        data_repo = MongoSensorDataRepository(db)
        sensor_repo = MongoIoTSensorRepository(db)

        # Get all active sensors
        sensors = await sensor_repo.list(skip=0, limit=1000, status="online")

        # Aggregate data for the last hour
        to_time = datetime.utcnow()
        from_time = to_time - timedelta(hours=1)

        aggregated_count = 0
        for sensor in sensors:
            try:
                aggregated = await data_repo.aggregate_readings(
                    str(sensor.id),
                    from_time,
                    to_time,
                    granularity="hour"
                )
                aggregated_count += len(aggregated)
            except Exception as e:
                logger.error(f"Error aggregating data for sensor {sensor.sensor_code}: {e}")
                continue

        logger.info(f"Aggregated data for {len(sensors)} sensors, {aggregated_count} data points")
        return {"sensors_processed": len(sensors), "data_points": aggregated_count}
    except Exception as e:
        logger.error(f"Error aggregating sensor data: {e}")
        raise
