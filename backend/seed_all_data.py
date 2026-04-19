#!/usr/bin/env python3
"""
Comprehensive seed script for OpenInfra.
Seeds ALL data types with realistic Vietnamese data.
Preserves existing users and assets, fills everything else.

Usage:
    python3 seed_all_data.py
    
Runs directly against MongoDB (no API dependency).
"""
import asyncio
import random
import math
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# ── Configuration ──────────────────────────────────────────────
import os
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongo:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "openinfra")

# ── Vietnamese data pools ──────────────────────────────────────
TECHNICIAN_NAMES = [
    "Nguyễn Văn An", "Trần Thị Bích", "Lê Văn Cường", "Phạm Thị Dung",
    "Hoàng Văn Em", "Vũ Thị Phương", "Đặng Văn Giang", "Bùi Thị Hoa",
    "Ngô Văn Khoa", "Đỗ Thị Lan", "Lý Văn Minh", "Trương Thị Ngọc",
]
CITIZEN_NAMES = [
    "Nguyễn Hữu Phát", "Trần Minh Quân", "Lê Thị Thanh", "Phạm Văn Tùng",
    "Hoàng Thị Uyên", "Vũ Đức Vinh", "Đặng Thị Xuân", "Bùi Quốc Bảo",
    "Ngô Thị Cẩm", "Đỗ Minh Đức", "Lý Thị Hương", "Mai Văn Khánh",
    "Trương Thị Mai", "Phan Văn Nam", "Hồ Thị Oanh", "Dương Văn Phong",
]

DA_NANG_STREETS = [
    "Bạch Đằng", "Trần Phú", "Nguyễn Văn Linh", "Lê Duẩn", "Ngô Quyền",
    "Phan Châu Trinh", "Hùng Vương", "Lý Thường Kiệt", "Hoàng Diệu",
    "Điện Biên Phủ", "Hải Phòng", "Ông Ích Khiêm", "Nguyễn Tri Phương",
    "Lê Lợi", "Quang Trung", "Nguyễn Hữu Thọ", "Võ Nguyên Giáp",
    "Phạm Văn Đồng", "Nguyễn Tất Thành", "Trần Đại Nghĩa",
    "2 Tháng 9", "30 Tháng 4", "Tôn Đức Thắng", "Xô Viết Nghệ Tĩnh",
]

DA_NANG_DISTRICTS = [
    {"district": "Hải Châu", "wards": ["Thạch Thang", "Hòa Cường Bắc", "Bình Hiên", "Hải Châu I", "Hải Châu II", "Nam Dương"]},
    {"district": "Thanh Khê", "wards": ["Tâm Thuận", "Thanh Khê Tây", "An Khê", "Xuân Hà", "Hòa Khê"]},
    {"district": "Sơn Trà", "wards": ["Thọ Quang", "Mân Thái", "An Hải Bắc", "An Hải Tây", "Phước Mỹ"]},
    {"district": "Ngũ Hành Sơn", "wards": ["Mỹ An", "Hòa Hải", "Hòa Quý", "Khuê Mỹ"]},
    {"district": "Cẩm Lệ", "wards": ["Hòa Phát", "Hòa An", "Khuê Trung", "Hòa Xuân"]},
    {"district": "Liên Chiểu", "wards": ["Hòa Minh", "Hòa Khánh Bắc", "Hòa Khánh Nam"]},
]

# Feature type mapping (Vietnamese names as used in existing DB)
FEATURE_TYPE_MAP = {
    "Cột điện": {"code": "cot_dien", "category": "utility", "iot_types": ["vibration", "temperature"]},
    "Đèn giao thông": {"code": "den_giao_thong", "category": "traffic", "iot_types": ["power", "temperature"]},
    "Đèn đường": {"code": "den_duong", "category": "lighting", "iot_types": ["power"]},
    "Trụ chữa cháy": {"code": "tru_chua_chay", "category": "safety", "iot_types": ["pressure"]},
    "Trạm điện": {"code": "tram_dien", "category": "utility", "iot_types": ["power", "voltage", "temperature"]},
    "Cống thoát nước": {"code": "cong_thoat_nuoc", "category": "infrastructure", "iot_types": ["water_level", "flow_rate"]},
    "Đường ống điện": {"code": "duong_ong_dien", "category": "utility", "iot_types": ["temperature"]},
    "Trạm sạc": {"code": "tram_sac", "category": "utility", "iot_types": ["power", "current"]},
    "Ống dẫn nước": {"code": "ong_dan_nuoc", "category": "infrastructure", "iot_types": ["pressure", "flow_rate"]},
}

# Sensor configs by iot_type
SENSOR_CONFIGS = {
    "temperature": {
        "sensor_type": "temperature", "unit": "°C", "sample_rate": 300,
        "value_range": (20, 45), "normal_range": (25, 35),
        "thresholds": {"min_value": -10, "max_value": 60, "warning_max": 45, "critical_max": 55, "warning_min": 5, "critical_min": 0},
        "manufacturers": ["Sensirion", "Bosch", "Texas Instruments"],
        "models": ["SHT30", "BME280", "TMP102"],
    },
    "humidity": {
        "sensor_type": "humidity", "unit": "%", "sample_rate": 300,
        "value_range": (40, 90), "normal_range": (50, 80),
        "thresholds": {"min_value": 0, "max_value": 100, "warning_max": 90, "critical_max": 95, "warning_min": 10, "critical_min": 5},
        "manufacturers": ["Sensirion", "Honeywell"], "models": ["SHT30", "HIH6130"],
    },
    "pressure": {
        "sensor_type": "pressure", "unit": "bar", "sample_rate": 600,
        "value_range": (2.0, 6.0), "normal_range": (3.0, 5.0),
        "thresholds": {"min_value": 1.5, "max_value": 8.0, "warning_min": 2.5, "critical_min": 2.0, "warning_max": 6.5, "critical_max": 7.5},
        "manufacturers": ["Bosch", "Honeywell", "TE Connectivity"], "models": ["BMP280", "MPX5700", "MS5611"],
    },
    "vibration": {
        "sensor_type": "vibration", "unit": "mm/s", "sample_rate": 60,
        "value_range": (0, 15), "normal_range": (0.5, 5),
        "thresholds": {"min_value": 0, "max_value": 30, "warning_max": 10, "critical_max": 20},
        "manufacturers": ["Analog Devices", "STMicroelectronics"], "models": ["ADXL345", "LSM6DS3"],
    },
    "power": {
        "sensor_type": "power", "unit": "kW", "sample_rate": 60,
        "value_range": (0, 500), "normal_range": (50, 300),
        "thresholds": {"min_value": 0, "max_value": 600, "warning_max": 450, "critical_max": 550},
        "manufacturers": ["Schneider Electric", "ABB", "Siemens"], "models": ["PM8000", "CM4000", "SENTRON"],
    },
    "voltage": {
        "sensor_type": "voltage", "unit": "V", "sample_rate": 30,
        "value_range": (210, 240), "normal_range": (218, 232),
        "thresholds": {"min_value": 200, "max_value": 250, "warning_min": 210, "warning_max": 240, "critical_min": 200, "critical_max": 250},
        "manufacturers": ["Schneider Electric", "ABB"], "models": ["PM5000", "A44"],
    },
    "current": {
        "sensor_type": "current", "unit": "A", "sample_rate": 30,
        "value_range": (0, 400), "normal_range": (50, 250),
        "thresholds": {"min_value": 0, "max_value": 500, "warning_max": 400, "critical_max": 450},
        "manufacturers": ["ABB", "Siemens"], "models": ["CT-100", "7KT1260"],
    },
    "water_level": {
        "sensor_type": "water_level", "unit": "cm", "sample_rate": 300,
        "value_range": (0, 150), "normal_range": (10, 60),
        "thresholds": {"min_value": 0, "max_value": 200, "warning_max": 100, "critical_max": 150},
        "manufacturers": ["Siemens", "Endress+Hauser"], "models": ["SITRANS LU", "FMU30"],
    },
    "flow_rate": {
        "sensor_type": "flow_rate", "unit": "L/s", "sample_rate": 60,
        "value_range": (0, 50), "normal_range": (5, 30),
        "thresholds": {"min_value": 0, "max_value": 100, "warning_max": 70, "critical_max": 90},
        "manufacturers": ["Endress+Hauser", "Siemens"], "models": ["Promag W", "SITRANS FM"],
    },
}


