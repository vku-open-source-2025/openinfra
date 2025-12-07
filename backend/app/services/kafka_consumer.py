"""
Kafka Consumer Service for IoT Sensor Data
Consumes messages from ESP8266 sensors via Kafka and stores in MongoDB
"""
import asyncio
import json
import os
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from aiokafka import AIOKafkaConsumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_IOT_TOPIC", "iot-sensor-data")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "openinfra-iot-consumer")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("DATABASE_NAME", os.getenv("MONGODB_DB", "gis_db"))


async def get_database():
    """Get MongoDB connection"""
    client = AsyncIOMotorClient(MONGODB_URL)
    return client[MONGODB_DB]


async def check_thresholds_and_alert(db, reading: dict):
    """Check if reading exceeds thresholds and create alerts"""
    sensor = await db["iot_sensors"].find_one({"sensor_id": reading["sensor_id"]})
    if not sensor or not sensor.get("config"):
        return
    
    thresholds = sensor["config"].get("thresholds", {})
    readings_data = reading.get("readings", {})
    
    # Check water level thresholds
    water_level = readings_data.get("water_level")
    if water_level is not None:
        if thresholds.get("critical_max") and water_level > thresholds["critical_max"]:
            alert = {
                "sensor_id": reading["sensor_id"],
                "asset_id": reading["asset_id"],
                "alert_type": "threshold_critical",
                "severity": "critical",
                "message": f"Water level CRITICAL: {water_level}m exceeds {thresholds['critical_max']}m",
                "value": water_level,
                "threshold": thresholds["critical_max"],
                "created_at": datetime.utcnow(),
                "acknowledged": False
            }
            await db["alerts"].insert_one(alert)
            logger.warning(f"CRITICAL ALERT: {alert['message']}")
        elif thresholds.get("max") and water_level > thresholds["max"]:
            alert = {
                "sensor_id": reading["sensor_id"],
                "asset_id": reading["asset_id"],
                "alert_type": "threshold_exceeded",
                "severity": "warning",
                "message": f"Water level WARNING: {water_level}m exceeds {thresholds['max']}m",
                "value": water_level,
                "threshold": thresholds["max"],
                "created_at": datetime.utcnow(),
                "acknowledged": False
            }
            await db["alerts"].insert_one(alert)
            logger.warning(f"WARNING ALERT: {alert['message']}")
    
    # Check battery
    battery = reading.get("battery")
    if battery is not None and battery < 20:
        alert = {
            "sensor_id": reading["sensor_id"],
            "asset_id": reading["asset_id"],
            "alert_type": "low_battery",
            "severity": "warning" if battery > 10 else "critical",
            "message": f"Low battery: {battery}%",
            "value": battery,
            "threshold": 20,
            "created_at": datetime.utcnow(),
            "acknowledged": False
        }
        await db["alerts"].insert_one(alert)
        logger.warning(f"BATTERY ALERT: {alert['message']}")


async def process_message(db, message_value: bytes):
    """Process a Kafka message and store in MongoDB"""
    try:
        data = json.loads(message_value.decode("utf-8"))
        sensor_code = data.get('sensor_id')
        logger.info(f"Processing message from sensor: {sensor_code}")
        
        # Validate required fields
        if not sensor_code or not data.get("asset_id"):
            logger.error("Missing required fields: sensor_id or asset_id")
            return
        
        # Lookup sensor by sensor_code to get the MongoDB ObjectId
        sensor = await db["iot_sensors"].find_one({"sensor_code": sensor_code})
        if sensor:
            # Use sensor's ObjectId as sensor_id for consistency with API
            actual_sensor_id = str(sensor["_id"])
            actual_asset_id = sensor.get("asset_id", data["asset_id"])
        else:
            # Fallback to the raw sensor_id if sensor not registered
            actual_sensor_id = sensor_code
            actual_asset_id = data["asset_id"]
            logger.warning(f"Sensor {sensor_code} not found in iot_sensors collection, using raw id")
        
        timestamp = datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.utcnow()
        readings_data = data.get("readings", {})
        
        # Determine the primary value and unit from readings
        # Support multiple reading types
        value = None
        unit = "m"  # default unit
        
        if "water_level" in readings_data:
            value = readings_data["water_level"]
            unit = "m"
        elif "temperature" in readings_data:
            value = readings_data["temperature"]
            unit = "°C"
        elif "humidity" in readings_data:
            value = readings_data["humidity"]
            unit = "%"
        elif "pressure" in readings_data:
            value = readings_data["pressure"]
            unit = "kPa"
        elif readings_data:
            # Use first available reading
            first_key = list(readings_data.keys())[0]
            value = readings_data[first_key]
            unit = ""
        
        if value is None:
            logger.warning(f"No reading value found in message: {data}")
            return
        
        # Prepare reading document in standard SensorReading format
        reading = {
            "sensor_id": actual_sensor_id,
            "asset_id": actual_asset_id,
            "timestamp": timestamp,
            "value": float(value),
            "unit": unit,
            "quality": "good",
            "quality_flags": [],
            "status": "normal",
            "threshold_exceeded": False,
            "metadata": {
                "readings": readings_data,
                "battery": data.get("battery"),
                "rssi": data.get("rssi"),
                **data.get("metadata", {})
            }
        }
        
        # Store reading
        result = await db["sensor_readings"].insert_one(reading)
        logger.info(f"Stored reading with ID: {result.inserted_id}")
        
        # Update sensor last_seen and last_reading (by sensor_code or _id)
        update_query = {"sensor_code": sensor_code} if sensor else {"_id": actual_sensor_id}
        await db["iot_sensors"].update_one(
            update_query,
            {"$set": {
                "last_seen": reading["timestamp"],
                "last_reading": reading["value"],
                "status": "online"
            }}
        )
        
        # Check thresholds and create alerts if needed
        await check_thresholds_and_alert(db, {
            **reading,
            "sensor_code": sensor_code,
            "readings": readings_data,
            "battery": data.get("battery")
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")


async def consume():
    """Main consumer loop"""
    logger.info(f"Starting Kafka consumer...")
    logger.info(f"Kafka servers: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Topic: {KAFKA_TOPIC}")
    logger.info(f"Group ID: {KAFKA_GROUP_ID}")
    
    db = await get_database()
    
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset="latest",
        value_deserializer=lambda x: x  # Keep as bytes, decode in process_message
    )
    
    try:
        await consumer.start()
        logger.info("Consumer started successfully")
        
        async for message in consumer:
            await process_message(db, message.value)
            
    except Exception as e:
        logger.error(f"Consumer error: {e}")
    finally:
        await consumer.stop()
        logger.info("Consumer stopped")


if __name__ == "__main__":
    asyncio.run(consume())
