"""
Celery task to seed sensor readings data for IoT sensors.
This generates realistic time-series data for all sensors that lack readings.
"""

import random
from datetime import datetime, timedelta
from celery import shared_task
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os

# Sensor type configurations with realistic value ranges
SENSOR_CONFIGS = {
    "temperature": {
        "min": 15.0, "max": 45.0, "unit": "°C",
        "variation": 5.0, "trend_factor": 0.1
    },
    "humidity": {
        "min": 30.0, "max": 95.0, "unit": "%",
        "variation": 10.0, "trend_factor": 0.05
    },
    "pressure": {
        "min": 0.5, "max": 6.0, "unit": "bar",
        "variation": 0.5, "trend_factor": 0.02
    },
    "vibration": {
        "min": 0.0, "max": 10.0, "unit": "mm/s",
        "variation": 2.0, "trend_factor": 0.1
    },
    "power": {
        "min": 0.0, "max": 500.0, "unit": "kW",
        "variation": 50.0, "trend_factor": 0.15
    },
    "water_level": {
        "min": 0.0, "max": 100.0, "unit": "%",
        "variation": 15.0, "trend_factor": 0.1
    },
    "flow_rate": {
        "min": 0.0, "max": 1000.0, "unit": "L/min",
        "variation": 100.0, "trend_factor": 0.1
    },
    "air_quality": {
        "min": 0.0, "max": 500.0, "unit": "AQI",
        "variation": 50.0, "trend_factor": 0.05
    },
    "noise": {
        "min": 30.0, "max": 100.0, "unit": "dB",
        "variation": 15.0, "trend_factor": 0.1
    },
    "custom": {
        "min": 0.0, "max": 100.0, "unit": "units",
        "variation": 20.0, "trend_factor": 0.1
    }
}


def get_sensor_config(sensor_type: str) -> dict:
    """Get config for sensor type, with fallback to custom."""
    sensor_type_lower = sensor_type.lower()
    for key in SENSOR_CONFIGS:
        if key in sensor_type_lower:
            return SENSOR_CONFIGS[key]
    return SENSOR_CONFIGS["custom"]


def generate_realistic_value(config: dict, prev_value: float = None, hour: int = 12) -> float:
    """Generate a realistic sensor value with time-of-day patterns and continuity."""
    base_min, base_max = config["min"], config["max"]
    variation = config["variation"]
    
    # Time-of-day factor (higher during day for temp, lower at night)
    time_factor = 0.5 + 0.5 * abs(12 - hour) / 12  # 0.5 to 1.0
    
    if prev_value is None:
        # Initial value: random within middle 60% of range
        range_size = base_max - base_min
        prev_value = base_min + range_size * 0.2 + random.random() * range_size * 0.6
    
    # Add variation with continuity (random walk)
    change = random.gauss(0, variation * 0.3)
    
    # Add some time-based trend
    trend = (time_factor - 0.75) * config["trend_factor"] * (base_max - base_min)
    
    new_value = prev_value + change + trend
    
    # Clamp to valid range
    new_value = max(base_min, min(base_max, new_value))
    
    return round(new_value, 2)


def determine_status(value: float, config: dict) -> str:
    """Determine reading status based on value."""
    range_size = config["max"] - config["min"]
    normalized = (value - config["min"]) / range_size
    
    if normalized < 0.1 or normalized > 0.9:
        return "critical"
    elif normalized < 0.2 or normalized > 0.8:
        return "warning"
    return "normal"


