"""
Seed script for IoT sensor data
Creates sensors for cong_thoat_nuoc (drainage) assets and generates fake historical data

Usage:
    python seed_iot_data.py
    
Environment:
    MONGODB_URL - MongoDB connection string (default: mongodb://localhost:27017)
"""
import asyncio
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "openinfra")

# Real sensor asset (the one with actual ESP8266)
REAL_SENSOR_ASSET_ID = "69298e9e3127bed87ace1a93"

# Drainage feature codes
DRAINAGE_FEATURE_CODES = ["cong_thoat_nuoc"]


async def get_database():
    """Get MongoDB connection"""
    client = AsyncIOMotorClient(MONGODB_URL)
    return client[MONGODB_DB]


async def get_drainage_assets(db):
    """Get all drainage assets"""
    cursor = db["assets"].find({
        "feature_code": {"$in": DRAINAGE_FEATURE_CODES}
    })
    return await cursor.to_list(length=1000)  # Get all drainage assets


def generate_sensor_id(index: int, is_real: bool = False) -> str:
    """Generate sensor ID"""
    if is_real:
        return "drainage-sensor-001"  # Real sensor
    return f"drainage-sensor-sim-{index:03d}"


def generate_sensor_config():
    """Generate default sensor configuration"""
    return {
        "thresholds": {
            "min": 0,
            "max": 5.0,           # Warning at 5m
            "critical_min": -0.5,
            "critical_max": 6.0   # Critical at 6m
        },
        "sampling_interval": 60   # 60 seconds
    }


def generate_reading(base_level: float = 1.0, variance: float = 0.5) -> dict:
    """Generate a realistic sensor reading"""
    # Simulate water level with some variation
    water_level = base_level + random.uniform(-variance, variance)
    water_level = max(0, min(water_level, 10))  # Clamp to 0-10m
    
    # Simulate flow rate (correlates somewhat with water level)
    flow_rate = (water_level * 0.5) + random.uniform(0, 1)
    
    return {
        "water_level": round(water_level, 3),
        "flow_rate": round(flow_rate, 3)
    }


def generate_historical_readings(
    sensor_id: str,
    asset_id: str,
    hours: int = 24,
    interval_minutes: int = 5
) -> list:
    """Generate historical sensor readings"""
    readings = []
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    current_time = start_time
    
    # Simulate a pattern: lower levels at night, higher during day
    # Also add some rain events (higher water levels)
    rain_events = [
        (random.randint(0, hours), random.randint(2, 5))  # (hour, duration)
        for _ in range(random.randint(0, 3))
    ]
    
    base_level = random.uniform(0.5, 1.5)
    
    while current_time <= end_time:
        hour = current_time.hour
        hours_elapsed = (current_time - start_time).total_seconds() / 3600
        
        # Time-based variation
        if 6 <= hour <= 9 or 17 <= hour <= 20:  # Rush hours
            level_modifier = 0.5
        elif 0 <= hour <= 5:  # Night
            level_modifier = -0.3
        else:
            level_modifier = 0.1
        
        # Check for rain events
        for rain_hour, rain_duration in rain_events:
            if rain_hour <= hours_elapsed <= rain_hour + rain_duration:
                level_modifier += random.uniform(1, 2)
        
        reading_data = generate_reading(base_level + level_modifier)
        
        reading = {
            "sensor_id": sensor_id,
            "asset_id": asset_id,
            "timestamp": current_time,
            "readings": reading_data,
            "battery": max(20, 100 - int(hours_elapsed * 0.5)),  # Slowly depleting battery
            "rssi": random.randint(-80, -50),
            "metadata": {
                "simulated": True,
                "firmware_version": "1.0.0"
            }
        }
        
        readings.append(reading)
        current_time += timedelta(minutes=interval_minutes)
    
    return readings


async def seed_sensors(db, assets):
    """Create sensors for 60% of assets (40% will have no IoT)"""
    sensors = []
    
    # Shuffle assets randomly then take 60%
    import random
    shuffled = assets.copy()
    random.shuffle(shuffled)
    
    num_with_sensors = int(len(assets) * 0.6)
    assets_with_sensors = shuffled[:num_with_sensors]
    
    print(f"Creating sensors for {num_with_sensors} assets (60%), {len(assets) - num_with_sensors} assets will have no IoT (40%)")
    
    for i, asset in enumerate(assets_with_sensors):
        asset_id = str(asset["_id"])
        is_real = asset_id == REAL_SENSOR_ASSET_ID
        
        sensor = {
            "sensor_id": generate_sensor_id(i + 1, is_real),
            "asset_id": asset_id,
            "sensor_type": "water_level",
            "status": "active",
            "config": generate_sensor_config(),
            "location": asset.get("geometry"),
            "created_at": datetime.utcnow() - timedelta(days=30),
            "last_seen": datetime.utcnow() - timedelta(minutes=random.randint(1, 60)),
            "metadata": {
                "is_real_sensor": is_real,
                "model": "ESP8266-WL-01" if is_real else "simulated",
                "installed_by": "VKU.OneLove",
                "notes": "Real sensor with ESP8266" if is_real else "Simulated sensor for demo"
            }
        }
        
        sensors.append(sensor)
    
    # Clear existing sensors
    await db["sensors"].delete_many({})
    
    # Insert new sensors
    if sensors:
        result = await db["sensors"].insert_many(sensors)
        print(f"Created {len(result.inserted_ids)} sensors")
    
    return sensors


