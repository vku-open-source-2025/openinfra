#!/usr/bin/env python3
"""Database seeding script for a single asset with full mock data."""
import asyncio
import sys
import os
import random
from datetime import datetime, timedelta
from typing import List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from app.core.config import settings
from app.core.logging import setup_logging
from app.domain.models.user import UserRole, UserStatus
from app.domain.models.asset import AssetStatus, AssetCondition, LifecycleStage
from app.domain.models.incident import (
    IncidentCategory,
    IncidentSeverity,
    IncidentStatus,
    ReporterType,
)
from app.domain.models.maintenance import (
    MaintenanceType,
    MaintenancePriority,
    MaintenanceStatus,
)
from app.domain.models.budget import (
    BudgetCategory,
    BudgetStatus,
    BudgetPeriodType,
)
from app.domain.models.iot_sensor import (
    SensorType,
    SensorStatus,
    ConnectionType,
)
from app.domain.models.alert import (
    AlertSeverity,
    AlertStatus,
    AlertSourceType,
)
from app.domain.models.report import (
    ReportType,
    ReportFormat,
    ReportStatus,
)

logger = setup_logging()


# Helper functions from seed_db.py
def generate_work_order_number(index: int) -> str:
    """Generate work order number."""
    year = datetime.now().year
    return f"WO-{year}-{index:05d}"


def generate_incident_number(index: int) -> str:
    """Generate incident number."""
    year = datetime.now().year
    return f"INC-{year}-{index:05d}"


def generate_sensor_code(index: int) -> str:
    """Generate sensor code."""
    return f"SENS-{index:05d}"


def generate_alert_code(index: int) -> str:
    """Generate alert code."""
    year = datetime.now().year
    return f"ALT-{year}-{index:05d}"


def generate_transaction_number(index: int) -> str:
    """Generate transaction number."""
    year = datetime.now().year
    return f"TXN-{year}-{index:06d}"


def generate_report_code(index: int) -> str:
    """Generate report code."""
    year = datetime.now().year
    return f"RPT-{year}-{index:05d}"


async def get_or_create_users(db) -> List[str]:
    """Get existing users or create sample users."""
    users = await db.users.find({}).to_list(length=10)
    if users:
        return [str(user["_id"]) for user in users]

    # Create a few users if none exist
    from app.core.security import get_password_hash

    users_data = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "password_hash": get_password_hash("admin123"),
            "full_name": "System Administrator",
            "phone": f"0{random.randint(3, 9)}{random.randint(10000000, 99999999)}",
            "role": UserRole.ADMIN.value,
            "status": UserStatus.ACTIVE.value,
            "department": "IT",
            "permissions": ["*"],
            "created_at": datetime.utcnow() - timedelta(days=365),
        },
        {
            "username": "technician1",
            "email": "tech1@example.com",
            "password_hash": get_password_hash("tech123"),
            "full_name": "Nguyen Van A",
            "phone": f"0{random.randint(3, 9)}{random.randint(10000000, 99999999)}",
            "role": UserRole.TECHNICIAN.value,
            "status": UserStatus.ACTIVE.value,
            "department": "Maintenance",
            "permissions": ["maintenance:read", "maintenance:write"],
            "created_at": datetime.utcnow() - timedelta(days=180),
        },
    ]
    result = await db.users.insert_many(users_data)
    return [str(id) for id in result.inserted_ids]


async def get_or_create_asset(db, user_ids: List[str]) -> str:
    """Get an existing asset or create a new one."""
    # Try to get an existing asset
    asset = await db.assets.find_one({"iot_enabled": True})

    if asset:
        logger.info(f"Using existing asset: {asset.get('asset_code', 'N/A')}")
        return str(asset["_id"])

    # Create a new asset
    location = {
        "lat": 16.0544,
        "lng": 108.2022,
        "district": "Hai Chau",
        "ward": "Thach Thang",
    }

    geometry = {
        "type": "Point",
        "coordinates": [location["lng"], location["lat"]],
    }

    asset_data = {
        "asset_code": "DGT-0001",
        "name": "Traffic Light - Bach Dang St.",
        "feature_type": "traffic_light",
        "feature_code": "DGT",
        "category": "traffic",
        "description": "Traffic signal control system at major intersection",
        "geometry": geometry,
        "location": {
            "district": location["district"],
            "ward": location["ward"],
            "address": "123 Bach Dang Street",
        },
        "specifications": {
            "voltage": "220V",
            "led_type": "LED",
            "poles": "galvanized_steel",
        },
        "status": AssetStatus.OPERATIONAL.value,
        "condition": AssetCondition.GOOD.value,
        "lifecycle_stage": LifecycleStage.OPERATIONAL.value,
        "installation_date": datetime.utcnow() - timedelta(days=1095),  # 3 years ago
        "iot_enabled": True,
        "public_info_visible": True,
        "maintenance_schedule": {
            "frequency": "quarterly",
            "last_maintenance": datetime.utcnow() - timedelta(days=60),
        },
        "created_by": user_ids[0] if user_ids else None,
        "created_at": datetime.utcnow() - timedelta(days=1095),
        "updated_at": datetime.utcnow() - timedelta(days=1),
    }

    result = await db.assets.insert_one(asset_data)
    logger.info(f"Created new asset: {asset_data['asset_code']}")
    return str(result.inserted_id)


