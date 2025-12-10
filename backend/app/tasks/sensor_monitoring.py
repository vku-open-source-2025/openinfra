"""Celery tasks for IoT sensor monitoring."""

from app.celery_app import app as celery_app
from app.infrastructure.database.mongodb import get_database
from app.domain.services.alert_service import AlertService
from app.domain.services.iot_service import IoTService
from app.domain.models.alert import Alert, AlertSeverity, AlertSourceType
from app.infrastructure.database.repositories.mongo_iot_repository import (
    MongoIoTSensorRepository,
)
from app.infrastructure.database.repositories.mongo_sensor_data_repository import (
    MongoSensorDataRepository,
)
from app.infrastructure.database.repositories.mongo_alert_repository import (
    MongoAlertRepository,
)
from app.services.rain_forecast_service import RainForecastService
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
                skip=0, limit=1, status="active", asset_id=sensor.asset_id
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
                    triggered_at=datetime.utcnow(),
                )
                await alert_service.create_alert(alert)
                alerts_created += 1

        logger.info(
            f"Checked {len(offline_sensors)} offline sensors, created {alerts_created} alerts"
        )
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
                    str(sensor.id), from_time, to_time, granularity="hour"
                )
                aggregated_count += len(aggregated)
            except Exception as e:
                logger.error(
                    f"Error aggregating data for sensor {sensor.sensor_code}: {e}"
                )
                continue

        logger.info(
            f"Aggregated data for {len(sensors)} sensors, {aggregated_count} data points"
        )
        return {"sensors_processed": len(sensors), "data_points": aggregated_count}
    except Exception as e:
        logger.error(f"Error aggregating sensor data: {e}")
        raise


async def detect_ai_risks(grouped_readings: dict, db=None) -> dict:
    """
    AI-powered risk detection algorithm.

    This function will analyze sensor readings grouped by sensor and sensor type
    to detect anomalies, patterns, and potential risks.

    Args:
        grouped_readings: Dictionary with structure:
            {
                "sensor_id": {
                    "sensor_type": "temperature",
                    "readings": [{"timestamp": ..., "value": ..., ...}, ...],
                    "sensor_info": {...}
                }
            }
        db: Database connection (required for rainfall forecast service)

    Returns:
        Dictionary containing detected risks:
        {
            "risks": [
                {
                    "sensor_id": "...",
                    "sensor_type": "...",
                    "risk_level": "low|medium|high|critical",
                    "risk_type": "...",
                    "description": "...",
                    "confidence": 0.0-1.0,
                    "detected_at": datetime
                }
            ],
            "summary": {
                "total_risks": 0,
                "critical_risks": 0,
                "warning_risks": 0,
                "info_risks": 0
            }
        }
    """
    risks = []
    summary = {
        "total_risks": 0,
        "critical_risks": 0,
        "warning_risks": 0,
        "info_risks": 0,
    }

    # Initialize rain forecast service if database is available
    rain_forecast_service = None
    if db:
        try:
            rain_forecast_service = RainForecastService(db)
        except Exception as e:
            logger.warning(f"Could not initialize rain forecast service: {e}")

    # Analyze each sensor group
    for sensor_id, sensor_data in grouped_readings.items():
        readings = sensor_data.get("readings", [])
        if not readings:
            continue

        sensor_type = sensor_data.get("sensor_type", "unknown")

        # Rainfall sensor: Use ARIMA forecast model for anomaly detection
        if sensor_type == "rainfall" and rain_forecast_service:
            try:
                risk_result = await rain_forecast_service.analyze_rainfall_sensor(
                    sensor_id=sensor_id, readings=readings, db=db
                )

                if risk_result.get("anomaly_detected"):
                    risk_level = risk_result.get("severity", "medium")
                    risks.append(
                        {
                            "sensor_id": sensor_id,
                            "sensor_type": sensor_type,
                            "risk_level": risk_level,
                            "risk_type": risk_result.get(
                                "risk_type", "abnormal_rain_accumulation"
                            ),
                            "description": risk_result.get(
                                "description",
                                "Abnormal rain accumulation detected",
                            ),
                            "confidence": risk_result.get("confidence", 0.7),
                            "detected_at": datetime.utcnow(),
                            "forecast_data": risk_result.get("forecast_data", {}),
                        }
                    )

                    # Update summary
                    if risk_level == "critical":
                        summary["critical_risks"] += 1
                    elif risk_level == "high":
                        summary["critical_risks"] += 1  # High maps to critical
                    elif risk_level == "medium":
                        summary["warning_risks"] += 1
                    else:
                        summary["info_risks"] += 1

                    summary["total_risks"] += 1

            except Exception as e:
                logger.error(
                    f"Error in rainfall forecast analysis for sensor {sensor_id}: {e}",
                    exc_info=True,
                )
                # Fall through to basic detection

        # Water level sensor: Basic threshold detection
        elif sensor_type == "water_level":
            values = [r.get("value", 0) for r in readings if "value" in r]
            if not values:
                continue

            avg_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)

            if max_value > 10.0:
                risks.append(
                    {
                        "sensor_id": sensor_id,
                        "sensor_type": sensor_type,
                        "risk_level": "high",
                        "risk_type": "elevated_reading",
                        "description": f"Water level readings show elevated values (max: {max_value:.2f})",
                        "confidence": 0.7,
                        "detected_at": datetime.utcnow(),
                        "statistics": {
                            "avg": avg_value,
                            "min": min_value,
                            "max": max_value,
                            "count": len(values),
                        },
                    }
                )
                summary["critical_risks"] += 1
                summary["total_risks"] += 1

        # Other sensor types: Basic statistical analysis (placeholder)
        else:
            values = [r.get("value", 0) for r in readings if "value" in r]
            if not values:
                continue

            # Placeholder for future ML models for other sensor types
            # Currently no risk detection for other types
            pass

    return {"risks": risks, "summary": summary, "processed_at": datetime.utcnow()}