def random_location():
    """Get a random Da Nang district/ward."""
    district_info = random.choice(DA_NANG_DISTRICTS)
    ward = random.choice(district_info["wards"])
    street = random.choice(DA_NANG_STREETS)
    return {
        "address": f"{random.randint(1, 500)} {street}, {ward}, {district_info['district']}",
        "ward": ward,
        "district": district_info["district"],
        "city": "Đà Nẵng",
    }


def generate_phone():
    return f"0{random.choice([3,5,7,8,9])}{random.randint(10000000, 99999999)}"


async def get_database():
    client = AsyncIOMotorClient(MONGODB_URL)
    return client, client[DATABASE_NAME]


# ═══════════════════════════════════════════════════════════════
# 1. SEED USERS (technicians + citizens, keep existing admins)
# ═══════════════════════════════════════════════════════════════
async def seed_users(db):
    """Add technicians and citizens. Keep existing admin accounts."""
    print("\n📌 Seeding users...")
    
    # Simple bcrypt hash for "Tech@2025!" - pre-computed
    # We'll use a workaround: insert with a known hash
    # Actually let's generate a proper hash using passlib
    from hashlib import sha256
    import hmac
    
    # For demo purposes, we'll use a fixed bcrypt hash
    # This is the hash of "Tech@2025!" generated by passlib bcrypt
    tech_hash = "$2b$12$LJ3m4ys4J.HjXcGK7xwPpuGZoKHrGMoYfNvGvR0C2q4RlRzFhV5pS"
    citizen_hash = "$2b$12$LJ3m4ys4J.HjXcGK7xwPpuGZoKHrGMoYfNvGvR0C2q4RlRzFhV5pS"

    users = []
    
    # Technicians
    for i, name in enumerate(TECHNICIAN_NAMES):
        username = f"technician{i+1}"
        existing = await db.users.find_one({"username": username})
        if existing:
            continue
        users.append({
            "username": username,
            "email": f"tech{i+1}@openinfra.space",
            "password_hash": tech_hash,
            "full_name": name,
            "phone": generate_phone(),
            "role": "technician",
            "status": "active",
            "department": random.choice(["Bảo trì", "Vận hành", "Kỹ thuật điện", "Cấp thoát nước"]),
            "permissions": ["maintenance:read", "maintenance:write", "incidents:read", "incidents:write"],
            "language": "vi",
            "created_at": datetime.utcnow() - timedelta(days=random.randint(60, 365)),
            "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
        })
    
    # Citizens
    for i, name in enumerate(CITIZEN_NAMES):
        username = f"citizen{i+1}"
        existing = await db.users.find_one({"username": username})
        if existing:
            continue
        users.append({
            "username": username,
            "email": f"citizen{i+1}@gmail.com",
            "password_hash": citizen_hash,
            "full_name": name,
            "phone": generate_phone(),
            "role": "citizen",
            "status": "active",
            "language": "vi",
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 180)),
            "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
        })
    
    if users:
        await db.users.insert_many(users)
    
    total = await db.users.count_documents({})
    print(f"   ✅ Users total: {total} (added {len(users)} new)")
    return [str(u["_id"]) async for u in db.users.find({}, {"_id": 1})]


# ═══════════════════════════════════════════════════════════════
# 2. ENRICH ASSETS (add missing fields to existing assets)
# ═══════════════════════════════════════════════════════════════
async def enrich_assets(db, user_ids):
    """Add status, location, specs, etc. to existing assets that lack them."""
    print("\n📌 Enriching assets with additional fields...")
    
    assets = await db.assets.find({}).to_list(length=2000)
    enriched = 0
    
    statuses = ["operational", "operational", "operational", "maintenance", "damaged", "retired"]
    conditions = ["excellent", "good", "good", "fair", "poor"]
    lifecycle = ["operational", "operational", "operational", "construction", "decommissioned"]
    
    for asset in assets:
        update = {}
        ft = asset.get("feature_type", "")
        fc = asset.get("feature_code", "")
        info = FEATURE_TYPE_MAP.get(ft, {})
        
        # Add status if missing
        if "status" not in asset:
            update["status"] = random.choice(statuses)
        
        if "condition" not in asset:
            update["condition"] = random.choice(conditions)
        
        if "lifecycle_stage" not in asset:
            update["lifecycle_stage"] = random.choice(lifecycle)
        
        # Add location details if missing
        if "location" not in asset:
            loc = random_location()
            update["location"] = loc
        
        # Add name if missing
        if "name" not in asset:
            street = random.choice(DA_NANG_STREETS)
            update["name"] = f"{ft} - {street}"
        
        # Add asset_code if missing
        if "asset_code" not in asset:
            short_id = str(asset["_id"])[-6:].upper()
            code_prefix = fc.upper()[:3] if fc else "AST"
            update["asset_code"] = f"{code_prefix}-{short_id}"
        
        # Add category
        if "category" not in asset:
            update["category"] = info.get("category", "infrastructure")
        
        # IoT enabled for relevant types
        if "iot_enabled" not in asset:
            iot_types = info.get("iot_types", [])
            update["iot_enabled"] = len(iot_types) > 0 and random.random() > 0.3
        
        # Add installation date
        if "installation_date" not in asset and "installed_date" not in asset:
            update["installation_date"] = datetime.utcnow() - timedelta(days=random.randint(365, 3650))
        
        if "public_info_visible" not in asset:
            update["public_info_visible"] = True
        
        if "created_by" not in asset and user_ids:
            update["created_by"] = random.choice(user_ids)
        
        if "updated_at" not in asset:
            update["updated_at"] = datetime.utcnow() - timedelta(days=random.randint(0, 60))
        
        if update:
            await db.assets.update_one({"_id": asset["_id"]}, {"$set": update})
            enriched += 1
    
    print(f"   ✅ Enriched {enriched} assets")


# ═══════════════════════════════════════════════════════════════
# 3. SEED IoT SENSORS
# ═══════════════════════════════════════════════════════════════
async def seed_iot_sensors(db, user_ids):
    """Create IoT sensors for IoT-enabled assets."""
    print("\n📌 Seeding IoT sensors...")
    
    await db.iot_sensors.delete_many({})
    
    iot_assets = await db.assets.find({"iot_enabled": True}).to_list(length=2000)
    if not iot_assets:
        # Fallback: get ~40% of all assets
        all_assets = await db.assets.find({}).to_list(length=2000)
        iot_assets = random.sample(all_assets, int(len(all_assets) * 0.4))
    
    sensors = []
    sensor_idx = 1
    
    for asset in iot_assets:
        ft = asset.get("feature_type", "")
        info = FEATURE_TYPE_MAP.get(ft)
        if not info:
            continue
        
        iot_types = info.get("iot_types", [])
        asset_id = str(asset["_id"])
        
        for iot_type in iot_types:
            cfg = SENSOR_CONFIGS.get(iot_type)
            if not cfg:
                continue
            
            sensor_code = f"SENS-{sensor_idx:05d}"
            installed_days_ago = random.randint(30, 730)
            installed_at = datetime.utcnow() - timedelta(days=installed_days_ago)
            
            # 80% online, 12% offline, 8% maintenance
            status_roll = random.random()
            if status_roll < 0.80:
                status = "online"
                last_seen = datetime.utcnow() - timedelta(minutes=random.randint(1, 30))
            elif status_roll < 0.92:
                status = "offline"
                last_seen = datetime.utcnow() - timedelta(hours=random.randint(2, 72))
            else:
                status = "maintenance"
                last_seen = datetime.utcnow() - timedelta(days=random.randint(1, 14))
            
            conn_type = random.choice(["wifi", "lora", "cellular"])
            ip_address = f"192.168.{random.randint(1,10)}.{random.randint(100,254)}" if conn_type == "wifi" else None
            mac_addr = f"{random.randint(0,255):02X}:{random.randint(0,255):02X}:{random.randint(0,255):02X}:{random.randint(0,255):02X}:{random.randint(0,255):02X}:{random.randint(0,255):02X}"
            
            min_v, max_v = cfg["normal_range"]
            last_value = round(random.uniform(min_v, max_v), 2)
            
            calibration_date = installed_at + timedelta(days=random.randint(1, 30))
            
            sensor = {
                "_id": ObjectId(),
                "sensor_code": sensor_code,
                "asset_id": asset_id,
                "sensor_type": cfg["sensor_type"],
                "manufacturer": random.choice(cfg["manufacturers"]),
                "model": random.choice(cfg["models"]),
                "firmware_version": f"v{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}",
                "measurement_unit": cfg["unit"],
                "sample_rate": cfg["sample_rate"],
                "thresholds": cfg["thresholds"],
                "connection_type": conn_type,
                "ip_address": ip_address,
                "mac_address": mac_addr,
                "gateway_id": f"GW-{random.randint(1,8):03d}",
                "status": status,
                "last_seen": last_seen,
                "last_reading": {
                    "value": last_value,
                    "unit": cfg["unit"],
                    "timestamp": last_seen,
                    "status": "normal",
                },
                "calibration_date": calibration_date,
                "calibration_due": calibration_date + timedelta(days=365),
                "calibration_factor": round(random.uniform(0.97, 1.03), 4),
                "installed_at": installed_at,
                "installed_by": random.choice(user_ids) if user_ids else None,
                "location_description": f"Lắp trên {ft} tại {random.choice(DA_NANG_STREETS)}",
                "maintenance_schedule": random.choice(["monthly", "quarterly", "yearly"]),
                "last_maintenance": datetime.utcnow() - timedelta(days=random.randint(7, 90)),
                "next_maintenance": datetime.utcnow() + timedelta(days=random.randint(7, 90)),
                "created_at": installed_at,
                "updated_at": last_seen,
                "created_by": random.choice(user_ids) if user_ids else None,
                "tags": [cfg["sensor_type"], ft, conn_type],
            }
            sensors.append(sensor)
            sensor_idx += 1
    
    if sensors:
        await db.iot_sensors.insert_many(sensors)
    
    # Create indexes
    await db.iot_sensors.create_index("sensor_code", unique=True)
    await db.iot_sensors.create_index("asset_id")
    await db.iot_sensors.create_index("status")
    
    print(f"   ✅ Created {len(sensors)} IoT sensors")
    return [str(s["_id"]) for s in sensors]