async def seed_maintenance_history(
    db, asset_id: str, user_ids: List[str], count: int = 10
) -> List[str]:
    """Seed maintenance history for the asset."""
    logger.info(f"Seeding {count} maintenance records for asset...")

    maintenance_data = []
    wo_index = 1

    # Realistic maintenance tasks
    maintenance_tasks = [
        {
            "type": MaintenanceType.PREVENTIVE,
            "title": "Traffic light routine inspection",
            "description": "Quarterly inspection of traffic signal system, check bulbs, wiring, and timing controls.",
            "duration": 120,
            "priority": MaintenancePriority.MEDIUM,
        },
        {
            "type": MaintenanceType.PREVENTIVE,
            "title": "LED bulb replacement",
            "description": "Replace aging LED bulbs with new ones. Check electrical connections.",
            "duration": 60,
            "priority": MaintenancePriority.LOW,
        },
        {
            "type": MaintenanceType.CORRECTIVE,
            "title": "Repair damaged traffic light",
            "description": "Fix malfunctioning traffic light fixture and repair electrical wiring.",
            "duration": 180,
            "priority": MaintenancePriority.HIGH,
        },
        {
            "type": MaintenanceType.EMERGENCY,
            "title": "Emergency traffic light repair",
            "description": "Urgent repair of traffic light causing safety hazard at intersection.",
            "duration": 120,
            "priority": MaintenancePriority.CRITICAL,
        },
        {
            "type": MaintenanceType.PREVENTIVE,
            "title": "System calibration",
            "description": "Calibrate timing controls and verify all signals working correctly.",
            "duration": 90,
            "priority": MaintenancePriority.MEDIUM,
        },
    ]

    # Create maintenance records over the past year
    for i in range(count):
        days_ago = random.randint(0, 365)
        scheduled_date = datetime.utcnow() - timedelta(days=days_ago)

        task = random.choice(maintenance_tasks)

        # Vary status based on how old the record is
        if days_ago < 7:
            status = random.choice(
                [
                    MaintenanceStatus.SCHEDULED,
                    MaintenanceStatus.IN_PROGRESS,
                    MaintenanceStatus.COMPLETED,
                ]
            )
        elif days_ago < 30:
            status = random.choice(
                [
                    MaintenanceStatus.COMPLETED,
                    MaintenanceStatus.IN_PROGRESS,
                ]
            )
        else:
            status = MaintenanceStatus.COMPLETED

        maintenance = {
            "work_order_number": generate_work_order_number(wo_index),
            "asset_id": asset_id,
            "type": task["type"].value,
            "priority": task["priority"].value,
            "title": task["title"],
            "description": task["description"],
            "status": status.value,
            "scheduled_date": scheduled_date,
            "estimated_duration": task["duration"],
            "assigned_to": random.choice(user_ids) if user_ids else None,
            "created_at": scheduled_date - timedelta(days=random.randint(1, 14)),
            "updated_at": scheduled_date - timedelta(days=random.randint(0, 7)),
        }

        # Add execution details for completed maintenance
        if status == MaintenanceStatus.COMPLETED:
            maintenance["actual_start_time"] = scheduled_date + timedelta(
                minutes=random.randint(0, 60)
            )
            maintenance["actual_end_time"] = maintenance[
                "actual_start_time"
            ] + timedelta(
                minutes=maintenance["estimated_duration"] + random.randint(-30, 60)
            )
            maintenance["actual_duration"] = (
                maintenance["actual_end_time"] - maintenance["actual_start_time"]
            ).total_seconds() / 60
            maintenance["work_performed"] = "Maintenance work completed successfully."
            maintenance["total_cost"] = random.uniform(500000, 3000000)  # VND
            maintenance["labor_cost"] = maintenance["total_cost"] * 0.6
            maintenance["parts_cost"] = maintenance["total_cost"] * 0.4
            maintenance["completed_by"] = maintenance["assigned_to"]

        # Add in-progress details
        if status == MaintenanceStatus.IN_PROGRESS:
            maintenance["actual_start_time"] = scheduled_date + timedelta(
                minutes=random.randint(0, 60)
            )

        maintenance_data.append(maintenance)
        wo_index += 1

    # Insert maintenance records
    result = await db.maintenance_records.insert_many(maintenance_data)
    maintenance_ids = [str(id) for id in result.inserted_ids]

    logger.info(f"Created {len(maintenance_ids)} maintenance records")
    return maintenance_ids