@celery_app.task(name="ai_automated_risk_detection")
async def ai_automated_risk_detection():
    """
    AI automated risk detection from sensor_reading data.
    Groups readings by IoT sensor and sensor type, then runs AI risk detection.
    """
    try:
        db = await get_database()
        sensor_repo = MongoIoTSensorRepository(db)

        # Get time window for analysis (last hour by default)
        to_time = datetime.utcnow()
        from_time = to_time - timedelta(hours=1)

        logger.info(
            f"Starting AI risk detection for readings from {from_time} to {to_time}"
        )

        # Query sensor readings from the time window
        readings_cursor = db["sensor_readings"].find(
            {"timestamp": {"$gte": from_time, "$lte": to_time}}
        )

        # Group readings by sensor_id
        readings_by_sensor = {}
        async for reading in readings_cursor:
            sensor_id = reading.get("sensor_id")
            if not sensor_id:
                continue

            if sensor_id not in readings_by_sensor:
                readings_by_sensor[sensor_id] = []

            readings_by_sensor[sensor_id].append(
                {
                    "timestamp": reading.get("timestamp"),
                    "value": reading.get("value"),
                    "unit": reading.get("unit"),
                    "quality": reading.get("quality"),
                    "status": reading.get("status"),
                    "metadata": reading.get("metadata", {}),
                }
            )

        # Get sensor information and group by sensor_id and sensor_type
        grouped_readings = {}
        for sensor_id, readings in readings_by_sensor.items():
            # Get sensor info
            sensor = await sensor_repo.find_by_id(sensor_id)
            if not sensor:
                # Try to find by sensor_code if sensor_id is not ObjectId
                continue

            sensor_type = (
                sensor.sensor_type.value
                if hasattr(sensor.sensor_type, "value")
                else str(sensor.sensor_type)
            )

            # Group by sensor_id and sensor_type
            if sensor_id not in grouped_readings:
                grouped_readings[sensor_id] = {
                    "sensor_type": sensor_type,
                    "readings": readings,
                    "sensor_info": {
                        "sensor_code": sensor.sensor_code,
                        "asset_id": sensor.asset_id,
                        "manufacturer": sensor.manufacturer,
                        "model": sensor.model,
                        "measurement_unit": sensor.measurement_unit,
                    },
                }
            else:
                # Append readings if sensor already exists
                grouped_readings[sensor_id]["readings"].extend(readings)

        # Further group by sensor_type for analysis
        grouped_by_type = {}
        for sensor_id, sensor_data in grouped_readings.items():
            sensor_type = sensor_data["sensor_type"]
            if sensor_type not in grouped_by_type:
                grouped_by_type[sensor_type] = {}
            grouped_by_type[sensor_type][sensor_id] = sensor_data

        logger.info(
            f"Grouped {len(grouped_readings)} sensors into {len(grouped_by_type)} sensor types"
        )

        # Run AI risk detection on grouped data
        detection_results = await detect_ai_risks(grouped_readings, db=db)

        # Process detected risks and create alerts if needed
        alert_repo = MongoAlertRepository(db)
        alert_service = AlertService(alert_repo)
        alerts_created = 0

        for risk in detection_results.get("risks", []):
            try:
                # Map risk level to alert severity
                severity_mapping = {
                    "critical": AlertSeverity.CRITICAL,
                    "high": AlertSeverity.CRITICAL,  # High risks map to CRITICAL
                    "medium": AlertSeverity.WARNING,
                    "low": AlertSeverity.INFO,
                }

                severity = severity_mapping.get(
                    risk.get("risk_level", "low"), AlertSeverity.INFO
                )

                # Create alert for detected risk
                alert = Alert(
                    alert_code=f"AI-RISK-{uuid.uuid4().hex[:8].upper()}",
                    source_type=AlertSourceType.SENSOR,
                    sensor_id=risk["sensor_id"],
                    asset_id=grouped_readings[risk["sensor_id"]]["sensor_info"][
                        "asset_id"
                    ],
                    type="ai_risk_detection",
                    severity=severity,
                    title=f"AI Detected Risk: {risk.get('risk_type', 'Unknown')}",
                    message=risk.get(
                        "description", "AI risk detection identified a potential issue"
                    ),
                    triggered_at=risk.get("detected_at", datetime.utcnow()),
                    metadata={
                        "risk_level": risk.get("risk_level"),
                        "risk_type": risk.get("risk_type"),
                        "confidence": risk.get("confidence"),
                        "sensor_type": risk.get("sensor_type"),
                        "statistics": risk.get("statistics", {}),
                    },
                )

                await alert_service.create_alert(alert)
                alerts_created += 1

            except Exception as e:
                logger.error(
                    f"Error creating alert for risk {risk.get('sensor_id')}: {e}"
                )
                continue

        summary = detection_results.get("summary", {})
        logger.info(
            f"AI risk detection completed: "
            f"Processed {len(grouped_readings)} sensors, "
            f"Detected {summary.get('total_risks', 0)} risks, "
            f"Created {alerts_created} alerts"
        )

        return {
            "sensors_processed": len(grouped_readings),
            "sensor_types": len(grouped_by_type),
            "readings_analyzed": sum(
                len(data["readings"]) for data in grouped_readings.values()
            ),
            "risks_detected": summary.get("total_risks", 0),
            "alerts_created": alerts_created,
            "summary": summary,
            "time_window": {"from": from_time.isoformat(), "to": to_time.isoformat()},
        }

    except Exception as e:
        logger.error(f"Error in AI automated risk detection: {e}", exc_info=True)
        raise