async def seed_readings_for_sensor(db, sensor: dict, days: int = 7, readings_per_day: int = 96):
    """Generate readings for a single sensor."""
    config = get_sensor_config(sensor.get("sensor_type", "custom"))
    sensor_id = str(sensor["_id"])
    asset_id = sensor.get("asset_id", "")
    unit = sensor.get("measurement_unit") or config["unit"]
    
    # Check existing readings count
    existing_count = await db.sensor_readings.count_documents({"sensor_id": sensor_id})
    if existing_count > 100:
        return 0  # Skip if already has significant data
    
    readings = []
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    # Calculate interval between readings
    total_readings = days * readings_per_day
    interval_minutes = (days * 24 * 60) / total_readings
    
    current_time = start_time
    prev_value = None
    
    for i in range(total_readings):
        hour = current_time.hour
        value = generate_realistic_value(config, prev_value, hour)
        prev_value = value
        
        # Add some randomness to timestamp (±2 minutes)
        timestamp = current_time + timedelta(minutes=random.uniform(-2, 2))
        
        reading = {
            "sensor_id": sensor_id,
            "asset_id": asset_id,
            "timestamp": timestamp,
            "value": value,
            "unit": unit,
            "quality": random.choices(["good", "suspect"], weights=[0.95, 0.05])[0],
            "quality_flags": [],
            "status": determine_status(value, config),
            "threshold_exceeded": value < config["min"] * 1.1 or value > config["max"] * 0.9,
            "metadata": {
                "source": "celery_seed_task",
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        readings.append(reading)
        
        current_time += timedelta(minutes=interval_minutes)
    
    # Bulk insert
    if readings:
        await db.sensor_readings.insert_many(readings)
        
        # Update sensor with last reading info
        last_reading = readings[-1]
        await db.iot_sensors.update_one(
            {"_id": sensor["_id"]},
            {
                "$set": {
                    "last_seen": last_reading["timestamp"],
                    "last_reading": {
                        "value": last_reading["value"],
                        "timestamp": last_reading["timestamp"].isoformat(),
                        "unit": last_reading["unit"]
                    },
                    "status": "online",
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    return len(readings)


async def run_seed_readings(days: int = 7, readings_per_day: int = 96):
    """Main async function to seed readings for all sensors."""
    mongo_url = os.getenv("MONGODB_URL", "mongodb://mongo:27017")
    db_name = os.getenv("DATABASE_NAME", "gis_db")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Get all sensors
        sensors = await db.iot_sensors.find({}).to_list(length=1000)
        
        total_readings = 0
        sensors_updated = 0
        
        for sensor in sensors:
            try:
                count = await seed_readings_for_sensor(db, sensor, days, readings_per_day)
                if count > 0:
                    total_readings += count
                    sensors_updated += 1
                    print(f"Seeded {count} readings for sensor {sensor.get('sensor_code', sensor['_id'])}")
            except Exception as e:
                print(f"Error seeding sensor {sensor.get('sensor_code', sensor['_id'])}: {e}")
        
        # Create index for efficient queries
        await db.sensor_readings.create_index([("sensor_id", 1), ("timestamp", -1)])
        await db.sensor_readings.create_index([("asset_id", 1), ("timestamp", -1)])
        
        return {
            "sensors_processed": len(sensors),
            "sensors_updated": sensors_updated,
            "total_readings_created": total_readings,
            "days": days,
            "readings_per_day": readings_per_day
        }
    finally:
        client.close()


@shared_task(name="seed_sensor_readings")
def seed_sensor_readings(days: int = 7, readings_per_day: int = 96):
    """
    Celery task to seed sensor readings for all IoT sensors.
    
    Args:
        days: Number of days of historical data to generate (default: 7)
        readings_per_day: Number of readings per day per sensor (default: 96 = every 15 min)
    
    Returns:
        dict with seeding statistics
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(run_seed_readings(days, readings_per_day))
        return result
    finally:
        loop.close()


@shared_task(name="seed_sensor_readings_continuous")
def seed_sensor_readings_continuous():
    """
    Celery task for continuous sensor data generation.
    Generates 1 hour of data - run every hour via celery beat.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Generate last 1 hour with 4 readings (every 15 min)
        result = loop.run_until_complete(run_seed_readings(days=1/24, readings_per_day=4))
        return result
    finally:
        loop.close()