async def seed_sensors(
    db, asset_id: str, user_ids: List[str], count: int = 3
) -> List[str]:
    """Seed IoT sensors for the asset."""
    logger.info(f"Seeding {count} sensors for asset...")

    sensors_data = []
    sensor_index = 1

    # Sensor configurations
    sensor_configs = {
        SensorType.TEMPERATURE: {
            "unit": "°C",
            "sample_rate": 300,
            "manufacturers": ["Sensirion", "Bosch"],
            "models": ["SHT30", "BME280"],
            "thresholds": {
                "min_value": -10.0,
                "max_value": 60.0,
                "critical_min": -5.0,
                "critical_max": 55.0,
            },
        },
        SensorType.POWER: {
            "unit": "kW",
            "sample_rate": 60,
            "manufacturers": ["Schneider Electric", "ABB"],
            "models": ["PM8000", "CM4000"],
            "thresholds": {
                "min_value": 0.0,
                "max_value": 50.0,
                "critical_min": 0.0,
                "critical_max": 45.0,
            },
        },
        SensorType.VIBRATION: {
            "unit": "Hz",
            "sample_rate": 60,
            "manufacturers": ["Analog Devices", "STMicroelectronics"],
            "models": ["ADXL345", "LSM6DS3"],
            "thresholds": {
                "min_value": 0.0,
                "max_value": 100.0,
                "critical_min": 0.0,
                "critical_max": 80.0,
            },
        },
    }

    connection_configs = {
        ConnectionType.WIFI: {
            "ip_prefix": "192.168.1.",
            "mac_prefix": "00:1B:44:",
        },
        ConnectionType.LORA: {
            "ip_prefix": None,
            "mac_prefix": "AA:BB:CC:",
        },
    }

    sensor_types = list(SensorType)[:count]  # Use first N sensor types

    for i, sensor_type in enumerate(sensor_types):
        config = sensor_configs.get(
            sensor_type,
            {
                "unit": "units",
                "sample_rate": 300,
                "manufacturers": ["Generic"],
                "models": ["Model-1"],
                "thresholds": {},
            },
        )

        connection_type = random.choice(list(ConnectionType))
        conn_config = connection_configs.get(
            connection_type,
            {"ip_prefix": None, "mac_prefix": "00:1A:7D:"},
        )

        # Generate IP and MAC addresses
        ip_address = None
        mac_address = None
        if conn_config["ip_prefix"]:
            ip_address = f"{conn_config['ip_prefix']}{100 + i}"
        mac_address = f"{conn_config['mac_prefix']}{random.randint(10, 99):02X}:{random.randint(10, 99):02X}:{random.randint(10, 99):02X}"

        installed_days_ago = random.randint(30, 365)
        installed_at = datetime.utcnow() - timedelta(days=installed_days_ago)

        # Status: mostly online
        status = random.choice(
            [
                SensorStatus.ONLINE,
                SensorStatus.ONLINE,
                SensorStatus.ONLINE,
                SensorStatus.OFFLINE,
            ]
        )

        # Last seen
        if status == SensorStatus.ONLINE:
            last_seen = datetime.utcnow() - timedelta(minutes=random.randint(1, 60))
        else:
            last_seen = datetime.utcnow() - timedelta(days=random.randint(1, 7))

        # Generate last reading
        base_value = {
            SensorType.TEMPERATURE: random.uniform(25.0, 35.0),
            SensorType.POWER: random.uniform(5.0, 20.0),
            SensorType.VIBRATION: random.uniform(0.0, 30.0),
        }.get(sensor_type, random.uniform(0.0, 100.0))

        last_reading = {
            "value": base_value,
            "timestamp": last_seen,
            "status": "normal" if status == SensorStatus.ONLINE else "warning",
        }

        calibration_date = installed_at + timedelta(days=random.randint(1, 30))
        calibration_due = calibration_date + timedelta(days=365)

        sensor = {
            "sensor_code": generate_sensor_code(sensor_index),
            "asset_id": asset_id,
            "sensor_type": sensor_type.value,
            "manufacturer": random.choice(config["manufacturers"]),
            "model": random.choice(config["models"]),
            "firmware_version": f"v{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "measurement_unit": config["unit"],
            "sample_rate": config["sample_rate"],
            "thresholds": config.get("thresholds", {}),
            "connection_type": connection_type.value,
            "ip_address": ip_address,
            "mac_address": mac_address,
            "gateway_id": f"GW-{random.randint(1, 10):03d}",
            "status": status.value,
            "last_seen": last_seen,
            "last_reading": last_reading,
            "calibration_date": calibration_date,
            "calibration_due": calibration_due,
            "calibration_factor": random.uniform(0.95, 1.05),
            "installed_at": installed_at,
            "installed_by": random.choice(user_ids) if user_ids else None,
            "location_description": f"Installed on traffic light asset",
            "maintenance_schedule": random.choice(["monthly", "quarterly"]),
            "last_maintenance": installed_at + timedelta(days=random.randint(30, 180)),
            "next_maintenance": datetime.utcnow()
            + timedelta(days=random.randint(1, 90)),
            "created_at": installed_at,
            "updated_at": last_seen,
            "created_by": random.choice(user_ids) if user_ids else None,
            "notes": f"Installed for monitoring {sensor_type.value}",
            "tags": [sensor_type.value, connection_type.value],
        }

        sensors_data.append(sensor)
        sensor_index += 1

    # Insert sensors
    result = await db.iot_sensors.insert_many(sensors_data)
    sensor_ids = [str(id) for id in result.inserted_ids]

    logger.info(f"Created {len(sensor_ids)} sensors")
    return sensor_ids


