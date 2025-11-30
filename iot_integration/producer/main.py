"""
IoT Producer Service
Receives HTTP POST from ESP8266 sensors and publishes to Kafka

Run: uvicorn main:app --host 0.0.0.0 --port 8001
"""
from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import json
import os
import logging

from aiokafka import AIOKafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_IOT_TOPIC", "iot-sensor-data")
IOT_API_KEY = os.getenv("IOT_API_KEY", "")  # Optional API key for authentication

app = FastAPI(
    title="OpenInfra IoT Producer",
    description="Receives sensor data from ESP8266 devices and publishes to Kafka",
    version="1.0.0"
)

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
    timestamp: str


@app.on_event("startup")
async def startup():
    """Initialize Kafka producer on startup"""
    global producer
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


@app.on_event("shutdown")
async def shutdown():
    """Stop Kafka producer on shutdown"""
    global producer
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
