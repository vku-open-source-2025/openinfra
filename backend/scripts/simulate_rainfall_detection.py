#!/usr/bin/env python3
"""
Simulate IoT Rainfall Sensor Data and Trigger AI Risk Detection

This script generates realistic rainfall sensor data and demonstrates
the AI automated risk detection system.

Usage:
    python scripts/simulate_rainfall_detection.py [--scenario normal|spike|gradual|mixed]
    python scripts/simulate_rainfall_detection.py --scenario spike --trigger-task

Scenarios:
    normal: Normal rainfall pattern (no anomalies expected)
    spike: Sudden spike in rainfall (should detect anomaly)
    gradual: Gradual increase (may detect if significant)
    mixed: Combination of patterns
"""

import asyncio
import sys
import os
import random
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from app.core.config import settings
from app.infrastructure.database.mongodb import db, get_database
from app.services.rain_forecast_service import RainForecastService
from app.tasks.sensor_monitoring import detect_ai_risks
from app.domain.services.alert_service import AlertService
from app.domain.models.alert import Alert, AlertSeverity, AlertSourceType
from app.infrastructure.database.repositories.mongo_alert_repository import (
    MongoAlertRepository,
)
from app.infrastructure.database.repositories.mongo_incident_repository import (
    MongoIncidentRepository,
)
from app.domain.services.incident_service import IncidentService
from app.domain.models.incident import (
    IncidentCreate,
    IncidentCategory,
    IncidentSeverity as IncidentSeverityEnum,
    ReporterType,
)
import uuid

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("DATABASE_NAME", os.getenv("MONGODB_DB", "gis_db"))