async def seed_incidents(
    db, asset_id: str, user_ids: List[str], count: int = 5
) -> List[str]:
    """Seed incidents for the asset."""
    logger.info(f"Seeding {count} incidents for asset...")

    incidents_data = []
    incident_index = 1

    incident_scenarios = [
        {
            "title": "Traffic light not working",
            "category": IncidentCategory.MALFUNCTION,
            "description": "Traffic signal at intersection is not functioning properly. Red light stays on continuously.",
            "severity": IncidentSeverity.HIGH,
        },
        {
            "title": "Traffic light showing wrong signal",
            "category": IncidentCategory.MALFUNCTION,
            "description": "Traffic light displaying green in multiple directions simultaneously.",
            "severity": IncidentSeverity.CRITICAL,
        },
        {
            "title": "Damaged traffic light pole",
            "category": IncidentCategory.DAMAGE,
            "description": "Traffic light pole has been damaged, possibly from vehicle collision.",
            "severity": IncidentSeverity.HIGH,
        },
        {
            "title": "Flickering traffic light",
            "category": IncidentCategory.MALFUNCTION,
            "description": "Traffic light bulbs are flickering, creating visibility issues.",
            "severity": IncidentSeverity.MEDIUM,
        },
    ]

    # Get asset location
    asset = await db.assets.find_one({"_id": ObjectId(asset_id)})
    location = asset.get("location", {}) if asset else {}
    geometry = (
        asset.get("geometry", {"type": "Point", "coordinates": [108.2022, 16.0544]})
        if asset
        else {"type": "Point", "coordinates": [108.2022, 16.0544]}
    )

    for i in range(count):
        days_ago = random.randint(0, 180)
        reported_at = datetime.utcnow() - timedelta(days=days_ago)

        scenario = random.choice(incident_scenarios)

        # Status based on age
        if days_ago < 7:
            status = random.choice(
                [
                    IncidentStatus.REPORTED,
                    IncidentStatus.ACKNOWLEDGED,
                    IncidentStatus.INVESTIGATING,
                    IncidentStatus.RESOLVED,
                ]
            )
        elif days_ago < 30:
            status = random.choice(
                [
                    IncidentStatus.RESOLVED,
                    IncidentStatus.CLOSED,
                ]
            )
        else:
            status = IncidentStatus.CLOSED

        incident = {
            "incident_number": generate_incident_number(incident_index),
            "asset_id": asset_id,
            "title": scenario["title"],
            "description": scenario["description"],
            "category": scenario["category"].value,
            "severity": scenario["severity"].value,
            "status": status.value,
            "location": {
                "geometry": geometry,
                "address": location.get("address", "123 Bach Dang Street"),
                "description": f"At traffic light intersection",
                "district": location.get("district", "Hai Chau"),
                "ward": location.get("ward", "Thach Thang"),
            },
            "reported_by": random.choice(user_ids) if user_ids else None,
            "reporter_type": random.choice(list(ReporterType)).value,
            "reported_via": random.choice(["web", "mobile", "qr_code", "phone"]),
            "reported_at": reported_at,
            "public_visible": True,
            "upvotes": random.randint(0, 20) if random.random() > 0.5 else 0,
            "created_at": reported_at,
            "updated_at": reported_at + timedelta(days=random.randint(0, 5)),
        }

        # Add assignment and resolution
        if status in [
            IncidentStatus.ACKNOWLEDGED,
            IncidentStatus.INVESTIGATING,
            IncidentStatus.RESOLVED,
            IncidentStatus.CLOSED,
        ]:
            incident["assigned_to"] = random.choice(user_ids) if user_ids else None
            incident["acknowledged_at"] = reported_at + timedelta(
                hours=random.randint(1, 24)
            )
            incident["acknowledged_by"] = incident["assigned_to"]

        if status in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
            incident["resolved_at"] = reported_at + timedelta(days=random.randint(1, 7))
            incident["resolved_by"] = incident["assigned_to"]
            incident["resolution_notes"] = "Issue has been resolved successfully."
            incident["resolution_type"] = "fixed"

        if status == IncidentStatus.CLOSED:
            incident["closed_at"] = incident["resolved_at"] + timedelta(
                days=random.randint(1, 3)
            )

        incidents_data.append(incident)
        incident_index += 1

    # Insert incidents
    result = await db.incidents.insert_many(incidents_data)
    incident_ids = [str(id) for id in result.inserted_ids]

    logger.info(f"Created {len(incident_ids)} incidents")
    return incident_ids


