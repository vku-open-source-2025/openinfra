#!/usr/bin/env python3
"""
Seed alerts for rain accumulation risk exceeding thresholds.

This script creates alerts specifically for rain accumulation scenarios
where the accumulated rainfall exceeds safe thresholds, indicating potential
flooding or water accumulation risks.

Usage:
    python scripts/seed_rain_accumulation_alerts.py [--count 10] [--asset-id ASSET_ID]
    python scripts/seed_rain_accumulation_alerts.py --count 20 --clear-existing
"""

import asyncio
import sys
import os
import random
import argparse
from datetime import datetime, timedelta
from typing import List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bson import ObjectId
from app.core.logging import setup_logging
from app.domain.models.alert import (
    AlertSeverity,
    AlertStatus,
    AlertSourceType,
)
from app.infrastructure.database.mongodb import db, get_database

logger = setup_logging()


def generate_alert_code(index: int, timestamp: Optional[datetime] = None) -> str:
    """Generate unique alert code with timestamp to avoid duplicates."""
    if timestamp is None:
        timestamp = datetime.utcnow()
    year = timestamp.year
    # Use timestamp components to ensure uniqueness
    timestamp_str = timestamp.strftime("%m%d%H%M%S")
    return f"ALT-RAIN-{year}-{timestamp_str}-{index:03d}"


async def find_rainfall_sensors(database, asset_id: Optional[str] = None) -> List[dict]:
    """Find rainfall sensors in the database."""
    query = {"sensor_type": "rainfall"}
    if asset_id:
        query["asset_id"] = asset_id

    sensors = []
    async for sensor in database["iot_sensors"].find(query):
        sensors.append(
            {
                "id": str(sensor["_id"]),
                "sensor_code": sensor.get("sensor_code", "UNKNOWN"),
                "asset_id": sensor.get("asset_id"),
            }
        )
    return sensors


async def find_assets_with_rainfall_sensors(database) -> List[str]:
    """Find asset IDs that have rainfall sensors."""
    asset_ids = set()
    async for sensor in database["iot_sensors"].find({"sensor_type": "rainfall"}):
        if sensor.get("asset_id"):
            asset_ids.add(sensor["asset_id"])
    return list(asset_ids)