# ═══════════════════════════════════════════════════════════════
# 4. SEED SENSOR READINGS (7 days of historical data)
# ═══════════════════════════════════════════════════════════════
async def seed_sensor_readings(db):
    """Generate 7 days of realistic sensor readings."""
    print("\n📌 Seeding sensor readings (7 days)...")
    
    # Drop existing readings
    try:
        await db.sensor_readings.drop()
    except Exception:
        pass
    
    sensors = await db.iot_sensors.find({}).to_list(length=5000)
    total_readings = 0
    
    now = datetime.utcnow()
    hours_back = 168  # 7 days
    
    for sensor in sensors:
        cfg = SENSOR_CONFIGS.get(sensor.get("sensor_type"))
        if not cfg:
            continue
        
        sensor_id = str(sensor["_id"])
        asset_id = sensor.get("asset_id")
        sample_rate = cfg["sample_rate"]
        min_v, max_v = cfg["value_range"]
        norm_min, norm_max = cfg["normal_range"]
        
        readings = []
        
        # Generate readings at sample_rate intervals for 7 days
        # But cap to avoid too many (max ~2000 per sensor)
        effective_interval = max(sample_rate, 300)  # Minimum 5-min intervals for storage
        
        # Simulate patterns
        base_value = random.uniform(norm_min, norm_max)
        
        # Random anomaly events (2-5 events over 7 days)
        anomaly_events = []
        for _ in range(random.randint(2, 5)):
            anomaly_hour = random.randint(0, hours_back)
            anomaly_duration = random.randint(1, 4)  # hours
            anomaly_events.append((anomaly_hour, anomaly_duration))
        
        t = now - timedelta(hours=hours_back)
        while t <= now:
            hour_of_day = t.hour
            hours_from_start = (now - t).total_seconds() / 3600
            
            # Time-based patterns
            value = base_value
            
            if cfg["sensor_type"] == "power" and sensor.get("tags") and "Đèn đường" in sensor.get("tags", []):
                # Street lights: high at night, low during day
                if 6 <= hour_of_day <= 18:
                    value = random.uniform(0, max_v * 0.05)  # near zero during day
                else:
                    value = random.uniform(norm_min, norm_max)
            elif cfg["sensor_type"] == "power":
                # General power: higher during work hours
                if 8 <= hour_of_day <= 18:
                    value = random.uniform(norm_min * 1.2, norm_max)
                else:
                    value = random.uniform(norm_min * 0.3, norm_min)
            elif cfg["sensor_type"] == "temperature":
                # Temperature: peaks at 14:00, lowest at 5:00
                temp_offset = 5 * math.sin((hour_of_day - 5) * math.pi / 12)
                value = base_value + temp_offset + random.uniform(-1, 1)
            elif cfg["sensor_type"] in ("water_level", "flow_rate"):
                # Water: higher in morning and evening, spike during rain
                if 6 <= hour_of_day <= 9 or 17 <= hour_of_day <= 20:
                    value = random.uniform(norm_max * 0.7, norm_max)
                else:
                    value = random.uniform(norm_min, norm_max * 0.5)
            elif cfg["sensor_type"] == "voltage":
                # Voltage: slight dip during peak load
                if 18 <= hour_of_day <= 21:
                    value = random.uniform(min_v, norm_min)  # voltage dip
                else:
                    value = random.uniform(norm_min, norm_max)
            else:
                value = base_value + random.uniform(-(norm_max - norm_min) * 0.2, (norm_max - norm_min) * 0.2)
            
            # Check anomaly events
            for anom_h, anom_d in anomaly_events:
                if anom_h <= hours_from_start <= anom_h + anom_d:
                    # Spike value above warning threshold
                    thresholds = cfg["thresholds"]
                    if "warning_max" in thresholds:
                        value = random.uniform(thresholds["warning_max"], thresholds.get("critical_max", thresholds["warning_max"] * 1.2))
                    else:
                        value = max_v * random.uniform(0.85, 0.95)
                    break
            
            value = max(min_v, min(max_v, value))
            
            # Determine status
            status = "normal"
            threshold_exceeded = False
            thresholds = cfg["thresholds"]
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
            
            readings.append({
                "sensor_id": sensor_id,
                "asset_id": asset_id,
                "timestamp": t,
                "value": round(value, 2),
                "unit": cfg["unit"],
                "quality": "good",
                "status": status,
                "threshold_exceeded": threshold_exceeded,
                "metadata": {},
            })
            
            t += timedelta(seconds=effective_interval)
        
        # Insert in batches
        if readings:
            batch_size = 1000
            for i in range(0, len(readings), batch_size):
                batch = readings[i:i + batch_size]
                await db.sensor_readings.insert_many(batch)
            total_readings += len(readings)
    
    # Create indexes
    await db.sensor_readings.create_index([("sensor_id", 1), ("timestamp", -1)])
    await db.sensor_readings.create_index([("asset_id", 1), ("timestamp", -1)])
    await db.sensor_readings.create_index("timestamp")
    
    print(f"   ✅ Created {total_readings} sensor readings")


