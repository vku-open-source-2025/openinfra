from pydantic import BaseModel, Field, field_serializer
from typing import Any, Dict, List, Optional
from datetime import datetime
from bson import ObjectId
from enum import Enum


class SensorType(str, Enum):
    WATER_LEVEL = "water_level"
    FLOW_RATE = "flow_rate"
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"


class SensorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, Enum):
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    THRESHOLD_CRITICAL = "threshold_critical"
    SENSOR_OFFLINE = "sensor_offline"
    LOW_BATTERY = "low_battery"
    RAPID_CHANGE = "rapid_change"


# ==================== Sensor Models ====================

class SensorThresholds(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    critical_min: Optional[float] = None
    critical_max: Optional[float] = None


class SensorConfig(BaseModel):
    thresholds: SensorThresholds = Field(default_factory=SensorThresholds)
    sampling_interval: int = 60  # seconds


class SensorBase(BaseModel):
    sensor_id: str
    asset_id: str  # Reference to assets collection
    sensor_type: SensorType
    location: Optional[Dict[str, Any]] = None  # GeoJSON Point
    config: SensorConfig = Field(default_factory=SensorConfig)
    status: SensorStatus = SensorStatus.ACTIVE
    last_seen: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SensorCreate(BaseModel):
    sensor_id: str
    asset_id: str
    sensor_type: SensorType
    location: Optional[Dict[str, Any]] = None
    config: Optional[SensorConfig] = None


class Sensor(SensorBase):
    id: Any = Field(alias="_id")

    @field_serializer('id')
    def serialize_id(self, value: Any, _info):
        return str(value)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


# ==================== Sensor Reading Models ====================

class SensorReadings(BaseModel):
    water_level: Optional[float] = None  # meters
    flow_rate: Optional[float] = None  # liters/second
    pressure: Optional[float] = None  # bar
    temperature: Optional[float] = None  # celsius
    humidity: Optional[float] = None  # percentage


class SensorReadingBase(BaseModel):
    sensor_id: str
    asset_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    readings: SensorReadings
    battery: Optional[float] = None  # percentage
    signal_strength: Optional[int] = None  # dBm


class SensorReadingCreate(BaseModel):
    sensor_id: str
    asset_id: str
    readings: SensorReadings
    battery: Optional[float] = None
    signal_strength: Optional[int] = None
    timestamp: Optional[datetime] = None


class SensorReading(SensorReadingBase):
    id: Any = Field(alias="_id")

    @field_serializer('id')
    def serialize_id(self, value: Any, _info):
        return str(value)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


# ==================== Alert Models ====================

class AlertBase(BaseModel):
    sensor_id: str
    asset_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class AlertCreate(BaseModel):
    sensor_id: str
    asset_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None


class Alert(AlertBase):
    id: Any = Field(alias="_id")

    @field_serializer('id')
    def serialize_id(self, value: Any, _info):
        return str(value)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


# ==================== Kafka Message Models ====================

class IoTKafkaMessage(BaseModel):
    """Message format from ESP8266 via Kafka"""
    sensor_id: str
    asset_id: str
    timestamp: Optional[str] = None
    readings: Dict[str, float]
    battery: Optional[float] = None
    signal_strength: Optional[int] = None
    api_key: str


# ==================== API Response Models ====================

class SensorStats(BaseModel):
    sensor_id: str
    asset_id: str
    period: str  # hourly, daily
    start_time: datetime
    end_time: datetime
    readings_count: int
    avg_water_level: Optional[float] = None
    min_water_level: Optional[float] = None
    max_water_level: Optional[float] = None
    avg_flow_rate: Optional[float] = None


class SensorReadingsList(BaseModel):
    sensor_id: str
    asset_id: str
    readings: List[SensorReading]
    total_count: int
