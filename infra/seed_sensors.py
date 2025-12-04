#!/usr/bin/env python3
"""
Seed IoT sensor data for OpenInfra.
Creates sensors and fake readings for assets based on their type.
"""

import asyncio
import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# MongoDB connection
MONGODB_URL = "mongodb://mongo:27017"
DATABASE_NAME = "gis_db"

# Sensor configurations by asset type
SENSOR_CONFIGS = {
    "cong_thoat_nuoc": [  # Drainage - water level, flow rate sensors
        {
            "sensor_type": "custom",
            "measurement_unit": "cm",
            "name_prefix": "WATER_LEVEL",
            "sample_rate": 300,  # 5 minutes
            "value_range": (0, 150),  # cm water level
            "thresholds": {
                "min_value": 0,
                "max_value": 120,
                "warning_max": 80,
                "critical_max": 100
            }
        },
        {
            "sensor_type": "custom",
            "measurement_unit": "L/s",
            "name_prefix": "FLOW_RATE",
            "sample_rate": 60,  # 1 minute
            "value_range": (0, 50),  # L/s
            "thresholds": {
                "min_value": 0,
                "max_value": 100,
                "warning_max": 70,
                "critical_max": 90
            }
        }
    ],
    "tram_dien": [  # Power station - voltage, power, temperature
        {
            "sensor_type": "power",
            "measurement_unit": "kW",
            "name_prefix": "POWER_OUTPUT",
            "sample_rate": 60,
            "value_range": (50, 500),
            "thresholds": {
                "min_value": 0,
                "max_value": 600,
                "warning_max": 450,
                "critical_max": 550
            }
        },
        {
            "sensor_type": "custom",
            "measurement_unit": "V",
            "name_prefix": "VOLTAGE",
            "sample_rate": 30,
            "value_range": (210, 240),
            "thresholds": {
                "min_value": 200,
                "max_value": 250,
                "warning_min": 210,
                "warning_max": 240,
                "critical_min": 200,
                "critical_max": 250
            }
        },
        {
            "sensor_type": "temperature",
            "measurement_unit": "°C",
            "name_prefix": "TRANSFORMER_TEMP",
            "sample_rate": 120,
            "value_range": (30, 70),
            "thresholds": {
                "min_value": 0,
                "max_value": 100,
                "warning_max": 65,
                "critical_max": 80
            }
        }
    ],
    "tram_sac": [  # Charging station - power, voltage, current
        {
            "sensor_type": "power",
            "measurement_unit": "kW",
            "name_prefix": "CHARGE_POWER",
            "sample_rate": 60,
            "value_range": (0, 150),  # EV charger power
            "thresholds": {
                "min_value": 0,
                "max_value": 200
            }
        },
        {
            "sensor_type": "custom",
            "measurement_unit": "A",
            "name_prefix": "CURRENT",
            "sample_rate": 30,
            "value_range": (0, 400),
            "thresholds": {
                "min_value": 0,
                "max_value": 500,
                "warning_max": 400,
                "critical_max": 450
            }
        }
    ],
    "tru_chua_chay": [  # Fire hydrant - water pressure
        {
            "sensor_type": "pressure",
            "measurement_unit": "bar",
            "name_prefix": "WATER_PRESSURE",
            "sample_rate": 600,  # 10 minutes
            "value_range": (2, 6),
            "thresholds": {
                "min_value": 2,
                "max_value": 8,
                "warning_min": 2.5,
                "critical_min": 2
            }
        }
    ],
    "den_duong": [  # Street light - power consumption, light level
        {
            "sensor_type": "power",
            "measurement_unit": "W",
            "name_prefix": "POWER_CONSUMPTION",
            "sample_rate": 300,
            "value_range": (0, 250),
            "thresholds": {
                "min_value": 0,
                "max_value": 300
            }
        }
    ]
}