class RainfallSimulator:
    """Simulate rainfall sensor data with various patterns."""

    def __init__(self, sensor_id: str, asset_id: str):
        self.sensor_id = sensor_id
        self.asset_id = asset_id
        self.cumulative_rainfall = 0.0  # Track cumulative rainfall

    def generate_historical_data(
        self, days: int = 7, interval_minutes: int = 15
    ) -> List[Dict]:
        """
        Generate historical rainfall data for ARIMA model training.

        Args:
            days: Number of days of historical data
            interval_minutes: Interval between readings

        Returns:
            List of reading dictionaries
        """
        readings = []
        end_time = datetime.utcnow() - timedelta(hours=1)  # End 1 hour ago
        start_time = end_time - timedelta(days=days)
        current_time = start_time

        # Reset cumulative for historical data
        self.cumulative_rainfall = 0.0

        while current_time <= end_time:
            hour = current_time.hour
            day_of_week = current_time.weekday()

            # Simulate realistic rainfall patterns:
            # - More rain during certain hours (afternoon storms)
            # - Some daily variation
            # - Occasional rain events

            # Base probability of rain
            if 14 <= hour <= 18:  # Afternoon
                rain_probability = 0.3
                intensity_multiplier = 1.5
            elif 6 <= hour <= 10:  # Morning
                rain_probability = 0.2
                intensity_multiplier = 1.2
            else:  # Night/evening
                rain_probability = 0.1
                intensity_multiplier = 0.8

            # Check if it's raining
            is_raining = random.random() < rain_probability

            if is_raining:
                # Generate rainfall amount (mm per interval)
                base_rate = random.uniform(0.1, 2.0) * intensity_multiplier
                # Add some variation
                rate = max(0, base_rate + np.random.normal(0, 0.3))
            else:
                rate = 0.0

            # Update cumulative rainfall
            self.cumulative_rainfall += rate * (interval_minutes / 60.0)

            reading = {
                "sensor_id": self.sensor_id,
                "asset_id": self.asset_id,
                "timestamp": current_time,
                "value": self.cumulative_rainfall,
                "unit": "mm",
                "quality": "good",
                "quality_flags": [],
                "status": "normal",
                "threshold_exceeded": False,
                "metadata": {
                    "source": "simulation",
                    "rate_mm_per_hour": rate * (60 / interval_minutes),
                    "scenario": "historical",
                },
            }

            readings.append(reading)
            current_time += timedelta(minutes=interval_minutes)

        return readings

    def generate_current_readings(
        self,
        scenario: str = "normal",
        hours: int = 2,
        interval_minutes: int = 15,
    ) -> List[Dict]:
        """
        Generate current readings with specified scenario.

        Args:
            scenario: 'normal', 'spike', 'gradual', or 'mixed'
            hours: Number of hours of current data
            interval_minutes: Interval between readings

        Returns:
            List of reading dictionaries
        """
        readings = []
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        current_time = start_time

        if scenario == "spike":
            # Generate sudden spike pattern
            readings = self._generate_spike_pattern(
                start_time, end_time, interval_minutes
            )
        elif scenario == "gradual":
            # Generate gradual increase
            readings = self._generate_gradual_pattern(
                start_time, end_time, interval_minutes
            )
        elif scenario == "mixed":
            # Mix of patterns
            readings = self._generate_mixed_pattern(
                start_time, end_time, interval_minutes
            )
        else:  # normal
            readings = self._generate_normal_pattern(
                start_time, end_time, interval_minutes
            )

        return readings

    def _generate_normal_pattern(
        self, start_time: datetime, end_time: datetime, interval_minutes: int
    ) -> List[Dict]:
        """Generate normal rainfall pattern."""
        readings = []
        current_time = start_time

        while current_time <= end_time:
            hour = current_time.hour
            # Normal pattern: occasional light rain
            rain_probability = 0.15 if 14 <= hour <= 18 else 0.05

            if random.random() < rain_probability:
                rate = random.uniform(0.1, 1.5)  # Light to moderate rain
            else:
                rate = 0.0

            self.cumulative_rainfall += rate * (interval_minutes / 60.0)

            reading = {
                "sensor_id": self.sensor_id,
                "asset_id": self.asset_id,
                "timestamp": current_time,
                "value": self.cumulative_rainfall,
                "unit": "mm",
                "quality": "good",
                "quality_flags": [],
                "status": "normal",
                "threshold_exceeded": False,
                "metadata": {
                    "source": "simulation",
                    "rate_mm_per_hour": rate * (60 / interval_minutes),
                    "scenario": "normal",
                },
            }

            readings.append(reading)
            current_time += timedelta(minutes=interval_minutes)

        return readings

    def _generate_spike_pattern(
        self, start_time: datetime, end_time: datetime, interval_minutes: int
    ) -> List[Dict]:
        """
        Generate sudden spike pattern (anomaly scenario).
        Creates a dramatic spike that accumulates to 200-400 mm total.
        This will definitely trigger AI risk detection due to the high rate of change.
        """
        readings = []
        current_time = start_time
        spike_started = False

        # Target accumulation: 200-400 mm total
        target_accumulation = random.uniform(200.0, 400.0)

        # Get starting baseline (from historical data or previous readings)
        baseline_at_start = self.cumulative_rainfall

        # Calculate spike duration (last hour of the period for dramatic effect)
        total_duration_hours = (end_time - start_time).total_seconds() / 3600
        spike_start_hour = max(
            0.5, total_duration_hours - 1.0
        )  # Start spike in last hour
        spike_duration_hours = total_duration_hours - spike_start_hour

        # Calculate how much we need to accumulate during current period
        # If baseline is already high, we still want to add significant spike
        if baseline_at_start >= target_accumulation:
            # Already at or above target, add dramatic spike anyway (50-150 mm more)
            spike_accumulation_needed = random.uniform(50.0, 150.0)
            final_target = baseline_at_start + spike_accumulation_needed
        else:
            # Need to reach target from baseline
            spike_accumulation_needed = target_accumulation - baseline_at_start
            final_target = target_accumulation

        # Calculate average rate needed during spike period
        if spike_duration_hours > 0:
            avg_spike_rate = spike_accumulation_needed / spike_duration_hours
        else:
            avg_spike_rate = spike_accumulation_needed

        # Ensure spike rate is dramatic (minimum 50 mm/hour for detection)
        # For a spike from baseline to 200-400 mm in 1 hour, rate will be 100-400 mm/hour
        min_spike_rate = max(50.0, avg_spike_rate * 0.7)  # At least 70% of needed rate
        max_spike_rate = max(100.0, avg_spike_rate * 1.5)  # Up to 150% for variation

        spike_accumulated = 0.0
        baseline_accumulation = baseline_at_start

        while current_time <= end_time:
            elapsed_hours = (current_time - start_time).total_seconds() / 3600

            # Normal pattern before spike (minimal accumulation)
            if elapsed_hours < spike_start_hour:
                rain_probability = 0.05  # Very light rain before spike
                if random.random() < rain_probability:
                    rate = random.uniform(0.1, 0.5)  # Very light rain
                else:
                    rate = 0.0
                baseline_accumulation += rate * (interval_minutes / 60.0)
                self.cumulative_rainfall = baseline_accumulation
            else:
                # Spike period: intense rainfall
                if not spike_started:
                    spike_started = True
                    # Very high initial rate to start the spike dramatically
                    rate = random.uniform(min_spike_rate, max_spike_rate)
                else:
                    # Continue spike with varying intensity
                    # Ensure we reach target accumulation
                    remaining_needed = spike_accumulation_needed - spike_accumulated
                    remaining_time_hours = (
                        end_time - current_time
                    ).total_seconds() / 3600

                    if remaining_time_hours > 0.01:  # More than 36 seconds remaining
                        # Calculate rate needed to reach target
                        required_rate = remaining_needed / remaining_time_hours
                        # Add variation but ensure we're on track to reach target
                        rate = random.uniform(
                            max(min_spike_rate, required_rate * 0.8),
                            max(max_spike_rate, required_rate * 1.2),
                        )
                    else:
                        # Last reading - ensure we hit target exactly
                        if remaining_needed > 0:
                            rate = remaining_needed / (interval_minutes / 60.0)
                        else:
                            rate = random.uniform(10.0, 30.0)  # Continue heavy rain

                # Add spike accumulation
                spike_increment = rate * (interval_minutes / 60.0)
                spike_accumulated += spike_increment
                self.cumulative_rainfall = baseline_accumulation + spike_accumulated

                # Cap at reasonable maximum (slightly above target for realism)
                if self.cumulative_rainfall >= final_target:
                    self.cumulative_rainfall = min(
                        final_target * 1.02,  # Allow 2% over target
                        self.cumulative_rainfall,
                    )

            reading = {
                "sensor_id": self.sensor_id,
                "asset_id": self.asset_id,
                "timestamp": current_time,
                "value": self.cumulative_rainfall,
                "unit": "mm",
                "quality": "good",
                "quality_flags": [],
                "status": "normal",
                "threshold_exceeded": False,
                "metadata": {
                    "source": "simulation",
                    "rate_mm_per_hour": rate * (60 / interval_minutes),
                    "scenario": "spike",
                    "target_accumulation": final_target,
                },
            }

            readings.append(reading)
            current_time += timedelta(minutes=interval_minutes)

        return readings

    def _generate_gradual_pattern(
        self, start_time: datetime, end_time: datetime, interval_minutes: int
    ) -> List[Dict]:
        """Generate gradual increase pattern."""
        readings = []
        current_time = start_time

        while current_time <= end_time:
            elapsed_hours = (current_time - start_time).total_seconds() / 3600

            # Gradually increase rainfall rate
            base_rate = elapsed_hours * 2.0  # Gradual increase
            rate = max(0, base_rate + random.uniform(-0.5, 1.0))

            self.cumulative_rainfall += rate * (interval_minutes / 60.0)

            reading = {
                "sensor_id": self.sensor_id,
                "asset_id": self.asset_id,
                "timestamp": current_time,
                "value": self.cumulative_rainfall,
                "unit": "mm",
                "quality": "good",
                "quality_flags": [],
                "status": "normal",
                "threshold_exceeded": False,
                "metadata": {
                    "source": "simulation",
                    "rate_mm_per_hour": rate * (60 / interval_minutes),
                    "scenario": "gradual",
                },
            }

            readings.append(reading)
            current_time += timedelta(minutes=interval_minutes)

        return readings

    def _generate_mixed_pattern(
        self, start_time: datetime, end_time: datetime, interval_minutes: int
    ) -> List[Dict]:
        """Generate mixed pattern (normal + spike)."""
        readings = []
        current_time = start_time
        spike_occurred = False

        while current_time <= end_time:
            elapsed_hours = (current_time - start_time).total_seconds() / 3600

            # Normal pattern for first hour, then spike
            if elapsed_hours < 1.0:
                rain_probability = 0.1
                if random.random() < rain_probability:
                    rate = random.uniform(0.1, 1.0)
                else:
                    rate = 0.0
            elif elapsed_hours < 1.5 and not spike_occurred:
                # Sudden spike
                spike_occurred = True
                rate = random.uniform(18.0, 25.0)
            elif spike_occurred and elapsed_hours < 1.8:
                # Continue spike
                rate = random.uniform(12.0, 18.0)
            else:
                # Return to normal
                rain_probability = 0.1
                if random.random() < rain_probability:
                    rate = random.uniform(0.1, 1.5)
                else:
                    rate = 0.0

            self.cumulative_rainfall += rate * (interval_minutes / 60.0)

            reading = {
                "sensor_id": self.sensor_id,
                "asset_id": self.asset_id,
                "timestamp": current_time,
                "value": self.cumulative_rainfall,
                "unit": "mm",
                "quality": "good",
                "quality_flags": [],
                "status": "normal",
                "threshold_exceeded": False,
                "metadata": {
                    "source": "simulation",
                    "rate_mm_per_hour": rate * (60 / interval_minutes),
                    "scenario": "mixed",
                },
            }

            readings.append(reading)
            current_time += timedelta(minutes=interval_minutes)

        return readings