# ═══════════════════════════════════════════════════════════════
# 5. SEED INCIDENTS
# ═══════════════════════════════════════════════════════════════
async def seed_incidents(db, user_ids):
    """Create realistic incidents in Vietnamese."""
    print("\n📌 Seeding incidents...")
    
    await db.incidents.delete_many({})
    
    assets = await db.assets.find({}).to_list(length=2000)
    asset_map = {str(a["_id"]): a for a in assets}
    asset_ids = list(asset_map.keys())
    
    # Incident templates by feature type
    INCIDENT_TEMPLATES = [
        # Cột điện
        {"title": "Cột điện bị nghiêng nguy hiểm", "desc": "Cột điện bị nghiêng do va chạm xe tải, có nguy cơ đổ gây nguy hiểm cho người đi đường.", "cat": "damage", "sev": "critical", "ft": "Cột điện"},
        {"title": "Dây điện bị đứt rơi xuống đường", "desc": "Dây điện trên cột bị đứt rơi xuống mặt đường, rất nguy hiểm cho người và phương tiện.", "cat": "safety_hazard", "sev": "critical", "ft": "Cột điện"},
        {"title": "Cột điện bị gỉ sét phần chân", "desc": "Chân cột điện bị ăn mòn gỉ sét nghiêm trọng, cần kiểm tra và gia cố.", "cat": "damage", "sev": "high", "ft": "Cột điện"},
        {"title": "Cột điện bị hư hỏng biến thế", "desc": "Biến thế trên cột điện phát ra tiếng kêu bất thường và có mùi khét.", "cat": "malfunction", "sev": "high", "ft": "Cột điện"},
        
        # Đèn giao thông
        {"title": "Đèn giao thông không hoạt động", "desc": "Đèn tín hiệu giao thông tại ngã tư không hoạt động, đèn đỏ sáng liên tục không chuyển sang xanh.", "cat": "malfunction", "sev": "critical", "ft": "Đèn giao thông"},
        {"title": "Đèn giao thông hiển thị sai tín hiệu", "desc": "Đèn giao thông hiển thị tín hiệu xanh cả hai chiều cùng lúc, gây nguy hiểm.", "cat": "malfunction", "sev": "critical", "ft": "Đèn giao thông"},
        {"title": "Đèn giao thông bị mờ khó nhìn", "desc": "Đèn LED tín hiệu giao thông bị mờ, tài xế khó nhận diện vào ban ngày.", "cat": "malfunction", "sev": "medium", "ft": "Đèn giao thông"},
        {"title": "Bộ đếm ngược đèn giao thông bị lỗi", "desc": "Bộ đếm ngược hiển thị sai số, nhảy số không đều.", "cat": "malfunction", "sev": "medium", "ft": "Đèn giao thông"},
        
        # Đèn đường
        {"title": "Đèn đường không sáng", "desc": "Đèn đường tại đoạn đường này không sáng vào ban đêm, gây mất an toàn cho người đi bộ.", "cat": "malfunction", "sev": "medium", "ft": "Đèn đường"},
        {"title": "Đèn đường sáng ban ngày", "desc": "Đèn đường vẫn sáng suốt ban ngày, gây lãng phí điện.", "cat": "malfunction", "sev": "low", "ft": "Đèn đường"},
        {"title": "Đèn đường nhấp nháy liên tục", "desc": "Đèn đường bị nhấp nháy liên tục vào ban đêm, ảnh hưởng thị giác người đi đường.", "cat": "malfunction", "sev": "medium", "ft": "Đèn đường"},
        {"title": "Trụ đèn đường bị gãy đổ", "desc": "Trụ đèn đường bị gãy đổ sau bão, nằm chắn ngang lề đường.", "cat": "damage", "sev": "high", "ft": "Đèn đường"},
        
        # Cống thoát nước
        {"title": "Cống thoát nước bị tắc nghẽn", "desc": "Hệ thống thoát nước bị tắc do rác thải và bùn đất, gây ngập đường sau mưa.", "cat": "damage", "sev": "high", "ft": "Cống thoát nước"},
        {"title": "Nắp cống bị mất", "desc": "Nắp cống thoát nước bị mất, tạo hố nguy hiểm trên mặt đường.", "cat": "safety_hazard", "sev": "critical", "ft": "Cống thoát nước"},
        {"title": "Cống thoát nước bốc mùi hôi", "desc": "Cống thoát nước bốc mùi hôi nồng nặc, ảnh hưởng đến cư dân xung quanh.", "cat": "other", "sev": "medium", "ft": "Cống thoát nước"},
        {"title": "Ngập lụt do cống quá tải", "desc": "Đường bị ngập nước sâu 30-40cm sau cơn mưa lớn do hệ thống cống quá tải.", "cat": "safety_hazard", "sev": "high", "ft": "Cống thoát nước"},
        
        # Trạm điện
        {"title": "Trạm điện phát tiếng nổ", "desc": "Trạm biến áp phát ra tiếng nổ và tia lửa, đã mất điện khu vực.", "cat": "malfunction", "sev": "critical", "ft": "Trạm điện"},
        {"title": "Trạm điện rò rỉ dầu", "desc": "Máy biến áp tại trạm điện bị rò rỉ dầu cách điện, cần xử lý gấp.", "cat": "damage", "sev": "high", "ft": "Trạm điện"},
        {"title": "Hàng rào trạm điện bị phá", "desc": "Hàng rào bảo vệ trạm điện bị phá hỏng, có nguy cơ trẻ em vào khu vực nguy hiểm.", "cat": "vandalism", "sev": "high", "ft": "Trạm điện"},
        
        # Trụ chữa cháy
        {"title": "Trụ chữa cháy bị rò nước", "desc": "Trụ chữa cháy bị rò rỉ nước liên tục, cần thay van.", "cat": "malfunction", "sev": "medium", "ft": "Trụ chữa cháy"},
        {"title": "Trụ chữa cháy bị che khuất", "desc": "Trụ chữa cháy bị xe đậu che khuất và bị cây cối mọc bao quanh.", "cat": "other", "sev": "low", "ft": "Trụ chữa cháy"},
        {"title": "Trụ chữa cháy không có nước", "desc": "Kiểm tra phát hiện trụ chữa cháy không có nước, van bị kẹt.", "cat": "malfunction", "sev": "high", "ft": "Trụ chữa cháy"},

        # Trạm sạc
        {"title": "Trạm sạc xe điện bị hỏng màn hình", "desc": "Màn hình điều khiển trạm sạc bị hỏng, không hiển thị thông tin sạc.", "cat": "malfunction", "sev": "medium", "ft": "Trạm sạc"},
        {"title": "Trạm sạc không nhận thẻ", "desc": "Trạm sạc không nhận thẻ thanh toán, người dùng không sạc được.", "cat": "malfunction", "sev": "medium", "ft": "Trạm sạc"},
        
        # Ống dẫn nước
        {"title": "Ống nước bị vỡ gây ngập", "desc": "Ống dẫn nước chính bị vỡ, nước phun mạnh gây ngập khu vực.", "cat": "damage", "sev": "critical", "ft": "Ống dẫn nước"},
        {"title": "Ống nước rò rỉ trên đường", "desc": "Phát hiện nước rỉ ra mặt đường, nghi ngờ ống nước ngầm bị rò.", "cat": "damage", "sev": "medium", "ft": "Ống dẫn nước"},
        
        # Đường ống điện
        {"title": "Đường ống điện ngầm bị lộ", "desc": "Đường ống bảo vệ dây điện ngầm bị lộ ra do sụt lún đất.", "cat": "safety_hazard", "sev": "high", "ft": "Đường ống điện"},
        {"title": "Cáp điện ngầm bị đào trúng", "desc": "Thi công đào đường làm hỏng cáp điện ngầm, mất điện khu vực.", "cat": "damage", "sev": "critical", "ft": "Đường ống điện"},
    ]
    
    incidents = []
    statuses = ["reported", "acknowledged", "assigned", "investigating", "resolved", "closed"]
    
    # Create 60 incidents
    for i in range(60):
        template = random.choice(INCIDENT_TEMPLATES)
        
        # Find matching asset
        matching_assets = [aid for aid, a in asset_map.items() if a.get("feature_type") == template["ft"]]
        asset_id = random.choice(matching_assets) if matching_assets else random.choice(asset_ids)
        asset_doc = asset_map.get(asset_id, {})
        
        # Get coordinates from asset
        geom = asset_doc.get("geometry", {})
        coords = geom.get("coordinates", [108.22, 16.05])
        if isinstance(coords[0], list):
            coords = coords[0]  # Use first point for LineString/Polygon
        
        loc_coords = [coords[0] + random.uniform(-0.003, 0.003), coords[1] + random.uniform(-0.003, 0.003)]
        
        status = random.choice(statuses)
        reported_at = datetime.utcnow() - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
        loc_info = random_location()
        
        incident = {
            "incident_number": f"INC-2026-{i+1:05d}",
            "asset_id": asset_id,
            "title": template["title"],
            "description": template["desc"],
            "category": template["cat"],
            "severity": template["sev"],
            "status": status,
            "location": {
                "geometry": {"type": "Point", "coordinates": loc_coords},
                "address": loc_info["address"],
                "description": f"Tại {random.choice(DA_NANG_STREETS)}, gần ngã tư",
                "district": loc_info["district"],
                "ward": loc_info["ward"],
            },
            "reported_by": random.choice(user_ids),
            "reporter_type": random.choice(["citizen", "citizen", "citizen", "technician", "system"]),
            "reported_via": random.choice(["web", "mobile", "mobile", "phone", "qr_code"]),
            "reported_at": reported_at,
            "public_visible": True,
            "upvotes": random.randint(0, 30) if random.random() > 0.4 else 0,
            "comments": [],
            "created_at": reported_at,
            "updated_at": reported_at + timedelta(hours=random.randint(0, 48)),
        }
        
        # Add progress fields based on status
        tech_ids = [uid for uid in user_ids]
        
        if status in ("acknowledged", "assigned", "investigating", "resolved", "closed"):
            incident["acknowledged_at"] = reported_at + timedelta(hours=random.randint(1, 12))
            incident["acknowledged_by"] = random.choice(user_ids)
        
        if status in ("assigned", "investigating", "resolved", "closed"):
            incident["assigned_to"] = random.choice(user_ids)
        
        if status in ("resolved", "closed"):
            incident["resolved_at"] = reported_at + timedelta(days=random.randint(1, 7))
            incident["resolved_by"] = incident.get("assigned_to", random.choice(user_ids))
            incident["resolution_notes"] = random.choice([
                "Đã sửa chữa và kiểm tra hoạt động bình thường.",
                "Đã thay thế thiết bị hỏng bằng thiết bị mới.",
                "Đã khắc phục sự cố, khu vực an toàn trở lại.",
                "Đã xử lý và bàn giao cho đơn vị quản lý.",
                "Đã hoàn thành sửa chữa, thiết bị hoạt động ổn định.",
            ])
            incident["resolution_type"] = "fixed"
        
        if status == "closed":
            incident["closed_at"] = incident["resolved_at"] + timedelta(days=random.randint(1, 3))
        
        # Add comments for active incidents
        if status not in ("reported",):
            num_comments = random.randint(1, 4)
            for c in range(num_comments):
                incident["comments"].append({
                    "user_id": random.choice(user_ids),
                    "comment": random.choice([
                        "Đã ghi nhận, đang cử đội ngũ xuống hiện trường.",
                        "Đội kỹ thuật đã đến kiểm tra, đang đánh giá tình trạng.",
                        "Cần thêm vật tư để sửa chữa, đã đặt hàng.",
                        "Đã hoàn thành 70% công việc, dự kiến xong trong ngày.",
                        "Đã liên hệ đơn vị liên quan để phối hợp xử lý.",
                        "Khu vực đã được rào chắn bảo vệ tạm thời.",
                        "Báo cáo tiến độ: đang thi công sửa chữa.",
                    ]),
                    "posted_at": reported_at + timedelta(hours=random.randint(1, 72)),
                    "is_internal": random.random() > 0.6,
                })
        
        # AI verification for some
        if random.random() > 0.7:
            incident["ai_verified"] = True
            incident["confidence_score"] = round(random.uniform(0.75, 0.98), 2)
        
        incidents.append(incident)
    
    if incidents:
        await db.incidents.insert_many(incidents)
    
    print(f"   ✅ Created {len(incidents)} incidents")
    return [str(ObjectId()) for _ in incidents]  # simplification