async def seed_readings(db, sensors, hours: int = 48):
    """Generate historical readings for all sensors"""
    # Clear existing readings
    await db["sensor_readings"].delete_many({})
    
    total_readings = 0
    
    for sensor in sensors:
        readings = generate_historical_readings(
            sensor["sensor_id"],
            sensor["asset_id"],
            hours=hours,
            interval_minutes=5
        )
        
        if readings:
            await db["sensor_readings"].insert_many(readings)
            total_readings += len(readings)
            print(f"  - {sensor['sensor_id']}: {len(readings)} readings")
    
    print(f"Created {total_readings} total readings")


async def seed_alerts(db, sensors):
    """Generate some sample alerts"""
    alerts = []
    
    for sensor in sensors[:3]:  # Only create alerts for first 3 sensors
        # Create a warning alert
        if random.random() > 0.5:
            alerts.append({
                "sensor_id": sensor["sensor_id"],
                "asset_id": sensor["asset_id"],
                "alert_type": "threshold_exceeded",
                "severity": "warning",
                "message": f"Water level exceeded 5m threshold",
                "value": round(random.uniform(5.1, 5.5), 2),
                "threshold": 5.0,
                "created_at": datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
                "acknowledged": random.random() > 0.3
            })
        
        # Create a low battery alert
        if random.random() > 0.7:
            alerts.append({
                "sensor_id": sensor["sensor_id"],
                "asset_id": sensor["asset_id"],
                "alert_type": "low_battery",
                "severity": "warning",
                "message": "Low battery: 15%",
                "value": 15,
                "threshold": 20,
                "created_at": datetime.utcnow() - timedelta(hours=random.randint(1, 12)),
                "acknowledged": False
            })
    
    # Clear existing alerts
    await db["alerts"].delete_many({})
    
    if alerts:
        await db["alerts"].insert_many(alerts)
        print(f"Created {len(alerts)} alerts")


async def create_indexes(db):
    """Create indexes for efficient queries"""
    # Sensors indexes
    await db["sensors"].create_index("sensor_id", unique=True)
    await db["sensors"].create_index("asset_id")
    await db["sensors"].create_index("status")
    
    # Readings indexes
    await db["sensor_readings"].create_index("sensor_id")
    await db["sensor_readings"].create_index("asset_id")
    await db["sensor_readings"].create_index("timestamp")
    await db["sensor_readings"].create_index([("sensor_id", 1), ("timestamp", -1)])
    
    # Alerts indexes
    await db["alerts"].create_index("sensor_id")
    await db["alerts"].create_index("asset_id")
    await db["alerts"].create_index("severity")
    await db["alerts"].create_index("acknowledged")
    await db["alerts"].create_index("created_at")
    
    print("Created indexes")


async def main():
    print("=" * 50)
    print("OpenInfra IoT Data Seeding")
    print("=" * 50)
    
    print(f"\nConnecting to MongoDB: {MONGODB_URL}")
    db = await get_database()
    
    # Get drainage assets
    print("\nFetching drainage assets...")
    assets = await get_drainage_assets(db)
    print(f"Found {len(assets)} drainage assets")
    
    if not assets:
        print("No drainage assets found! Please seed asset data first.")
        return
    
    # Check for the specific real sensor asset
    real_asset_found = any(str(a["_id"]) == REAL_SENSOR_ASSET_ID for a in assets)
    if not real_asset_found:
        print(f"\nWarning: Real sensor asset {REAL_SENSOR_ASSET_ID} not found in database")
    
    # Seed data
    print("\nCreating sensors...")
    sensors = await seed_sensors(db, assets)
    
    print("\nGenerating readings (48 hours of data)...")
    await seed_readings(db, sensors, hours=48)
    
    print("\nCreating sample alerts...")
    await seed_alerts(db, sensors)
    
    print("\nCreating indexes...")
    await create_indexes(db)
    
    print("\n" + "=" * 50)
    print("IoT data seeding complete!")
    print("=" * 50)
    
    # Summary
    print(f"\nSummary:")
    print(f"  - Sensors: {await db['sensors'].count_documents({})}")
    print(f"  - Readings: {await db['sensor_readings'].count_documents({})}")
    print(f"  - Alerts: {await db['alerts'].count_documents({})}")
    
    if real_asset_found:
        real_sensor = await db["sensors"].find_one({"asset_id": REAL_SENSOR_ASSET_ID})
        print(f"\n  Real sensor ID: {real_sensor['sensor_id']}")
        print(f"  Asset ID: {REAL_SENSOR_ASSET_ID}")


if __name__ == "__main__":
    asyncio.run(main())