async def seed_alerts(
    db,
    asset_id: str,
    sensor_ids: List[str],
    incident_ids: List[str],
    maintenance_ids: List[str],
    user_ids: List[str],
    count: int = 8,
) -> List[str]:
    """Seed alerts for the asset."""
    logger.info(f"Seeding {count} alerts for asset...")

    alerts_data = []
    alert_index = 1

    alert_scenarios = [
        {
            "source_type": AlertSourceType.SENSOR,
            "type": "threshold_exceeded",
            "severity": AlertSeverity.WARNING,
            "title": "Temperature threshold exceeded",
            "message": "Sensor reading exceeds configured maximum threshold",
            "condition": "greater_than",
        },
        {
            "source_type": AlertSourceType.SENSOR,
            "type": "threshold_exceeded",
            "severity": AlertSeverity.CRITICAL,
            "title": "Critical temperature reading",
            "message": "Temperature reading is critically high",
            "condition": "greater_than",
        },
        {
            "source_type": AlertSourceType.SENSOR,
            "type": "sensor_offline",
            "severity": AlertSeverity.WARNING,
            "title": "Sensor offline",
            "message": "Sensor has not reported data for extended period",
            "condition": None,
        },
        {
            "source_type": AlertSourceType.SYSTEM,
            "type": "maintenance_due",
            "severity": AlertSeverity.INFO,
            "title": "Maintenance due",
            "message": "Scheduled maintenance is due for this asset",
            "condition": None,
        },
        {
            "source_type": AlertSourceType.SENSOR,
            "type": "power_consumption_high",
            "severity": AlertSeverity.WARNING,
            "message": "Power consumption exceeds normal operating range",
            "condition": "greater_than",
        },
    ]

    for i in range(count):
        days_ago = random.randint(0, 60)
        triggered_at = datetime.utcnow() - timedelta(days=days_ago)

        scenario = random.choice(alert_scenarios)

        sensor_id = None
        if scenario["source_type"] == AlertSourceType.SENSOR and sensor_ids:
            sensor_id = random.choice(sensor_ids)

        # Status distribution
        status_weights = [
            AlertStatus.ACTIVE,
            AlertStatus.ACTIVE,
            AlertStatus.ACKNOWLEDGED,
            AlertStatus.RESOLVED,
            AlertStatus.DISMISSED,
        ]
        status = random.choice(status_weights)

        # Generate trigger and threshold values
        trigger_value = None
        threshold_value = None
        if scenario["type"] == "threshold_exceeded":
            threshold_value = random.uniform(50.0, 100.0)
            trigger_value = threshold_value + random.uniform(5.0, 20.0)

        alert = {
            "alert_code": generate_alert_code(alert_index),
            "source_type": scenario["source_type"].value,
            "sensor_id": sensor_id,
            "asset_id": asset_id,
            "type": scenario["type"],
            "severity": scenario["severity"].value,
            "title": scenario.get("title", "Alert"),
            "message": scenario["message"],
            "trigger_value": trigger_value,
            "threshold_value": threshold_value,
            "condition": scenario["condition"],
            "status": status.value,
            "triggered_at": triggered_at,
            "created_at": triggered_at,
            "updated_at": triggered_at,
            "auto_created": scenario["source_type"] != AlertSourceType.MANUAL,
            "metadata": {
                "source": "seed_data",
                "scenario": scenario["type"],
            },
        }

        # Add acknowledgment/resolution details
        if status in [
            AlertStatus.ACKNOWLEDGED,
            AlertStatus.RESOLVED,
            AlertStatus.DISMISSED,
        ]:
            alert["acknowledged_at"] = triggered_at + timedelta(
                hours=random.randint(1, 24)
            )
            alert["acknowledged_by"] = random.choice(user_ids) if user_ids else None

        if status == AlertStatus.RESOLVED:
            alert["resolved_at"] = triggered_at + timedelta(days=random.randint(1, 7))
            alert["resolved_by"] = alert["acknowledged_by"]
            alert["resolution_notes"] = "Alert resolved successfully."

        # Link to incidents/maintenance
        if status == AlertStatus.RESOLVED and random.random() > 0.5:
            if incident_ids and random.random() > 0.5:
                alert["incident_created"] = True
                alert["incident_id"] = random.choice(incident_ids)
            elif maintenance_ids:
                alert["maintenance_created"] = True
                alert["maintenance_id"] = random.choice(maintenance_ids)

        # Add notifications
        if random.random() > 0.3:
            alert["notifications_sent"] = [
                {
                    "recipient_id": random.choice(user_ids) if user_ids else None,
                    "sent_at": triggered_at + timedelta(minutes=random.randint(1, 60)),
                    "method": random.choice(["email", "push", "sms"]),
                    "status": random.choice(["sent", "delivered"]),
                }
            ]

        alerts_data.append(alert)
        alert_index += 1

    # Insert alerts
    result = await db.alerts.insert_many(alerts_data)
    alert_ids = [str(id) for id in result.inserted_ids]

    logger.info(f"Created {len(alert_ids)} alerts")
    return alert_ids