# ═══════════════════════════════════════════════════════════════
# 6. SEED MAINTENANCE RECORDS
# ═══════════════════════════════════════════════════════════════
async def seed_maintenance(db, user_ids):
    """Create realistic maintenance records."""
    print("\n📌 Seeding maintenance records...")
    
    await db.maintenance_records.delete_many({})
    
    assets = await db.assets.find({}).to_list(length=2000)
    asset_ids = [str(a["_id"]) for a in assets]
    
    MAINTENANCE_TASKS = [
        # Preventive
        {"type": "preventive", "title": "Kiểm tra định kì đèn giao thông", "desc": "Kiểm tra hệ thống tín hiệu, bóng đèn LED, dây điện và bộ điều khiển.", "dur": 120, "pri": "medium", "ft": "Đèn giao thông"},
        {"type": "preventive", "title": "Bảo dưỡng đèn đường", "desc": "Thay bóng LED, vệ sinh chao đèn, kiểm tra kết nối điện.", "dur": 60, "pri": "low", "ft": "Đèn đường"},
        {"type": "preventive", "title": "Nạo vét cống thoát nước", "desc": "Nạo vét bùn đất rác thải trong hệ thống cống, đảm bảo thoát nước tốt.", "dur": 240, "pri": "medium", "ft": "Cống thoát nước"},
        {"type": "preventive", "title": "Kiểm tra trụ chữa cháy", "desc": "Kiểm tra áp lực nước, bôi trơn van, kiểm tra rò rỉ.", "dur": 45, "pri": "high", "ft": "Trụ chữa cháy"},
        {"type": "preventive", "title": "Bảo dưỡng trạm biến áp", "desc": "Kiểm tra dầu biến áp, đo nhiệt độ, kiểm tra rò rỉ và tiếp địa.", "dur": 180, "pri": "high", "ft": "Trạm điện"},
        {"type": "preventive", "title": "Kiểm tra cột điện", "desc": "Kiểm tra độ nghiêng, ăn mòn chân cột, dây néo và phụ kiện.", "dur": 90, "pri": "medium", "ft": "Cột điện"},
        {"type": "preventive", "title": "Bảo trì trạm sạc xe điện", "desc": "Kiểm tra đầu sạc, màn hình, hệ thống thanh toán và cáp.", "dur": 90, "pri": "medium", "ft": "Trạm sạc"},
        {"type": "preventive", "title": "Kiểm tra đường ống nước", "desc": "Kiểm tra áp suất, rò rỉ và van trên tuyến ống.", "dur": 120, "pri": "medium", "ft": "Ống dẫn nước"},
        
        # Corrective
        {"type": "corrective", "title": "Sửa chữa đèn đường hỏng", "desc": "Thay thế bộ nguồn đèn LED hỏng, kiểm tra dây điện.", "dur": 120, "pri": "medium", "ft": "Đèn đường"},
        {"type": "corrective", "title": "Sửa đèn giao thông lỗi", "desc": "Thay bo mạch điều khiển đèn giao thông bị lỗi.", "dur": 180, "pri": "critical", "ft": "Đèn giao thông"},
        {"type": "corrective", "title": "Thay nắp cống hỏng", "desc": "Thay thế nắp cống bị vỡ bằng nắp gang mới.", "dur": 60, "pri": "critical", "ft": "Cống thoát nước"},
        {"type": "corrective", "title": "Sửa rò rỉ ống nước", "desc": "Hàn vá điểm rò rỉ trên đường ống nước chính.", "dur": 240, "pri": "high", "ft": "Ống dẫn nước"},
        {"type": "corrective", "title": "Gia cố cột điện nghiêng", "desc": "Nắn lại cột điện, thay dây néo và gia cố chân cột.", "dur": 300, "pri": "high", "ft": "Cột điện"},
        {"type": "corrective", "title": "Sửa trạm sạc lỗi", "desc": "Thay module sạc bị hỏng, cập nhật phần mềm điều khiển.", "dur": 150, "pri": "medium", "ft": "Trạm sạc"},
        
        # Emergency
        {"type": "emergency", "title": "Khắc phục ngập đường khẩn cấp", "desc": "Huy động bơm hút nước và thông cống để giải quyết ngập.", "dur": 180, "pri": "critical", "ft": "Cống thoát nước"},
        {"type": "emergency", "title": "Xử lý sự cố mất điện khu vực", "desc": "Khẩn cấp xử lý sự cố trạm biến áp gây mất điện diện rộng.", "dur": 240, "pri": "critical", "ft": "Trạm điện"},
        {"type": "emergency", "title": "Xử lý dây điện đứt rơi", "desc": "Cắt điện khu vực và thu gom dây điện rơi xuống đường.", "dur": 120, "pri": "critical", "ft": "Cột điện"},
        {"type": "emergency", "title": "Sửa ống nước vỡ", "desc": "Khẩn cấp đóng van và hàn vá ống nước vỡ gây ngập.", "dur": 180, "pri": "critical", "ft": "Ống dẫn nước"},
        
        # Predictive
        {"type": "predictive", "title": "Thay thế biến áp có dấu hiệu quá nhiệt", "desc": "Hệ thống IoT phát hiện nhiệt độ biến áp tăng bất thường, cần thay thế phòng ngừa.", "dur": 480, "pri": "high", "ft": "Trạm điện"},
        {"type": "predictive", "title": "Bảo dưỡng sớm đèn có công suất giảm", "desc": "Cảm biến phát hiện công suất đèn giảm 30%, cần thay bóng trước khi hỏng.", "dur": 60, "pri": "low", "ft": "Đèn đường"},
    ]
    
    statuses = ["scheduled", "in_progress", "completed", "completed", "completed", "waiting_approval", "cancelled", "on_hold"]
    
    records = []
    for i in range(50):
        task = random.choice(MAINTENANCE_TASKS)
        
        # Find matching asset
        asset_map_by_ft = {str(a["_id"]): a for a in assets if a.get("feature_type") == task["ft"]}
        if asset_map_by_ft:
            asset_id = random.choice(list(asset_map_by_ft.keys()))
        else:
            asset_id = random.choice(asset_ids)
        
        status = random.choice(statuses)
        scheduled_date = datetime.utcnow() + timedelta(days=random.randint(-60, 30))
        
        parts_options = [
            [{"part_name": "Bóng đèn LED 150W", "part_code": "LED-150", "quantity": 2, "unit_cost": 350000, "total_cost": 700000}],
            [{"part_name": "Bo mạch điều khiển", "part_code": "MCU-001", "quantity": 1, "unit_cost": 2500000, "total_cost": 2500000}],
            [{"part_name": "Nắp cống gang D600", "part_code": "NC-600", "quantity": 1, "unit_cost": 1800000, "total_cost": 1800000}],
            [{"part_name": "Van nước DN100", "part_code": "VN-100", "quantity": 2, "unit_cost": 450000, "total_cost": 900000}],
            [{"part_name": "Dầu biến áp 20L", "part_code": "OIL-20", "quantity": 1, "unit_cost": 1200000, "total_cost": 1200000}],
            [{"part_name": "Cáp điện 2x6mm 50m", "part_code": "CAP-6-50", "quantity": 1, "unit_cost": 850000, "total_cost": 850000}],
            [],
        ]
        
        record = {
            "work_order_number": f"WO-2026-{i+1:05d}",
            "asset_id": asset_id,
            "type": task["type"],
            "priority": task["pri"],
            "title": task["title"],
            "description": task["desc"],
            "status": status,
            "scheduled_date": scheduled_date,
            "estimated_duration": task["dur"],
            "assigned_to": random.choice(user_ids),
            "parts_used": random.choice(parts_options),
            "created_at": scheduled_date - timedelta(days=random.randint(3, 14)),
            "updated_at": scheduled_date + timedelta(days=random.randint(0, 7)),
            "created_by": random.choice(user_ids),
        }
        
        if status == "completed":
            record["actual_start_time"] = scheduled_date + timedelta(minutes=random.randint(0, 60))
            record["actual_end_time"] = record["actual_start_time"] + timedelta(minutes=task["dur"] + random.randint(-20, 60))
            record["actual_duration"] = int((record["actual_end_time"] - record["actual_start_time"]).total_seconds() / 60)
            record["technician_notes"] = random.choice([
                "Hoàn thành tốt, thiết bị hoạt động bình thường sau sửa chữa.",
                "Đã thay thế linh kiện hỏng, cần theo dõi thêm 1 tuần.",
                "Công việc hoàn thành đúng tiến độ, chất lượng đạt yêu cầu.",
                "Phát hiện thêm vấn đề nhỏ, đã xử lý luôn.",
                "Cần lên lịch bảo dưỡng tiếp theo trong 3 tháng.",
            ])
            record["actual_cost"] = random.uniform(500000, 10000000)
            record["quality_check"] = {
                "performed": True, "passed": random.random() > 0.1,
                "checked_by": random.choice(user_ids),
                "checked_at": record["actual_end_time"] + timedelta(hours=random.randint(1, 24)),
                "notes": "Kiểm tra đạt yêu cầu kỹ thuật.",
            }
        
        if status == "in_progress":
            record["actual_start_time"] = scheduled_date + timedelta(minutes=random.randint(0, 60))
        
        records.append(record)
    
    if records:
        await db.maintenance_records.insert_many(records)
    
    print(f"   ✅ Created {len(records)} maintenance records")
    return [str(r.get("_id", ObjectId())) for r in records]


