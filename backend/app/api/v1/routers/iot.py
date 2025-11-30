"""IoT Sensors API router."""
from fastapi import APIRouter, Query, Depends, Body, HTTPException, status
from typing import List, Optional
from datetime import datetime
from app.domain.models.iot_sensor import IoTSensor, IoTSensorCreate, IoTSensorUpdate, SensorReading
from app.domain.services.iot_service import IoTService
from app.api.v1.dependencies import get_iot_service
from app.api.v1.middleware import get_current_user
from app.domain.models.user import User
from pydantic import BaseModel

router = APIRouter()


class SensorReadingRequest(BaseModel):
    """Sensor reading request schema."""
    timestamp: Optional[str] = None
    value: float
    metadata: Optional[dict] = None


class BatchIngestRequest(BaseModel):
    """Batch ingest request schema."""
    readings: List[dict]


@router.get("/sensors", response_model=List[IoTSensor])
async def list_sensors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    asset_id: Optional[str] = None,
    sensor_type: Optional[str] = None,
    status: Optional[str] = None,
    iot_service: IoTService = Depends(get_iot_service)
):
    """List IoT sensors."""
    return await iot_service.list_sensors(skip, limit, asset_id, sensor_type, status)


@router.post("/sensors", response_model=IoTSensor, status_code=status.HTTP_201_CREATED)
async def register_sensor(
    sensor_data: IoTSensorCreate,
    current_user: User = Depends(get_current_user),
    iot_service: IoTService = Depends(get_iot_service)
):
    """Register a new IoT sensor."""
    return await iot_service.register_sensor(sensor_data, created_by=str(current_user.id))


@router.get("/sensors/{sensor_id}", response_model=IoTSensor)
async def get_sensor(
    sensor_id: str,
    iot_service: IoTService = Depends(get_iot_service)
):
    """Get sensor details."""
    return await iot_service.get_sensor_by_id(sensor_id)


@router.put("/sensors/{sensor_id}", response_model=IoTSensor)
async def update_sensor(
    sensor_id: str,
    updates: IoTSensorUpdate,
    iot_service: IoTService = Depends(get_iot_service)
):
    """Update sensor configuration."""
    return await iot_service.update_sensor(sensor_id, updates)


@router.delete("/sensors/{sensor_id}")
async def delete_sensor(
    sensor_id: str,
    iot_service: IoTService = Depends(get_iot_service)
):
    """Remove sensor."""
    # Note: In production, you might want soft delete
    from app.domain.repositories.iot_repository import IoTSensorRepository
    # This would need to be implemented in the service
    return {"message": "Sensor deletion not yet implemented"}


@router.get("/sensors/{sensor_id}/data", response_model=List[SensorReading])
async def get_sensor_data(
    sensor_id: str,
    from_time: str = Query(..., description="ISO format datetime"),
    to_time: str = Query(..., description="ISO format datetime"),
    limit: int = Query(1000, ge=1, le=10000),
    iot_service: IoTService = Depends(get_iot_service)
):
    """Get sensor readings in time range."""
    from_time_dt = datetime.fromisoformat(from_time.replace('Z', '+00:00'))
    to_time_dt = datetime.fromisoformat(to_time.replace('Z', '+00:00'))
    return await iot_service.get_sensor_readings(sensor_id, from_time_dt, to_time_dt, limit)


@router.post("/sensors/{sensor_id}/data", response_model=SensorReading, status_code=status.HTTP_201_CREATED)
async def ingest_sensor_reading(
    sensor_id: str,
    reading: SensorReadingRequest,
    iot_service: IoTService = Depends(get_iot_service)
):
    """Ingest a sensor reading (API key auth for IoT devices)."""
    timestamp = None
    if reading.timestamp:
        timestamp = datetime.fromisoformat(reading.timestamp.replace('Z', '+00:00'))

    return await iot_service.ingest_sensor_reading(
        sensor_id,
        reading.value,
        timestamp,
        reading.metadata
    )


@router.post("/sensors/batch-ingest")
async def batch_ingest_readings(
    request: BatchIngestRequest,
    iot_service: IoTService = Depends(get_iot_service)
):
    """Batch ingest multiple sensor readings (MQTT gateway endpoint)."""
    result = await iot_service.batch_ingest_readings(request.readings)
    return result


@router.get("/sensors/{sensor_id}/status")
async def get_sensor_status(
    sensor_id: str,
    iot_service: IoTService = Depends(get_iot_service)
):
    """Get sensor health status."""
    sensor = await iot_service.get_sensor_by_id(sensor_id)
    return {
        "sensor_id": sensor_id,
        "status": sensor.status,
        "last_seen": sensor.last_seen.isoformat() if sensor.last_seen else None,
        "last_reading": sensor.last_reading
    }


@router.get("/sensors/{sensor_id}/statistics")
async def get_sensor_statistics(
    sensor_id: str,
    from_time: str = Query(..., description="ISO format datetime"),
    to_time: str = Query(..., description="ISO format datetime"),
    granularity: str = Query("hour", regex="^(minute|hour|day)$"),
    iot_service: IoTService = Depends(get_iot_service)
):
    """Get aggregated sensor statistics."""
    from_time_dt = datetime.fromisoformat(from_time.replace('Z', '+00:00'))
    to_time_dt = datetime.fromisoformat(to_time.replace('Z', '+00:00'))
    return await iot_service.get_sensor_statistics(sensor_id, from_time_dt, to_time_dt, granularity)