async def get_or_create_budget(db, user_ids: List[str]) -> str:
    """Get existing budget or create one."""
    current_year = datetime.now().year
    budget = await db.budgets.find_one({"fiscal_year": current_year})

    if budget:
        return str(budget["_id"])

    # Create a budget
    start_date = datetime(current_year, 1, 1)
    end_date = datetime(current_year, 12, 31)

    total_allocated = random.uniform(500000000, 2000000000)  # 500M-2B VND
    days_elapsed = (datetime.utcnow() - start_date).days
    days_total = (end_date - start_date).days
    progress = min(days_elapsed / days_total, 1.0) if days_total > 0 else 0
    spent_amount = total_allocated * progress * random.uniform(0.6, 0.9)

    budget_data = {
        "budget_code": f"BUD-{current_year}-OPS-001",
        "fiscal_year": current_year,
        "period_type": BudgetPeriodType.ANNUAL.value,
        "start_date": start_date,
        "end_date": end_date,
        "name": f"{current_year} - Infrastructure Operations & Maintenance",
        "description": "Daily operations and routine maintenance of city infrastructure",
        "category": BudgetCategory.OPERATIONS.value,
        "total_allocated": total_allocated,
        "spent_amount": spent_amount,
        "remaining_amount": total_allocated - spent_amount,
        "currency": "VND",
        "status": BudgetStatus.APPROVED.value,
        "created_by": user_ids[0] if user_ids else None,
        "approved_by": user_ids[0] if user_ids else None,
        "approved_at": start_date - timedelta(days=30),
        "created_at": start_date - timedelta(days=60),
        "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
    }

    result = await db.budgets.insert_one(budget_data)
    return str(result.inserted_id)