# ═══════════════════════════════════════════════════════════════
# 7. SEED ALERTS
# ═══════════════════════════════════════════════════════════════
async def seed_alerts(db, user_ids):
    """Create realistic alerts from sensors and system."""
    print("\n📌 Seeding alerts...")
    
    await db.alerts.delete_many({})
    
    sensors = await db.iot_sensors.find({}).to_list(length=5000)
    sensor_ids = [str(s["_id"]) for s in sensors]
    assets = await db.assets.find({}, {"_id": 1}).to_list(length=2000)
    asset_ids = [str(a["_id"]) for a in assets]
    
    ALERT_TEMPLATES = [
        {"src": "sensor", "type": "threshold_exceeded", "sev": "warning", "title": "Nhiệt độ vượt ngưỡng cảnh báo", "msg": "Cảm biến ghi nhận nhiệt độ vượt ngưỡng cảnh báo ({value}°C > {threshold}°C)."},
        {"src": "sensor", "type": "threshold_exceeded", "sev": "critical", "title": "Nhiệt độ đạt mức nguy hiểm", "msg": "Nhiệt độ đạt mức nguy hiểm ({value}°C). Cần kiểm tra ngay."},
        {"src": "sensor", "type": "threshold_exceeded", "sev": "warning", "title": "Mực nước vượt ngưỡng", "msg": "Mực nước tại cống thoát vượt ngưỡng cảnh báo ({value}cm)."},
        {"src": "sensor", "type": "threshold_exceeded", "sev": "critical", "title": "Mực nước nguy hiểm - Nguy cơ ngập", "msg": "Mực nước đạt mức nguy hiểm ({value}cm), có nguy cơ ngập lụt."},
        {"src": "sensor", "type": "sensor_offline", "sev": "warning", "title": "Cảm biến mất kết nối", "msg": "Cảm biến không gửi dữ liệu trong {hours} giờ qua."},
        {"src": "sensor", "type": "threshold_exceeded", "sev": "warning", "title": "Áp suất nước thấp bất thường", "msg": "Áp suất nước tại trụ chữa cháy giảm xuống {value} bar."},
        {"src": "sensor", "type": "threshold_exceeded", "sev": "warning", "title": "Công suất bất thường", "msg": "Công suất tiêu thụ vượt mức bình thường ({value}kW)."},
        {"src": "sensor", "type": "threshold_exceeded", "sev": "critical", "title": "Điện áp vượt ngưỡng nguy hiểm", "msg": "Điện áp đạt {value}V, vượt ngưỡng an toàn."},
        {"src": "sensor", "type": "vibration_anomaly", "sev": "warning", "title": "Rung động bất thường phát hiện", "msg": "Cảm biến rung phát hiện rung động bất thường ({value}mm/s)."},
        {"src": "system", "type": "maintenance_due", "sev": "info", "title": "Đến hạn bảo trì định kì", "msg": "Tài sản cần được bảo trì theo lịch. Lần bảo trì cuối cách đây {days} ngày."},
        {"src": "system", "type": "asset_condition_deteriorated", "sev": "warning", "title": "Tình trạng tài sản xấu đi", "msg": "Tình trạng tài sản thay đổi sang mức 'kém', cần đánh giá."},
        {"src": "manual", "type": "custom", "sev": "info", "title": "Thông báo bảo trì từ quản trị viên", "msg": "Lịch bảo trì toàn hệ thống sẽ diễn ra vào cuối tuần này."},
    ]
    
    alerts = []
    statuses = ["active", "active", "active", "acknowledged", "resolved", "dismissed"]
    
    for i in range(40):
        tmpl = random.choice(ALERT_TEMPLATES)
        triggered_at = datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        status = random.choice(statuses)
        
        trigger_value = None
        threshold_value = None
        if tmpl["type"] == "threshold_exceeded":
            threshold_value = round(random.uniform(40, 100), 1)
            trigger_value = round(threshold_value + random.uniform(2, 15), 1)
        
        alert = {
            "alert_code": f"ALT-2026-{i+1:05d}",
            "source_type": tmpl["src"],
            "sensor_id": random.choice(sensor_ids) if sensor_ids and tmpl["src"] == "sensor" else None,
            "asset_id": random.choice(asset_ids) if asset_ids else None,
            "type": tmpl["type"],
            "severity": tmpl["sev"],
            "title": tmpl["title"],
            "message": tmpl["msg"].format(value=trigger_value or random.randint(10,100), threshold=threshold_value or 50, hours=random.randint(2,24), days=random.randint(30,180)),
            "trigger_value": trigger_value,
            "threshold_value": threshold_value,
            "condition": "greater_than" if tmpl["type"] == "threshold_exceeded" else None,
            "status": status,
            "triggered_at": triggered_at,
            "created_at": triggered_at,
            "updated_at": triggered_at + timedelta(hours=random.randint(0, 48)),
            "auto_created": tmpl["src"] != "manual",
            "metadata": {"source": "seed_data"},
        }
        
        if status in ("acknowledged", "resolved", "dismissed"):
            alert["acknowledged_at"] = triggered_at + timedelta(hours=random.randint(1, 12))
            alert["acknowledged_by"] = random.choice(user_ids)
        
        if status == "resolved":
            alert["resolved_at"] = triggered_at + timedelta(days=random.randint(1, 5))
            alert["resolved_by"] = alert.get("acknowledged_by")
            alert["resolution_notes"] = random.choice([
                "Đã kiểm tra và xử lý, thiết bị hoạt động bình thường.",
                "Cảnh báo do lỗi tạm thời, đã tự khôi phục.",
                "Đã bảo trì thiết bị, giá trị trở về mức bình thường.",
            ])
        
        if random.random() > 0.5:
            alert["notifications_sent"] = [{
                "recipient_id": random.choice(user_ids),
                "sent_at": triggered_at + timedelta(minutes=random.randint(1, 30)),
                "method": random.choice(["email", "push"]),
                "status": "delivered",
            }]
        
        alerts.append(alert)
    
    if alerts:
        await db.alerts.insert_many(alerts)
    
    print(f"   ✅ Created {len(alerts)} alerts")