async def seed_rain_accumulation_alerts(
    database,
    count: int = 10,
    asset_id: Optional[str] = None,
    clear_existing: bool = False,
) -> List[str]:
    """
    Seed alerts for rain accumulation risk exceeding thresholds.

    Args:
        database: MongoDB database instance
        count: Number of alerts to create
        asset_id: Optional asset ID to filter sensors
        clear_existing: Whether to clear existing rain accumulation alerts

    Returns:
        List of created alert IDs
    """
    logger.info(f"Seeding {count} rain accumulation risk alerts...")

    # Clear existing rain accumulation alerts if requested
    if clear_existing:
        result = await database["alerts"].delete_many(
            {
                "type": {"$in": ["rain_accumulation_risk", "threshold_exceeded"]},
                "metadata.source": "rain_accumulation_seed",
            }
        )
        logger.info(f"Cleared {result.deleted_count} existing rain accumulation alerts")

    # Find rainfall sensors
    sensors = await find_rainfall_sensors(database, asset_id)
    if not sensors:
        logger.warning(
            "No rainfall sensors found. Creating alerts without sensor association."
        )
        # Use asset IDs if available
        asset_ids = await find_assets_with_rainfall_sensors(database)
        if not asset_ids and asset_id:
            asset_ids = [asset_id]
    else:
        asset_ids = list(set(s["asset_id"] for s in sensors if s.get("asset_id")))

    if not asset_ids:
        logger.warning(
            "No assets found. Alerts will be created without asset association."
        )
        asset_ids = [None]

    # Alert scenarios for rain accumulation risk
    scenarios = [
        {
            "severity": AlertSeverity.WARNING,
            "threshold_mm": 50.0,
            "title": "Tích tụ mưa đang tiến gần ngưỡng cảnh báo",
            "message_template": "Tích tụ mưa đã đạt {value:.1f} mm, đang tiến gần ngưỡng cảnh báo {threshold:.1f} mm. Theo dõi chặt chẽ để phát hiện nguy cơ tích tụ nước.",
        },
        {
            "severity": AlertSeverity.WARNING,
            "threshold_mm": 100.0,
            "title": "Tích tụ mưa vượt quá ngưỡng cảnh báo",
            "message_template": "Tích tụ mưa đã vượt quá ngưỡng cảnh báo: {value:.1f} mm (ngưỡng: {threshold:.1f} mm). Nguy cơ tích tụ nước đang tăng cao.",
        },
        {
            "severity": AlertSeverity.CRITICAL,
            "threshold_mm": 150.0,
            "title": "Tích tụ mưa nghiêm trọng - nguy cơ lũ lụt",
            "message_template": "NGHIÊM TRỌNG: Tích tụ mưa đã đạt {value:.1f} mm, vượt quá đáng kể ngưỡng an toàn {threshold:.1f} mm. Nguy cơ cao về lũ lụt và tích tụ nước.",
        },
        {
            "severity": AlertSeverity.CRITICAL,
            "threshold_mm": 200.0,
            "title": "Tích tụ mưa khẩn cấp - cần hành động ngay lập tức",
            "message_template": "KHẨN CẤP: Tích tụ mưa ở mức {value:.1f} mm vượt xa ngưỡng nghiêm trọng {threshold:.1f} mm. Cần hành động ngay lập tức để ngăn chặn lũ lụt.",
        },
        {
            "severity": AlertSeverity.EMERGENCY,
            "threshold_mm": 300.0,
            "title": "Tích tụ mưa cực đoan - tình trạng khẩn cấp",
            "message_template": "KHẨN CẤP CỰC ĐỘ: Tích tụ mưa đã đạt {value:.1f} mm, vượt xa ngưỡng khẩn cấp {threshold:.1f} mm. Nguy cơ lũ lụt nghiêm trọng - sơ tán nếu cần thiết.",
        },
    ]

    alerts_data = []
    alert_index = 1

    # Get user IDs for acknowledgment/resolution
    user_ids = []
    async for user in database["users"].find({}).limit(10):
        user_ids.append(str(user["_id"]))

    for i in range(count):
        # Select a scenario
        scenario = random.choice(scenarios)

        # Select asset and sensor
        selected_asset_id = random.choice(asset_ids) if asset_ids else None
        selected_sensor = None
        if sensors:
            # Try to find sensor for selected asset
            asset_sensors = [
                s for s in sensors if s.get("asset_id") == selected_asset_id
            ]
            if asset_sensors:
                selected_sensor = random.choice(asset_sensors)
            else:
                selected_sensor = random.choice(sensors)

        # Generate realistic values
        threshold_value = scenario["threshold_mm"]
        # Trigger value should exceed threshold
        trigger_value = threshold_value + random.uniform(10.0, 100.0)

        # For emergency scenarios, make the excess more dramatic
        if scenario["severity"] == AlertSeverity.EMERGENCY:
            trigger_value = threshold_value + random.uniform(50.0, 200.0)
        elif scenario["severity"] == AlertSeverity.CRITICAL:
            trigger_value = threshold_value + random.uniform(20.0, 150.0)

        # Generate timestamp (within last 30 days)
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        triggered_at = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)

        # All alerts will be ACTIVE status
        status = AlertStatus.ACTIVE

        # Generate alert message
        message = scenario["message_template"].format(
            value=trigger_value,
            threshold=threshold_value,
        )

        # Generate unique alert code using current timestamp to avoid duplicates
        alert = {
            "alert_code": generate_alert_code(alert_index, datetime.utcnow()),
            "source_type": AlertSourceType.SENSOR.value,
            "sensor_id": selected_sensor["id"] if selected_sensor else None,
            "asset_id": selected_asset_id,
            "type": "rain_accumulation_risk",
            "severity": scenario["severity"].value,
            "title": scenario["title"],
            "message": message,
            "trigger_value": round(trigger_value, 2),
            "threshold_value": round(threshold_value, 2),
            "condition": "greater_than",
            "status": status.value,
            "triggered_at": triggered_at,
            "created_at": triggered_at,
            "updated_at": triggered_at,
            "auto_created": True,
            "metadata": {
                "source": "rain_accumulation_seed",
                "scenario": "rain_accumulation_risk",
                "accumulation_mm": round(trigger_value, 2),
                "threshold_mm": round(threshold_value, 2),
                "excess_mm": round(trigger_value - threshold_value, 2),
                "sensor_code": (
                    selected_sensor["sensor_code"] if selected_sensor else None
                ),
            },
        }

        # All alerts are ACTIVE, so no acknowledgment/resolution details

        # Add notifications for some alerts
        if random.random() > 0.4 and user_ids:
            alert["notifications_sent"] = [
                {
                    "recipient_id": random.choice(user_ids),
                    "sent_at": triggered_at + timedelta(minutes=random.randint(1, 60)),
                    "method": random.choice(["email", "push", "sms"]),
                    "status": random.choice(["sent", "delivered", "read"]),
                }
            ]

        alerts_data.append(alert)
        alert_index += 1

    # Insert alerts
    if alerts_data:
        result = await database["alerts"].insert_many(alerts_data)
        alert_ids = [str(id) for id in result.inserted_ids]
        logger.info(f"Created {len(alert_ids)} rain accumulation risk alerts")
        return alert_ids
    else:
        logger.warning("No alerts created")
        return []


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Seed alerts for rain accumulation risk exceeding thresholds"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of alerts to create (default: 10)",
    )
    parser.add_argument(
        "--asset-id",
        type=str,
        default=None,
        help="Optional asset ID to filter sensors",
    )
    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Clear existing rain accumulation alerts before seeding",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Rain Accumulation Risk Alert Seeding")
    print("=" * 70)
    print(f"Count: {args.count}")
    print(f"Asset ID: {args.asset_id or 'All assets'}")
    print(f"Clear existing: {args.clear_existing}")
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
    print()

    # Seed alerts
    alert_ids = await seed_rain_accumulation_alerts(
        database,
        count=args.count,
        asset_id=args.asset_id,
        clear_existing=args.clear_existing,
    )

    print()
    print("=" * 70)
    print(f"Seeding complete! Created {len(alert_ids)} alerts")
    print("=" * 70)

    # Show summary
    if alert_ids:
        # Count by severity
        severity_counts = {}
        async for alert in database["alerts"].find(
            {"_id": {"$in": [ObjectId(id) for id in alert_ids]}}
        ):
            severity = alert.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        print("\nAlert Summary:")
        print(f"  Total alerts: {len(alert_ids)}")
        for severity, count in sorted(severity_counts.items()):
            print(f"  {severity}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