async def seed_budget_transactions(
    db,
    budget_id: str,
    asset_id: str,
    maintenance_ids: List[str],
    count: int = 5,
) -> List[str]:
    """Seed budget transactions related to the asset."""
    logger.info(f"Seeding {count} budget transactions for asset...")

    transactions_data = []
    txn_index = 1

    transaction_types = [
        {
            "category": "labor",
            "descriptions": [
                "Field technician labor for routine maintenance",
                "Emergency repair crew overtime pay",
            ],
            "amount_range": (500000, 2000000),
        },
        {
            "category": "materials",
            "descriptions": [
                "LED bulbs and lighting fixtures",
                "Replacement parts for traffic signals",
            ],
            "amount_range": (1000000, 5000000),
        },
        {
            "category": "equipment",
            "descriptions": [
                "Power tools and maintenance equipment",
                "Safety gear and protective equipment",
            ],
            "amount_range": (2000000, 8000000),
        },
    ]

    for i in range(count):
        days_ago = random.randint(0, 90)
        transaction_date = datetime.utcnow() - timedelta(days=days_ago)

        txn_type = random.choice(transaction_types)
        amount = random.uniform(*txn_type["amount_range"])
        status = random.choice(["pending", "approved", "paid"])

        transaction = {
            "transaction_number": generate_transaction_number(txn_index),
            "budget_id": budget_id,
            "amount": amount,
            "currency": "VND",
            "transaction_date": transaction_date,
            "description": random.choice(txn_type["descriptions"]),
            "category": txn_type["category"],
            "maintenance_record_id": (
                random.choice(maintenance_ids)
                if maintenance_ids and random.random() > 0.3
                else None
            ),
            "asset_id": asset_id,
            "vendor": f"Vendor {random.randint(1, 10)}",
            "status": status,
            "created_at": transaction_date - timedelta(days=random.randint(1, 7)),
            "updated_at": transaction_date,
        }

        if transaction["status"] == "approved":
            transaction["approved_at"] = transaction["created_at"] + timedelta(
                days=random.randint(1, 7)
            )

        if transaction["status"] == "paid":
            transaction["approved_at"] = transaction["created_at"] + timedelta(
                days=random.randint(1, 7)
            )
            transaction["payment_date"] = transaction["approved_at"] + timedelta(
                days=random.randint(1, 14)
            )
            transaction["payment_method"] = random.choice(["cash", "transfer", "check"])

        transactions_data.append(transaction)
        txn_index += 1

    # Insert transactions
    result = await db.budget_transactions.insert_many(transactions_data)
    transaction_ids = [str(id) for id in result.inserted_ids]

    logger.info(f"Created {len(transaction_ids)} budget transactions")
    return transaction_ids


async def seed_reports(
    db, asset_id: str, user_ids: List[str], count: int = 3
) -> List[str]:
    """Seed reports related to the asset."""
    logger.info(f"Seeding {count} reports for asset...")

    reports_data = []
    report_index = 1

    report_templates = [
        {
            "type": ReportType.MAINTENANCE_SUMMARY,
            "name": "Monthly Maintenance Summary",
            "description": "Summary of all maintenance activities for the month",
            "format": ReportFormat.PDF,
            "parameters": {
                "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "asset_id": asset_id,
                "status": ["completed", "in_progress"],
            },
        },
        {
            "type": ReportType.INCIDENT_REPORT,
            "name": "Weekly Incident Report",
            "description": "Summary of incidents reported this week",
            "format": ReportFormat.PDF,
            "parameters": {
                "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "asset_id": asset_id,
                "severity": ["high", "critical"],
            },
        },
        {
            "type": ReportType.IOT_SENSOR_DATA,
            "name": "Sensor Data Analysis",
            "description": "Analysis of IoT sensor readings and trends",
            "format": ReportFormat.PDF,
            "parameters": {
                "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "asset_id": asset_id,
                "sensor_types": ["temperature", "power"],
            },
        },
    ]

    for i in range(count):
        days_ago = random.randint(0, 30)
        created_at = datetime.utcnow() - timedelta(days=days_ago)

        template = report_templates[i % len(report_templates)]

        status = random.choice(
            [
                ReportStatus.COMPLETED,
                ReportStatus.COMPLETED,
                ReportStatus.PENDING,
            ]
        )

        generated_at = None
        file_url = None
        file_size = None

        if status == ReportStatus.COMPLETED:
            generated_at = created_at + timedelta(hours=random.randint(1, 24))
            file_url = f"/reports/{generate_report_code(report_index)}.{template['format'].value}"
            file_size = random.randint(100000, 2000000)  # 100KB - 2MB

        expires_at = None
        if status == ReportStatus.COMPLETED:
            expires_at = datetime.utcnow() + timedelta(days=random.randint(30, 365))

        report = {
            "report_code": generate_report_code(report_index),
            "type": template["type"].value,
            "name": f"{template['name']} - Asset {asset_id[:8]}",
            "description": template["description"],
            "parameters": template["parameters"],
            "format": template["format"].value,
            "file_url": file_url,
            "file_size": file_size,
            "status": status.value,
            "generated_at": generated_at,
            "scheduled": False,
            "recipients": (
                [random.choice(user_ids) for _ in range(random.randint(1, 2))]
                if user_ids
                else []
            ),
            "expires_at": expires_at,
            "created_at": created_at,
            "created_by": random.choice(user_ids) if user_ids else None,
            "metadata": {
                "template": template["type"].value,
                "generated_by": "seed_script",
                "asset_id": asset_id,
            },
        }

        reports_data.append(report)
        report_index += 1

    # Insert reports
    result = await db.reports.insert_many(reports_data)
    report_ids = [str(id) for id in result.inserted_ids]

    logger.info(f"Created {len(report_ids)} reports")
    return report_ids


