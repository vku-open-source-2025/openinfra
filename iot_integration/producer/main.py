"""
IoT Producer Service
- Receives HTTP POST from ESP8266 sensors and publishes to Kafka
- Subscribes to MQTT broker and bridges messages to Kafka

Run: uvicorn main:app --host 0.0.0.0 --port 8001
"""
from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager
import json
import os
import logging
import asyncio

from aiokafka import AIOKafkaProducer
import aiomqtt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_IOT_TOPIC", "iot-sensor-data")
IOT_API_KEY = os.getenv("IOT_API_KEY", "")  # Optional API key for authentication

# MQTT Configuration
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "openinfra")
MQTT_PASS = os.getenv("MQTT_PASS", "OpenInfra2025!")
MQTT_TOPICS = os.getenv("MQTT_TOPICS", "openinfra/sensors/#")

# Global instances
producer: Optional[AIOKafkaProducer] = None
mqtt_task: Optional[asyncio.Task] = None

app = FastAPI(
    title="OpenInfra IoT Producer",
    description="Receives sensor data from ESP8266 devices via HTTP/MQTT and publishes to Kafka",
    version="1.1.0"
)


async def mqtt_subscriber():
    """
    MQTT Subscriber - bridges MQTT messages to Kafka
    Subscribes to openinfra/sensors/# topics
    """
    global producer
    
    while True:
        try:
            async with aiomqtt.Client(
                hostname=MQTT_HOST,
                port=MQTT_PORT,
                username=MQTT_USER,
                password=MQTT_PASS,
                identifier="openinfra-mqtt-kafka-bridge"
            ) as client:
                logger.info(f"MQTT connected to {MQTT_HOST}:{MQTT_PORT}")
                
                # Subscribe to sensor topics
                await client.subscribe(MQTT_TOPICS)
                logger.info(f"MQTT subscribed to: {MQTT_TOPICS}")
                
                async for message in client.messages:
                    try:
                        topic = str(message.topic)
                        payload = message.payload.decode('utf-8')
                        
                        logger.info(f"MQTT received [{topic}]: {payload[:100]}...")
                        
                        # Parse JSON payload
                        data = json.loads(payload)
                        
                        # Add metadata
                        data["mqtt_topic"] = topic
                        data["received_at"] = datetime.utcnow().isoformat()
                        data["source"] = "mqtt"
                        
                        # Ensure timestamp exists
                        if "timestamp" not in data or isinstance(data.get("timestamp"), int):
                            data["timestamp"] = datetime.utcnow().isoformat()
                        
                        # Publish to Kafka
                        if producer:
                            await producer.send_and_wait(KAFKA_TOPIC, data)
                            logger.info(f"Bridged MQTT→Kafka: sensor={data.get('sensor_id')}")
                        else:
                            logger.warning("Kafka producer not available, message dropped")
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON from MQTT: {e}")
                    except Exception as e:
                        logger.error(f"Error processing MQTT message: {e}")
                        
        except aiomqtt.MqttError as e:
            logger.error(f"MQTT connection error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"MQTT subscriber error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)


# Global producer instance
producer: Optional[AIOKafkaProducer] = None


class SensorReading(BaseModel):
    sensor_id: str
    asset_id: str
    timestamp: Optional[str] = None
    readings: Dict[str, Any] = {}
    battery: Optional[int] = None
    rssi: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    kafka_connected: bool
    mqtt_running: bool
    timestamp: str


@app.on_event("startup")
async def startup():
    """Initialize Kafka producer and MQTT subscriber on startup"""
    global producer, mqtt_task
    
    # Start Kafka producer
    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await producer.start()
        logger.info(f"Kafka producer started, connected to {KAFKA_BOOTSTRAP_SERVERS}")
    except Exception as e:
        logger.error(f"Failed to start Kafka producer: {e}")
        producer = None
    
    # Start MQTT subscriber in background
    mqtt_task = asyncio.create_task(mqtt_subscriber())
    logger.info("MQTT subscriber task started")


@app.on_event("shutdown")
async def shutdown():
    """Stop Kafka producer and MQTT subscriber on shutdown"""
    global producer, mqtt_task
    
    # Stop MQTT subscriber
    if mqtt_task:
        mqtt_task.cancel()
        try:
            await mqtt_task
        except asyncio.CancelledError:
            pass
        logger.info("MQTT subscriber stopped")
    
    # Stop Kafka producer
    if producer:
        await producer.stop()
        logger.info("Kafka producer stopped")


def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """Verify API key if configured"""
    if not IOT_API_KEY:
        return True  # No API key configured, allow all requests
    return x_api_key == IOT_API_KEY


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "kafka_connected": producer is not None,
        "mqtt_running": mqtt_task is not None and not mqtt_task.done(),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/iot/reading")
async def ingest_reading(
    reading: SensorReading,
    x_api_key: Optional[str] = Header(None)
):
    """
    Receive sensor reading from ESP8266 and publish to Kafka
    
    Expected payload:
    {
        "sensor_id": "drainage-sensor-001",
        "asset_id": "69298e9e3127bed87ace1a93",
        "readings": {
            "water_level": 0.45,
            "flow_rate": 1.2
        },
        "battery": 85,
        "rssi": -65,
        "metadata": {
            "firmware_version": "1.0.0"
        }
    }
    """
    # Verify API key
    if not verify_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check Kafka connection
    if not producer:
        logger.error("Kafka producer not available")
        raise HTTPException(status_code=503, detail="Kafka producer not available")
    
    # Prepare message
    message = {
        "sensor_id": reading.sensor_id,
        "asset_id": reading.asset_id,
        "timestamp": reading.timestamp or datetime.utcnow().isoformat(),
        "readings": reading.readings,
        "battery": reading.battery,
        "rssi": reading.rssi,
        "metadata": reading.metadata or {},
        "received_at": datetime.utcnow().isoformat()
    }
    
    try:
        # Publish to Kafka
        await producer.send_and_wait(KAFKA_TOPIC, message)
        logger.info(f"Published reading from sensor {reading.sensor_id}")
        
        return {
            "status": "accepted",
            "sensor_id": reading.sensor_id,
            "message_id": f"{reading.sensor_id}-{datetime.utcnow().timestamp()}"
        }
    except Exception as e:
        logger.error(f"Failed to publish to Kafka: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish message: {str(e)}")


@app.post("/api/iot/readings/batch")
async def ingest_readings_batch(
    readings: list[SensorReading],
    x_api_key: Optional[str] = Header(None)
):
    """
    Receive batch of sensor readings and publish to Kafka
    Useful for buffered uploads when connectivity is intermittent
    """
    if not verify_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if not producer:
        raise HTTPException(status_code=503, detail="Kafka producer not available")
    
    results = []
    for reading in readings:
        message = {
            "sensor_id": reading.sensor_id,
            "asset_id": reading.asset_id,
            "timestamp": reading.timestamp or datetime.utcnow().isoformat(),
            "readings": reading.readings,
            "battery": reading.battery,
            "rssi": reading.rssi,
            "metadata": reading.metadata or {},
            "received_at": datetime.utcnow().isoformat()
        }
        
        try:
            await producer.send_and_wait(KAFKA_TOPIC, message)
            results.append({"sensor_id": reading.sensor_id, "status": "accepted"})
        except Exception as e:
            results.append({"sensor_id": reading.sensor_id, "status": "failed", "error": str(e)})
    
    return {
        "total": len(readings),
        "accepted": sum(1 for r in results if r["status"] == "accepted"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "results": results
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