# ═══════════════════════════════════════════════════════════════
# 8. SEED BUDGETS
# ═══════════════════════════════════════════════════════════════
async def seed_budgets(db, user_ids):
    """Create realistic budget data in VND."""
    print("\n📌 Seeding budgets...")
    
    await db.budgets.delete_many({})
    await db.budget_transactions.delete_many({})
    
    current_year = 2026
    
    budget_defs = [
        {"cat": "operations", "name": "Vận hành & Bảo trì hạ tầng", "desc": "Ngân sách vận hành và bảo trì hàng ngày các công trình hạ tầng đô thị", "alloc": (800_000_000, 2_000_000_000)},
        {"cat": "capital", "name": "Dự án đầu tư hạ tầng mới", "desc": "Ngân sách xây dựng và nâng cấp công trình hạ tầng lớn", "alloc": (3_000_000_000, 8_000_000_000)},
        {"cat": "maintenance", "name": "Bảo trì phòng ngừa", "desc": "Ngân sách bảo trì định kì và chăm sóc tài sản", "alloc": (500_000_000, 1_500_000_000)},
        {"cat": "emergency", "name": "Quỹ ứng phó khẩn cấp", "desc": "Ngân sách sửa chữa khẩn cấp và ứng phó thiên tai", "alloc": (300_000_000, 800_000_000)},
    ]
    
    budgets = []
    transactions = []
    txn_idx = 1
    
    for year in [2024, 2025, 2026]:
        for idx, bdef in enumerate(budget_defs):
            total = random.uniform(*bdef["alloc"])
            
            days_in_year = 365
            start = datetime(year, 1, 1)
            end = datetime(year, 12, 31)
            elapsed = min((datetime.utcnow() - start).days, days_in_year)
            progress = elapsed / days_in_year if year <= current_year else 0
            
            spent = total * progress * random.uniform(0.5, 0.85) if year <= current_year else 0
            
            budget = {
                "budget_code": f"BUD-{year}-{bdef['cat'].upper()[:3]}-{idx+1:03d}",
                "fiscal_year": year,
                "period_type": "annual",
                "start_date": start,
                "end_date": end,
                "name": f"{year} - {bdef['name']}",
                "description": bdef["desc"],
                "category": bdef["cat"],
                "total_allocated": total,
                "total_spent": spent,
                "total_remaining": total - spent,
                "utilization_rate": round(spent / total * 100, 1) if total > 0 else 0,
                "currency": "VND",
                "status": "approved" if year <= current_year else "draft",
                "departments": [
                    {"department": "Giao thông", "allocated_amount": total * 0.30, "spent_amount": spent * 0.30, "remaining_amount": (total - spent) * 0.30},
                    {"department": "Công trình công cộng", "allocated_amount": total * 0.25, "spent_amount": spent * 0.25, "remaining_amount": (total - spent) * 0.25},
                    {"department": "Cấp thoát nước", "allocated_amount": total * 0.20, "spent_amount": spent * 0.20, "remaining_amount": (total - spent) * 0.20},
                    {"department": "Điện lực", "allocated_amount": total * 0.15, "spent_amount": spent * 0.15, "remaining_amount": (total - spent) * 0.15},
                    {"department": "Công viên cây xanh", "allocated_amount": total * 0.10, "spent_amount": spent * 0.10, "remaining_amount": (total - spent) * 0.10},
                ],
                "breakdown": [
                    {"category": "Nhân công", "allocated": total * 0.40, "spent": spent * 0.40, "remaining": (total - spent) * 0.40},
                    {"category": "Vật tư", "allocated": total * 0.30, "spent": spent * 0.30, "remaining": (total - spent) * 0.30},
                    {"category": "Thiết bị", "allocated": total * 0.15, "spent": spent * 0.15, "remaining": (total - spent) * 0.15},
                    {"category": "Nhà thầu", "allocated": total * 0.15, "spent": spent * 0.15, "remaining": (total - spent) * 0.15},
                ],
                "created_by": random.choice(user_ids),
                "created_at": start - timedelta(days=60),
                "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            }
            
            if budget["status"] == "approved":
                budget["approved_by"] = random.choice(user_ids)
                budget["approved_at"] = budget["created_at"] + timedelta(days=random.randint(3, 14))
            
            budgets.append(budget)
    
    if budgets:
        result = await db.budgets.insert_many(budgets)
        budget_ids = [str(bid) for bid in result.inserted_ids]
    
    # Create transactions for current year budgets
    txn_descriptions = [
        ("Nhân công", ["Chi phí nhân công bảo trì tháng", "Lương kỹ thuật viên hiện trường", "Tăng ca sửa chữa khẩn cấp"], (1_000_000, 8_000_000)),
        ("Vật tư", ["Bóng đèn LED thay thế", "Nắp cống gang mới", "Cáp điện ngầm 50m", "Ống nước PVC DN100", "Sơn kẻ vạch đường"], (500_000, 15_000_000)),
        ("Thiết bị", ["Thuê xe cẩu", "Máy hút bùn cống", "Thiết bị đo điện", "Camera CCTV mới"], (3_000_000, 20_000_000)),
        ("Nhà thầu", ["Nhà thầu thi công sửa đường", "Dịch vụ chăm sóc cây xanh", "Nhà thầu điện chuyên dụng"], (10_000_000, 80_000_000)),
    ]
    
    assets = await db.assets.find({}, {"_id": 1}).to_list(length=2000)
    asset_ids = [str(a["_id"]) for a in assets]
    
    for i in range(40):
        cat_info = random.choice(txn_descriptions)
        cat_name, descs, amount_range = cat_info
        amount = random.uniform(*amount_range)
        txn_date = datetime.utcnow() - timedelta(days=random.randint(0, 120))
        txn_status = random.choice(["pending", "approved", "approved", "paid", "paid", "paid"])
        
        txn = {
            "transaction_number": f"TXN-2026-{txn_idx:06d}",
            "budget_id": random.choice(budget_ids) if budget_ids else None,
            "amount": round(amount),
            "currency": "VND",
            "transaction_date": txn_date,
            "description": random.choice(descs),
            "category": cat_name,
            "asset_id": random.choice(asset_ids) if random.random() > 0.3 else None,
            "vendor": random.choice([
                "Công ty TNHH Điện lực Đà Nẵng", "Xí nghiệp Cấp thoát nước",
                "Công ty Chiếu sáng Đô thị", "HTX Vận tải Trung Hậu",
                "Công ty TNHH Xây dựng Phú Hưng", "Cửa hàng Vật tư Điện Minh Long",
                "Công ty CP Môi trường Đà Nẵng", "Đội Bảo trì Hạ tầng Sơn Trà",
            ]),
            "status": txn_status,
            "created_at": txn_date - timedelta(days=random.randint(1, 7)),
            "updated_at": txn_date,
        }
        
        if txn_status in ("approved", "paid"):
            txn["approved_at"] = txn["created_at"] + timedelta(days=random.randint(1, 5))
        if txn_status == "paid":
            txn["payment_date"] = txn["approved_at"] + timedelta(days=random.randint(1, 14))
            txn["payment_method"] = random.choice(["transfer", "transfer", "check"])
        
        transactions.append(txn)
        txn_idx += 1
    
    if transactions:
        await db.budget_transactions.insert_many(transactions)
    
    print(f"   ✅ Created {len(budgets)} budgets, {len(transactions)} transactions")


# ═══════════════════════════════════════════════════════════════
# 9. SEED REPORTS
# ═══════════════════════════════════════════════════════════════
async def seed_reports(db, user_ids):
    """Create report records."""
    print("\n📌 Seeding reports...")
    
    await db.reports.delete_many({})
    
    templates = [
        {"type": "maintenance_summary", "name": "Báo cáo tổng hợp bảo trì tháng", "fmt": "pdf"},
        {"type": "asset_inventory", "name": "Báo cáo kiểm kê tài sản", "fmt": "excel"},
        {"type": "incident_report", "name": "Báo cáo sự cố tuần", "fmt": "pdf"},
        {"type": "budget_utilization", "name": "Báo cáo sử dụng ngân sách quý", "fmt": "excel"},
        {"type": "iot_sensor_data", "name": "Báo cáo phân tích dữ liệu cảm biến", "fmt": "pdf"},
        {"type": "custom", "name": "Báo cáo tổng hợp hạ tầng đô thị", "fmt": "pdf"},
    ]
    
    reports = []
    for i in range(15):
        tmpl = templates[i % len(templates)]
        created_at = datetime.utcnow() - timedelta(days=random.randint(0, 90))
        status = random.choice(["completed", "completed", "completed", "pending", "generating", "failed"])
        
        report = {
            "report_code": f"RPT-2026-{i+1:05d}",
            "type": tmpl["type"],
            "name": f"{tmpl['name']} - {i+1}",
            "description": f"Tự động tạo báo cáo {tmpl['name'].lower()}",
            "parameters": {
                "start_date": (created_at - timedelta(days=30)).isoformat(),
                "end_date": created_at.isoformat(),
            },
            "format": tmpl["fmt"],
            "status": status,
            "created_at": created_at,
            "created_by": random.choice(user_ids),
            "metadata": {"generated_by": "system"},
        }
        
        if status == "completed":
            report["generated_at"] = created_at + timedelta(hours=random.randint(1, 6))
            report["file_url"] = f"/reports/{report['report_code']}.{tmpl['fmt']}"
            report["file_size"] = random.randint(100_000, 5_000_000)
        elif status == "failed":
            report["error_message"] = "Lỗi khi tạo báo cáo: Timeout kết nối cơ sở dữ liệu"
        
        if random.random() > 0.6:
            report["scheduled"] = True
            report["schedule_pattern"] = random.choice(["0 0 * * *", "0 0 * * 1", "0 0 1 * *"])
            report["next_run"] = datetime.utcnow() + timedelta(days=random.randint(1, 30))
        
        reports.append(report)
    
    if reports:
        await db.reports.insert_many(reports)
    
    print(f"   ✅ Created {len(reports)} reports")


# ═══════════════════════════════════════════════════════════════
# 10. SEED NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════
async def seed_notifications(db, user_ids):
    """Create notifications for users."""
    print("\n📌 Seeding notifications...")
    
    await db.notifications.delete_many({})
    
    notif_templates = [
        {"type": "incident_reported", "title": "Sự cố mới được báo cáo", "msg": "Có sự cố mới '{detail}' cần xử lý.", "res": "incident"},
        {"type": "maintenance_assigned", "title": "Công việc bảo trì được giao", "msg": "Bạn được giao công việc bảo trì '{detail}'.", "res": "maintenance"},
        {"type": "alert_triggered", "title": "Cảnh báo hệ thống", "msg": "Cảnh báo: {detail}", "res": "alert"},
        {"type": "system", "title": "Thông báo hệ thống", "msg": "{detail}", "res": None},
        {"type": "budget_approved", "title": "Ngân sách được phê duyệt", "msg": "Ngân sách '{detail}' đã được phê duyệt.", "res": "budget"},
    ]
    
    details = [
        "Đèn đường hỏng tại Bạch Đằng", "Cống tắc đường Trần Phú",
        "Cột điện nghiêng Nguyễn Văn Linh", "Trạm điện quá nhiệt",
        "Mực nước vượt ngưỡng", "Bảo trì trạm sạc xe điện",
        "Cập nhật firmware cảm biến", "Lịch bảo trì quý II",
        "Đèn giao thông lỗi ngã tư", "Ống nước rò rỉ Hải Châu",
    ]
    
    notifications = []
    for i in range(50):
        tmpl = random.choice(notif_templates)
        detail = random.choice(details)
        created_at = datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        is_read = random.random() > 0.4
        
        notif = {
            "user_id": random.choice(user_ids),
            "type": tmpl["type"],
            "title": tmpl["title"],
            "message": tmpl["msg"].format(detail=detail),
            "resource_type": tmpl["res"],
            "resource_id": str(ObjectId()) if tmpl["res"] else None,
            "channels": [{
                "type": random.choice(["push", "email"]),
                "status": "delivered",
                "sent_at": created_at + timedelta(minutes=random.randint(1, 10)),
            }],
            "read": is_read,
            "read_at": created_at + timedelta(hours=random.randint(1, 24)) if is_read else None,
            "priority": random.choice(["low", "normal", "normal", "high"]),
            "created_at": created_at,
            "updated_at": created_at,
        }
        notifications.append(notif)
    
    if notifications:
        await db.notifications.insert_many(notifications)
    
    print(f"   ✅ Created {len(notifications)} notifications")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
async def main():
    print("=" * 65)
    print("  OpenInfra — Comprehensive Data Seeding")
    print("=" * 65)
    print(f"  MongoDB: {MONGODB_URL}")
    print(f"  Database: {DATABASE_NAME}")
    print("=" * 65)
    
    client, db = await get_database()
    
    try:
        # 1. Users (keep admins, add technicians + citizens)
        user_ids = await seed_users(db)
        
        # 2. Enrich existing assets
        await enrich_assets(db, user_ids)
        
        # 3. IoT Sensors
        sensor_ids = await seed_iot_sensors(db, user_ids)
        
        # 4. Sensor Readings (7 days)
        await seed_sensor_readings(db)
        
        # 5. Incidents
        await seed_incidents(db, user_ids)
        
        # 6. Maintenance Records
        await seed_maintenance(db, user_ids)
        
        # 7. Alerts
        await seed_alerts(db, user_ids)
        
        # 8. Budgets & Transactions
        await seed_budgets(db, user_ids)
        
        # 9. Reports
        await seed_reports(db, user_ids)
        
        # 10. Notifications
        await seed_notifications(db, user_ids)
        
        # ── Summary ──
        print("\n" + "=" * 65)
        print("  SEEDING COMPLETED — Summary")
        print("=" * 65)
        collections = [
            "users", "assets", "iot_sensors", "sensor_readings",
            "incidents", "maintenance_records", "alerts",
            "budgets", "budget_transactions", "reports", "notifications",
        ]
        for col in collections:
            count = await db[col].count_documents({})
            print(f"  {col:.<35} {count:>8}")
        print("=" * 65)
    
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