async def seed_single_asset(
    asset_id: Optional[str] = None,
    maintenance_count: int = 10,
    sensor_count: int = 3,
    incident_count: int = 5,
    alert_count: int = 8,
    transaction_count: int = 5,
    report_count: int = 3,
):
    """Main function to seed data for a single asset."""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    try:
        logger.info("=" * 60)
        logger.info("SEEDING SINGLE ASSET WITH FULL MOCK DATA")
        logger.info("=" * 60)
        logger.info(f"Database: {settings.DATABASE_NAME}")
        logger.info(f"MongoDB URL: {settings.MONGODB_URL}")
        logger.info("=" * 60)

        # Get or create users
        user_ids = await get_or_create_users(db)
        logger.info(f"Using {len(user_ids)} users")

        # Get or create asset
        if asset_id:
            try:
                asset = await db.assets.find_one({"_id": ObjectId(asset_id)})
                if not asset:
                    logger.error(f"Asset with ID {asset_id} not found")
                    return
                asset_id = str(asset["_id"])
                logger.info(f"Using existing asset: {asset.get('asset_code', 'N/A')}")
            except Exception as e:
                logger.error(f"Invalid asset ID: {e}")
                return
        else:
            asset_id = await get_or_create_asset(db, user_ids)

        # Seed all related data
        maintenance_ids = await seed_maintenance_history(
            db, asset_id, user_ids, count=maintenance_count
        )
        sensor_ids = await seed_sensors(db, asset_id, user_ids, count=sensor_count)
        incident_ids = await seed_incidents(
            db, asset_id, user_ids, count=incident_count
        )
        alert_ids = await seed_alerts(
            db,
            asset_id,
            sensor_ids,
            incident_ids,
            maintenance_ids,
            user_ids,
            count=alert_count,
        )
        budget_id = await get_or_create_budget(db, user_ids)
        transaction_ids = await seed_budget_transactions(
            db, budget_id, asset_id, maintenance_ids, count=transaction_count
        )
        report_ids = await seed_reports(db, asset_id, user_ids, count=report_count)

        logger.info("=" * 60)
        logger.info("SEEDING COMPLETED")
        logger.info("=" * 60)
        logger.info("Summary:")
        logger.info(f"  - Asset ID: {asset_id}")
        logger.info(f"  - Maintenance Records: {len(maintenance_ids)}")
        logger.info(f"  - Sensors: {len(sensor_ids)}")
        logger.info(f"  - Incidents: {len(incident_ids)}")
        logger.info(f"  - Alerts: {len(alert_ids)}")
        logger.info(f"  - Budget Transactions: {len(transaction_ids)}")
        logger.info(f"  - Reports: {len(report_ids)}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        raise
    finally:
        client.close()
        logger.info("Database connection closed")


async def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Seed a single asset with full mock data"
    )
    parser.add_argument(
        "--asset-id",
        type=str,
        default=None,
        help="Asset ID to seed data for (if not provided, creates a new asset)",
    )
    parser.add_argument(
        "--maintenance",
        type=int,
        default=10,
        help="Number of maintenance records to create",
    )
    parser.add_argument(
        "--sensors",
        type=int,
        default=3,
        help="Number of sensors to create",
    )
    parser.add_argument(
        "--incidents",
        type=int,
        default=5,
        help="Number of incidents to create",
    )
    parser.add_argument(
        "--alerts",
        type=int,
        default=8,
        help="Number of alerts to create",
    )
    parser.add_argument(
        "--transactions",
        type=int,
        default=5,
        help="Number of budget transactions to create",
    )
    parser.add_argument(
        "--reports",
        type=int,
        default=3,
        help="Number of reports to create",
    )

    args = parser.parse_args()

    await seed_single_asset(
        asset_id=args.asset_id,
        maintenance_count=args.maintenance,
        sensor_count=args.sensors,
        incident_count=args.incidents,
        alert_count=args.alerts,
        transaction_count=args.transactions,
        report_count=args.reports,
    )


if __name__ == "__main__":
    asyncio.run(main())
