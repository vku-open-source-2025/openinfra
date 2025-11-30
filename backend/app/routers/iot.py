from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId

from app.db.mongodb import get_database
from app.models.iot import (
    Sensor, SensorCreate,
    SensorReading, SensorReadingCreate,
    Alert, AlertCreate,
    SensorStats, SensorReadingsList,
    AlertSeverity, AlertType
)

router = APIRouter()


# ==================== Sensors CRUD ====================

@router.get("/sensors", response_model=List[Sensor])
async def list_sensors(
    asset_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """List all sensors, optionally filtered by asset_id or status"""
    db = await get_database()
    query = {}
    if asset_id:
        query["asset_id"] = asset_id
    if status:
        query["status"] = status
    
    cursor = db["sensors"].find(query).skip(skip).limit(limit)
    sensors = await cursor.to_list(length=limit)
    return sensors


@router.get("/sensors/{sensor_id}", response_model=Sensor)
async def get_sensor(sensor_id: str):
    """Get sensor by sensor_id"""
    db = await get_database()
    sensor = await db["sensors"].find_one({"sensor_id": sensor_id})
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor


@router.post("/sensors", response_model=Sensor)
async def create_sensor(sensor: SensorCreate):
    """Create a new sensor"""
    db = await get_database()
    
    # Check if sensor_id already exists
    existing = await db["sensors"].find_one({"sensor_id": sensor.sensor_id})
    if existing:
        raise HTTPException(status_code=400, detail="Sensor ID already exists")
    
    # Check if asset exists
    asset = await db["assets"].find_one({"_id": ObjectId(sensor.asset_id)})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    sensor_dict = sensor.model_dump()
    sensor_dict["created_at"] = datetime.utcnow()
    sensor_dict["status"] = "active"
    sensor_dict["last_seen"] = None
    
    if sensor_dict.get("config") is None:
        sensor_dict["config"] = {
            "thresholds": {"min": 0, "max": 5, "critical_min": -0.5, "critical_max": 6},
            "sampling_interval": 60
        }
    
    result = await db["sensors"].insert_one(sensor_dict)
    sensor_dict["_id"] = result.inserted_id
    return sensor_dict


# ==================== Sensor Readings ====================

@router.get("/sensors/{sensor_id}/readings", response_model=SensorReadingsList)
async def get_sensor_readings(
    sensor_id: str,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    limit: int = Query(default=100, le=1000)
):
    """Get sensor readings with optional time range filter"""
    db = await get_database()
    
    # Verify sensor exists
    sensor = await db["sensors"].find_one({"sensor_id": sensor_id})
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    query = {"sensor_id": sensor_id}
    
    if from_time or to_time:
        query["timestamp"] = {}
        if from_time:
            query["timestamp"]["$gte"] = from_time
        if to_time:
            query["timestamp"]["$lte"] = to_time
    
    cursor = db["sensor_readings"].find(query).sort("timestamp", -1).limit(limit)
    readings = await cursor.to_list(length=limit)
    
    total_count = await db["sensor_readings"].count_documents(query)
    
    return {
        "sensor_id": sensor_id,
        "asset_id": sensor["asset_id"],
        "readings": readings,
        "total_count": total_count
    }


@router.post("/sensors/readings", response_model=SensorReading)
async def ingest_sensor_reading(reading: SensorReadingCreate):
    """Ingest a new sensor reading (used by Kafka consumer or direct POST)"""
    db = await get_database()
    
    reading_dict = reading.model_dump()
    reading_dict["timestamp"] = reading.timestamp or datetime.utcnow()
    
    # Update sensor last_seen
    await db["sensors"].update_one(
        {"sensor_id": reading.sensor_id},
        {"$set": {"last_seen": reading_dict["timestamp"]}}
    )
    
    # Insert reading
    result = await db["sensor_readings"].insert_one(reading_dict)
    reading_dict["_id"] = result.inserted_id
    
    # Check thresholds and create alerts if needed
    await check_thresholds_and_alert(db, reading_dict)
    
    return reading_dict


async def check_thresholds_and_alert(db, reading: dict):
    """Check if reading exceeds thresholds and create alerts"""
    sensor = await db["sensors"].find_one({"sensor_id": reading["sensor_id"]})
    if not sensor or not sensor.get("config"):
        return
    
    thresholds = sensor["config"].get("thresholds", {})
    readings_data = reading.get("readings", {})
    
    # Check water level thresholds
    water_level = readings_data.get("water_level")
    if water_level is not None:
        if thresholds.get("critical_max") and water_level > thresholds["critical_max"]:
            await create_alert_internal(db, {
                "sensor_id": reading["sensor_id"],
                "asset_id": reading["asset_id"],
                "alert_type": AlertType.THRESHOLD_CRITICAL,
                "severity": AlertSeverity.CRITICAL,
                "message": f"Water level CRITICAL: {water_level}m exceeds {thresholds['critical_max']}m",
                "value": water_level,
                "threshold": thresholds["critical_max"]
            })
        elif thresholds.get("max") and water_level > thresholds["max"]:
            await create_alert_internal(db, {
                "sensor_id": reading["sensor_id"],
                "asset_id": reading["asset_id"],
                "alert_type": AlertType.THRESHOLD_EXCEEDED,
                "severity": AlertSeverity.WARNING,
                "message": f"Water level WARNING: {water_level}m exceeds {thresholds['max']}m",
                "value": water_level,
                "threshold": thresholds["max"]
            })
    
    # Check battery
    battery = reading.get("battery")
    if battery is not None and battery < 20:
        await create_alert_internal(db, {
            "sensor_id": reading["sensor_id"],
            "asset_id": reading["asset_id"],
            "alert_type": AlertType.LOW_BATTERY,
            "severity": AlertSeverity.WARNING if battery > 10 else AlertSeverity.CRITICAL,
            "message": f"Low battery: {battery}%",
            "value": battery,
            "threshold": 20
        })


async def create_alert_internal(db, alert_data: dict):
    """Internal function to create an alert"""
    alert_data["created_at"] = datetime.utcnow()
    alert_data["acknowledged"] = False
    await db["alerts"].insert_one(alert_data)


# ==================== Statistics ====================

@router.get("/sensors/{sensor_id}/stats", response_model=SensorStats)
async def get_sensor_stats(
    sensor_id: str,
    period: str = Query(default="hourly", regex="^(hourly|daily)$"),
    hours: int = Query(default=24, le=168)  # max 7 days
):
    """Get aggregated statistics for a sensor"""
    db = await get_database()
    
    sensor = await db["sensors"].find_one({"sensor_id": sensor_id})
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    pipeline = [
        {
            "$match": {
                "sensor_id": sensor_id,
                "timestamp": {"$gte": start_time, "$lte": end_time}
            }
        },
        {
            "$group": {
                "_id": None,
                "readings_count": {"$sum": 1},
                "avg_water_level": {"$avg": "$readings.water_level"},
                "min_water_level": {"$min": "$readings.water_level"},
                "max_water_level": {"$max": "$readings.water_level"},
                "avg_flow_rate": {"$avg": "$readings.flow_rate"}
            }
        }
    ]
    
    result = await db["sensor_readings"].aggregate(pipeline).to_list(length=1)
    
    if result:
        stats = result[0]
    else:
        stats = {
            "readings_count": 0,
            "avg_water_level": None,
            "min_water_level": None,
            "max_water_level": None,
            "avg_flow_rate": None
        }
    
    return {
        "sensor_id": sensor_id,
        "asset_id": sensor["asset_id"],
        "period": period,
        "start_time": start_time,
        "end_time": end_time,
        **stats
    }


# ==================== Alerts ====================

@router.get("/alerts", response_model=List[Alert])
async def list_alerts(
    sensor_id: Optional[str] = None,
    asset_id: Optional[str] = None,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
):
    """List alerts with optional filters"""
    db = await get_database()
    query = {}
    
    if sensor_id:
        query["sensor_id"] = sensor_id
    if asset_id:
        query["asset_id"] = asset_id
    if severity:
        query["severity"] = severity
    if acknowledged is not None:
        query["acknowledged"] = acknowledged
    
    cursor = db["alerts"].find(query).sort("created_at", -1).skip(skip).limit(limit)
    alerts = await cursor.to_list(length=limit)
    return alerts


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, acknowledged_by: str = "admin"):
    """Acknowledge an alert"""
    db = await get_database()
    
    result = await db["alerts"].update_one(
        {"_id": ObjectId(alert_id)},
        {
            "$set": {
                "acknowledged": True,
                "acknowledged_by": acknowledged_by,
                "acknowledged_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"message": "Alert acknowledged"}


# ==================== Asset IoT Data ====================

@router.get("/assets/{asset_id}/iot-data")
async def get_asset_iot_data(
    asset_id: str,
    hours: int = Query(default=24, le=168)
):
    """Get all IoT data for an asset (sensors, readings, alerts)"""
    db = await get_database()
    
    # Verify asset exists
    asset = await db["assets"].find_one({"_id": ObjectId(asset_id)})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Get sensors for this asset
    sensors = await db["sensors"].find({"asset_id": asset_id}).to_list(length=100)
    
    # Get recent readings
    start_time = datetime.utcnow() - timedelta(hours=hours)
    readings = await db["sensor_readings"].find({
        "asset_id": asset_id,
        "timestamp": {"$gte": start_time}
    }).sort("timestamp", -1).to_list(length=1000)
    
    # Get active alerts
    alerts = await db["alerts"].find({
        "asset_id": asset_id,
        "acknowledged": False
    }).sort("created_at", -1).to_list(length=100)
    
    return {
        "asset_id": asset_id,
        "asset": {
            "id": str(asset["_id"]),
            "feature_type": asset.get("feature_type"),
            "feature_code": asset.get("feature_code"),
            "geometry": asset.get("geometry")
        },
        "sensors": [
            {**s, "_id": str(s["_id"])} for s in sensors
        ],
        "readings": [
            {**r, "_id": str(r["_id"]), "timestamp": r["timestamp"].isoformat()} for r in readings
        ],
        "alerts": [
            {**a, "_id": str(a["_id"]), "created_at": a["created_at"].isoformat()} for a in alerts
        ],
        "summary": {
            "total_sensors": len(sensors),
            "total_readings": len(readings),
            "active_alerts": len(alerts)
        }
    }