async def get_or_create_rainfall_sensor(database) -> tuple[str, str]:
    """
    Get or create a rainfall sensor for testing.

    Returns:
        Tuple of (sensor_id, asset_id)
    """
    # Try to find existing rainfall sensor
    existing_sensor = await database["iot_sensors"].find_one(
        {"sensor_type": "rainfall"}
    )

    if existing_sensor:
        sensor_id = str(existing_sensor["_id"])
        asset_id = existing_sensor.get("asset_id", "")
        print(f"✓ Found existing rainfall sensor: {sensor_id}")
        return sensor_id, asset_id

    # Create a test asset if needed
    test_asset = await database["assets"].find_one({"feature_code": "cong_thoat_nuoc"})
    if not test_asset:
        # Create a simple test asset
        asset_result = await database["assets"].insert_one(
            {
                "feature_code": "cong_thoat_nuoc",
                "feature_type": "Cống thoát nước",
                "ten": "Test Rainfall Asset",
                "geometry": {
                    "type": "Point",
                    "coordinates": [108.0, 16.0],
                },
                "created_at": datetime.utcnow(),
            }
        )
        asset_id = str(asset_result.inserted_id)
        print(f"✓ Created test asset: {asset_id}")
    else:
        asset_id = str(test_asset["_id"])

    # Create rainfall sensor
    sensor_result = await database["iot_sensors"].insert_one(
        {
            "sensor_code": f"RAIN-SIM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "asset_id": asset_id,
            "sensor_type": "rainfall",
            "measurement_unit": "mm",
            "sample_rate": 60,
            "status": "online",
            "connection_type": "wifi",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    )

    sensor_id = str(sensor_result.inserted_id)
    print(f"✓ Created rainfall sensor: {sensor_id}")
    return sensor_id, asset_id


async def insert_readings(database, readings: List[Dict]) -> int:
    """Insert readings into MongoDB."""
    if not readings:
        return 0

    # Bulk insert
    result = await database["sensor_readings"].insert_many(readings)
    return len(result.inserted_ids)


async def run_ai_detection(database, sensor_id: str) -> Dict:
    """Run AI risk detection for the sensor."""
    # Get recent readings (last hour)
    to_time = datetime.utcnow()
    from_time = to_time - timedelta(hours=1)

    cursor = (
        database["sensor_readings"]
        .find(
            {
                "sensor_id": sensor_id,
                "timestamp": {"$gte": from_time, "$lte": to_time},
            }
        )
        .sort("timestamp", 1)
    )

    readings = []
    async for reading in cursor:
        readings.append(
            {
                "timestamp": reading.get("timestamp"),
                "value": reading.get("value"),
                "unit": reading.get("unit"),
                "quality": reading.get("quality"),
                "status": reading.get("status"),
                "metadata": reading.get("metadata", {}),
            }
        )

    # Get sensor info
    sensor = await database["iot_sensors"].find_one({"_id": ObjectId(sensor_id)})
    if not sensor:
        return {"error": "Sensor not found"}

    sensor_type = sensor.get("sensor_type", "rainfall")

    # Group readings for detection
    grouped_readings = {
        sensor_id: {
            "sensor_type": sensor_type,
            "readings": readings,
            "sensor_info": {
                "sensor_code": sensor.get("sensor_code"),
                "asset_id": sensor.get("asset_id"),
                "manufacturer": sensor.get("manufacturer"),
                "model": sensor.get("model"),
                "measurement_unit": sensor.get("measurement_unit", "mm"),
            },
        }
    }

    # Run detection
    result = await detect_ai_risks(grouped_readings, db=database)

    # Create alerts and incidents for detected risks
    alert_repo = MongoAlertRepository(database)
    alert_service = AlertService(alert_repo)
    incident_repo = MongoIncidentRepository(database)
    incident_service = IncidentService(incident_repo)
    alerts_created = 0
    incidents_created = 0

    for risk in result.get("risks", []):
        try:
            risk_level = risk.get("risk_level", "low")
            sensor_id = risk["sensor_id"]
            sensor_info = grouped_readings[sensor_id]["sensor_info"]
            asset_id = sensor_info["asset_id"]

            # Map risk level to alert severity
            severity_mapping = {
                "critical": AlertSeverity.CRITICAL,
                "high": AlertSeverity.CRITICAL,
                "medium": AlertSeverity.WARNING,
                "low": AlertSeverity.INFO,
            }

            severity = severity_mapping.get(risk_level, AlertSeverity.INFO)

            # Create alert for detected risk
            alert = Alert(
                alert_code=f"AI-RISK-{uuid.uuid4().hex[:8].upper()}",
                source_type=AlertSourceType.SENSOR,
                sensor_id=sensor_id,
                asset_id=asset_id,
                type="ai_risk_detection",
                severity=severity,
                title=f"AI Detected Risk: {risk.get('risk_type', 'Unknown')}",
                message=risk.get(
                    "description", "AI risk detection identified a potential issue"
                ),
                triggered_at=risk.get("detected_at", datetime.utcnow()),
                metadata={
                    "risk_level": risk_level,
                    "risk_type": risk.get("risk_type"),
                    "confidence": risk.get("confidence"),
                    "sensor_type": risk.get("sensor_type"),
                    "statistics": risk.get("statistics", {}),
                },
            )

            created_alert = await alert_service.create_alert(alert)
            alerts_created += 1

            # Create incident for critical/high risks
            if risk_level in ["critical", "high"]:
                try:
                    # Map risk level to incident severity
                    incident_severity_mapping = {
                        "critical": IncidentSeverityEnum.CRITICAL,
                        "high": IncidentSeverityEnum.HIGH,
                    }
                    incident_severity = incident_severity_mapping.get(
                        risk_level, IncidentSeverityEnum.MEDIUM
                    )

                    # Map risk type to incident category
                    risk_type = risk.get("risk_type", "").lower()
                    if "rain" in risk_type or "flood" in risk_type:
                        incident_category = IncidentCategory.SAFETY_HAZARD
                    elif "water" in risk_type or "level" in risk_type:
                        incident_category = IncidentCategory.MALFUNCTION
                    else:
                        incident_category = IncidentCategory.OTHER

                    # Map risk level to Vietnamese
                    risk_level_vn = {
                        "critical": "Nghiêm Trọng",
                        "high": "Cao",
                        "medium": "Trung Bình",
                        "low": "Thấp",
                    }.get(risk_level, risk_level.upper())

                    # Map risk type to Vietnamese
                    risk_type = risk.get("risk_type", "Unknown")
                    risk_type_vn = {
                        "abnormal_rain_accumulation": "Tích Tụ Mưa Bất Thường",
                        "elevated_reading": "Giá Trị Đo Cao",
                        "flood_risk": "Nguy Cơ Lũ Lụt",
                        "water_level_high": "Mực Nước Cao",
                    }.get(risk_type.lower(), risk_type)

                    # Create incident with Vietnamese description
                    sensor_code = sensor_info.get("sensor_code", sensor_id)
                    confidence_pct = risk.get("confidence", 0) * 100

                    # Translate description to Vietnamese or generate Vietnamese description
                    original_description = risk.get("description", "")
                    if original_description:
                        # Translate common English patterns to Vietnamese
                        description_vn = original_description
                        # Translate common phrases
                        description_vn = description_vn.replace(
                            "Abnormal rain accumulation detected",
                            "Phát hiện tích tụ mưa bất thường",
                        )
                        description_vn = description_vn.replace(
                            "Current rate", "Tốc độ hiện tại"
                        )
                        description_vn = description_vn.replace(
                            "exceeds forecast", "vượt quá dự báo"
                        )
                        description_vn = description_vn.replace("mm/h", "mm/giờ")
                        description_vn = description_vn.replace("Threshold", "Ngưỡng")
                        description_vn = description_vn.replace(
                            "High rain accumulation rate detected",
                            "Phát hiện tốc độ tích tụ mưa cao",
                        )
                        description_vn = description_vn.replace("threshold", "ngưỡng")
                        description_vn = description_vn.replace(
                            "Water level readings show elevated values",
                            "Giá trị đo mực nước cho thấy mức độ cao",
                        )
                        description_vn = description_vn.replace("max", "tối đa")

                        # If still mostly English, generate Vietnamese description from risk data
                        if any(
                            word in description_vn.lower()
                            for word in [
                                "detected",
                                "exceeds",
                                "threshold",
                                "readings show",
                            ]
                        ):
                            # Generate Vietnamese description from risk metadata
                            forecast_data = risk.get("forecast_data", {})
                            statistics = risk.get("statistics", {})

                            if forecast_data:
                                current_rate = forecast_data.get("current_rate", 0)
                                forecast_rate = forecast_data.get("forecast_rate", 0)
                                description_vn = (
                                    f"Phát hiện tích tụ mưa bất thường: "
                                    f"Tốc độ hiện tại {current_rate:.2f} mm/giờ vượt quá dự báo "
                                    f"{forecast_rate:.2f} mm/giờ."
                                )
                            elif statistics:
                                max_value = statistics.get("max", 0)
                                description_vn = (
                                    f"Giá trị đo mực nước cho thấy mức độ cao "
                                    f"(tối đa: {max_value:.2f} {sensor_info.get('measurement_unit', '')})."
                                )
                            else:
                                description_vn = (
                                    f"Hệ thống phát hiện rủi ro AI đã xác định một rủi ro mức {risk_level_vn.lower()} cho cảm biến {sensor_code}. "
                                    f"Loại rủi ro: {risk_type_vn}. "
                                    f"Độ tin cậy: {confidence_pct:.1f}%."
                                )
                    else:
                        # Generate Vietnamese description from risk data
                        forecast_data = risk.get("forecast_data", {})
                        statistics = risk.get("statistics", {})

                        if forecast_data:
                            current_rate = forecast_data.get("current_rate", 0)
                            forecast_rate = forecast_data.get("forecast_rate", 0)
                            description_vn = (
                                f"Phát hiện tích tụ mưa bất thường: "
                                f"Tốc độ hiện tại {current_rate:.2f} mm/giờ vượt quá dự báo "
                                f"{forecast_rate:.2f} mm/giờ."
                            )
                        elif statistics:
                            max_value = statistics.get("max", 0)
                            description_vn = (
                                f"Giá trị đo mực nước cho thấy mức độ cao "
                                f"(tối đa: {max_value:.2f} {sensor_info.get('measurement_unit', '')})."
                            )
                        else:
                            description_vn = (
                                f"Hệ thống phát hiện rủi ro AI đã xác định một rủi ro mức {risk_level_vn.lower()} cho cảm biến {sensor_code}. "
                                f"Loại rủi ro: {risk_type_vn}. "
                                f"Độ tin cậy: {confidence_pct:.1f}%."
                            )

                    incident_data = IncidentCreate(
                        asset_id=asset_id,
                        title=f"AI Phát Hiện Rủi Ro {risk_level_vn}: {risk_type_vn}",
                        description=description_vn,
                        category=incident_category,
                        severity=incident_severity,
                        reported_via="system",
                        public_visible=False,
                    )

                    created_incident = await incident_service.create_incident(
                        incident_data,
                        reported_by=None,
                        reporter_type=ReporterType.SYSTEM.value,
                    )

                    # Link alert to incident
                    await alert_repo.update(
                        str(created_alert.id),
                        {
                            "incident_created": True,
                            "incident_id": str(created_incident.id),
                        },
                    )

                    incidents_created += 1
                    print(
                        f"✓ Created incident {created_incident.incident_number} for risk {risk.get('risk_type')}"
                    )

                except Exception as e:
                    print(f"⚠ Error creating incident for risk {sensor_id}: {e}")
                    # Continue even if incident creation fails

        except Exception as e:
            print(f"⚠ Error creating alert for risk {risk.get('sensor_id')}: {e}")
            continue

    # Add creation counts to result
    result["alerts_created"] = alerts_created
    result["incidents_created"] = incidents_created

    return result


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Simulate rainfall sensor data and trigger AI detection"
    )
    parser.add_argument(
        "--scenario",
        choices=["normal", "spike", "gradual", "mixed"],
        default="spike",
        help="Rainfall scenario to simulate",
    )
    parser.add_argument(
        "--trigger-task",
        action="store_true",
        help="Trigger the Celery task instead of direct detection",
    )
    parser.add_argument(
        "--skip-historical",
        action="store_true",
        help="Skip generating historical data (use existing)",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=2,
        help="Number of hours of current data to generate",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Rainfall Sensor Data Simulation & AI Detection")
    print("=" * 70)
    print(f"Scenario: {args.scenario}")
    print(f"Current data hours: {args.hours}")
    print()

    # Connect to database
    db.connect()
    if db.client is None:
        print("❌ Failed to connect to database")
        return
    database = await get_database()
    if database is None:
        print("❌ Failed to get database instance")
        return
    print("✓ Connected to database")

    # Get or create sensor
    sensor_id, asset_id = await get_or_create_rainfall_sensor(database)
    print()

    # Generate historical data (7 days for ARIMA training)
    if not args.skip_historical:
        print("Generating historical data (7 days)...")
        simulator = RainfallSimulator(sensor_id, asset_id)
        historical_readings = simulator.generate_historical_data(
            days=7, interval_minutes=15
        )

        # Check if we already have enough historical data
        existing_count = await database["sensor_readings"].count_documents(
            {"sensor_id": sensor_id}
        )

        if existing_count < len(historical_readings):
            # Clear old simulated data
            await database["sensor_readings"].delete_many(
                {
                    "sensor_id": sensor_id,
                    "metadata.source": "simulation",
                }
            )

            # Insert historical data
            inserted = await insert_readings(database, historical_readings)
            print(f"✓ Inserted {inserted} historical readings")
        else:
            print(f"✓ Historical data already exists ({existing_count} readings)")
    else:
        print("⏭ Skipping historical data generation")
        simulator = RainfallSimulator(sensor_id, asset_id)

    print()

    # Generate current readings with specified scenario
    print(f"Generating current readings (scenario: {args.scenario})...")
    current_readings = simulator.generate_current_readings(
        scenario=args.scenario, hours=args.hours, interval_minutes=15
    )

    # Insert current readings
    inserted = await insert_readings(database, current_readings)
    print(f"✓ Inserted {inserted} current readings")
    print()

    # Show reading statistics
    if current_readings:
        values = [r["value"] for r in current_readings]
        rates = [r["metadata"].get("rate_mm_per_hour", 0) for r in current_readings]
        print("Reading Statistics:")
        print(f"  Total readings: {len(current_readings)}")
        print(f"  Cumulative rainfall: {max(values):.2f} mm")
        print(f"  Max rate: {max(rates):.2f} mm/hour")
        print(f"  Avg rate: {sum(rates) / len(rates):.2f} mm/hour")
        print()

    # Run AI detection
    if args.trigger_task:
        print("⚠ Triggering Celery task (ai_automated_risk_detection)...")
        print("   Note: This requires Celery worker to be running")
        print("   Run: celery -A app.celery_app worker --loglevel=info")
        print("   Then: celery -A app.celery_app beat --loglevel=info")
        print()
        print("   Or trigger manually:")
        print(f"   from app.tasks.sensor_monitoring import ai_automated_risk_detection")
        print(f"   await ai_automated_risk_detection()")
    else:
        print("Running AI risk detection...")
        print("-" * 70)

        detection_result = await run_ai_detection(database, sensor_id)

        if "error" in detection_result:
            print(f"❌ Error: {detection_result['error']}")
        else:
            risks = detection_result.get("risks", [])
            summary = detection_result.get("summary", {})

            print(f"\nDetection Results:")
            print(f"  Sensors processed: {len(detection_result.get('risks', []))}")
            print(f"  Total risks detected: {summary.get('total_risks', 0)}")
            print(f"  Critical risks: {summary.get('critical_risks', 0)}")
            print(f"  Warning risks: {summary.get('warning_risks', 0)}")
            print(f"  Info risks: {summary.get('info_risks', 0)}")
            print(f"  Alerts created: {detection_result.get('alerts_created', 0)}")
            print(
                f"  Incidents created: {detection_result.get('incidents_created', 0)}"
            )
            print()

            if risks:
                print("Detected Risks:")
                for i, risk in enumerate(risks, 1):
                    print(f"\n  Risk #{i}:")
                    print(f"    Type: {risk.get('risk_type', 'unknown')}")
                    print(f"    Level: {risk.get('risk_level', 'unknown')}")
                    print(f"    Confidence: {risk.get('confidence', 0):.2%}")
                    print(f"    Description: {risk.get('description', 'N/A')}")

                    forecast_data = risk.get("forecast_data", {})
                    if forecast_data:
                        print(f"    Forecast:")
                        print(
                            f"      Method: {forecast_data.get('forecast_method', 'N/A')}"
                        )
                        print(
                            f"      Forecast rate: {forecast_data.get('forecast_rate', 0):.2f} mm/h"
                        )
                        print(
                            f"      Current rate: {forecast_data.get('current_rate', 0):.2f} mm/h"
                        )
            else:
                print("✓ No risks detected (normal pattern)")

    print()
    print("=" * 70)
    print("Simulation complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