async def seed_sensors():
    """Create sensors and readings for assets."""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    # Get assets that can have sensors
    asset_types = list(SENSOR_CONFIGS.keys())
    assets = await db.assets.find({"feature_code": {"$in": asset_types}}).to_list(1000)
    
    print(f"Found {len(assets)} assets for sensor creation")
    
    sensors_created = 0
    readings_created = 0
    
    for asset in assets:
        asset_id = str(asset["_id"])
        feature_code = asset.get("feature_code")
        
        if feature_code not in SENSOR_CONFIGS:
            continue
        
        sensor_configs = SENSOR_CONFIGS[feature_code]
        
        # Create sensors for this asset
        for config in sensor_configs:
            sensor_code = f"{config['name_prefix']}_{asset_id[-6:]}"
            
            # Check if sensor already exists
            existing = await db.iot_sensors.find_one({"sensor_code": sensor_code})
            if existing:
                print(f"Sensor {sensor_code} already exists, skipping...")
                sensor_id = str(existing["_id"])
            else:
                sensor = {
                    "_id": ObjectId(),
                    "sensor_code": sensor_code,
                    "asset_id": asset_id,
                    "sensor_type": config["sensor_type"],
                    "manufacturer": random.choice(["Siemens", "ABB", "Schneider", "Honeywell"]),
                    "model": f"Model-{random.randint(100, 999)}",
                    "firmware_version": f"v{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                    "measurement_unit": config["measurement_unit"],
                    "sample_rate": config["sample_rate"],
                    "thresholds": config.get("thresholds"),
                    "connection_type": random.choice(["wifi", "lora", "cellular"]),
                    "status": random.choice(["online", "online", "online", "offline"]),  # 75% online
                    "last_seen": datetime.utcnow() - timedelta(minutes=random.randint(0, 60)),
                    "installed_at": datetime.utcnow() - timedelta(days=random.randint(30, 365)),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "tags": [feature_code, config["sensor_type"]]
                }
                
                await db.iot_sensors.insert_one(sensor)
                sensor_id = str(sensor["_id"])
                sensors_created += 1
                print(f"Created sensor: {sensor_code}")
            
            # Generate readings for last 24 hours
            readings = []
            now = datetime.utcnow()
            
            for hours_ago in range(24):
                for minute in range(0, 60, config["sample_rate"] // 60 or 1):
                    timestamp = now - timedelta(hours=hours_ago, minutes=minute)
                    
                    # Generate realistic value with some variation
                    min_val, max_val = config["value_range"]
                    base_value = random.uniform(min_val, max_val)
                    
                    # Add time-based patterns (e.g., lower values at night)
                    hour = timestamp.hour
                    if feature_code == "den_duong":
                        # Street lights higher at night
                        if 6 <= hour <= 18:
                            base_value *= 0.1  # Off during day
                    elif feature_code in ["tram_dien", "tram_sac"]:
                        # Higher power during day
                        if 9 <= hour <= 21:
                            base_value *= 1.3
                    
                    # Clamp to range
                    value = max(min_val, min(max_val, base_value))
                    
                    # Determine status based on thresholds
                    status = "normal"
                    threshold_exceeded = False
                    thresholds = config.get("thresholds", {})
                    
                    if thresholds:
                        if thresholds.get("critical_max") and value >= thresholds["critical_max"]:
                            status = "critical"
                            threshold_exceeded = True
                        elif thresholds.get("warning_max") and value >= thresholds["warning_max"]:
                            status = "warning"
                        elif thresholds.get("critical_min") and value <= thresholds["critical_min"]:
                            status = "critical"
                            threshold_exceeded = True
                        elif thresholds.get("warning_min") and value <= thresholds["warning_min"]:
                            status = "warning"
                    
                    reading = {
                        "_id": ObjectId(),
                        "sensor_id": sensor_id,
                        "asset_id": asset_id,
                        "timestamp": timestamp,
                        "value": round(value, 2),
                        "unit": config["measurement_unit"],
                        "quality": "good",
                        "quality_flags": [],
                        "status": status,
                        "threshold_exceeded": threshold_exceeded,
                        "metadata": {}
                    }
                    readings.append(reading)
            
            # Insert readings in batch
            if readings:
                # Clear old readings for this sensor (optional - keep for history)
                # await db.sensor_readings.delete_many({"sensor_id": sensor_id})
                
                await db.sensor_readings.insert_many(readings)
                readings_created += len(readings)
                print(f"  Created {len(readings)} readings for {sensor_code}")
    
    print(f"\n=== Summary ===")
    print(f"Sensors created: {sensors_created}")
    print(f"Readings created: {readings_created}")
    
    # Create indexes
    await db.iot_sensors.create_index("sensor_code", unique=True)
    await db.iot_sensors.create_index("asset_id")
    await db.iot_sensors.create_index("status")
    await db.sensor_readings.create_index([("sensor_id", 1), ("timestamp", -1)])
    await db.sensor_readings.create_index([("asset_id", 1), ("timestamp", -1)])
    await db.sensor_readings.create_index("timestamp")
    
    print("Indexes created!")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_sensors())
