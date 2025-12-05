"""IoT Sensor domain model."""
from pydantic import BaseModel, Field, field_serializer, field_validator
from typing import Optional, List, Any, Dict, Union
from datetime import datetime
from enum import Enum
from bson import ObjectId


class SensorType(str, Enum):
    """Sensor type enumeration."""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    VIBRATION = "vibration"
    POWER = "power"
    VOLTAGE = "voltage"
    CURRENT = "current"
    FLOW_RATE = "flow_rate"
    WATER_LEVEL = "water_level"
    AIR_QUALITY = "air_quality"
    CUSTOM = "custom"


class SensorStatus(str, Enum):
    """Sensor status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class ConnectionType(str, Enum):
    """Connection type enumeration."""
    WIFI = "wifi"
    LORA = "lora"
    CELLULAR = "cellular"
    ZIGBEE = "zigbee"
    BLUETOOTH = "bluetooth"


class SensorThresholds(BaseModel):
    """Sensor thresholds value object."""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    critical_min: Optional[float] = None
    critical_max: Optional[float] = None
    warning_min: Optional[float] = None
    warning_max: Optional[float] = None


class IoTSensor(BaseModel):
    """IoT Sensor domain entity."""
    id: Optional[str] = Field(validation_alias="_id", serialization_alias="id", default=None)
    sensor_code: str
    asset_id: str

    # Sensor Details
    sensor_type: SensorType
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None

    # Configuration
    measurement_unit: str  # "°C" | "%" | "kPa" | "Hz" | "kW"
    sample_rate: int  # seconds between readings
    thresholds: Optional[SensorThresholds] = None

    # Connectivity
    connection_type: ConnectionType = ConnectionType.WIFI
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    gateway_id: Optional[str] = None

    # Status
    status: SensorStatus = SensorStatus.OFFLINE
    last_seen: Optional[datetime] = None
    last_reading: Optional[Union[float, int, Dict[str, Any]]] = None

    # Calibration
    calibration_date: Optional[datetime] = None
    calibration_due: Optional[datetime] = None
    calibration_factor: Optional[float] = None

    # Installation
    installed_at: Optional[datetime] = None
    installed_by: Optional[str] = None
    location_description: Optional[str] = None

    # Maintenance
    maintenance_schedule: Optional[str] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None

    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    # Metadata
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, v: Any):
        """Convert ObjectId to string."""
        if isinstance(v, ObjectId):
            return str(v)
        return v

    @field_serializer("id")
    def serialize_id(self, value: Any, _info):
        if value is None:
            return None
        return str(value)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class SensorReading(BaseModel):
    """Sensor reading model."""
    id: Optional[str] = Field(validation_alias="_id", serialization_alias="id", default=None)
    sensor_id: str
    asset_id: str

    # Reading
    timestamp: datetime
    value: float
    unit: str

    # Quality
    quality: str = "good"  # "good" | "suspect" | "bad"
    quality_flags: List[str] = Field(default_factory=list)

    # Analysis
    status: str = "normal"  # "normal" | "warning" | "critical"
    threshold_exceeded: bool = False

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IoTSensorCreate(BaseModel):
    """IoT Sensor creation schema."""
    sensor_code: str
    asset_id: str
    sensor_type: SensorType
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    measurement_unit: str
    sample_rate: int = 60
    thresholds: Optional[SensorThresholds] = None
    connection_type: ConnectionType = ConnectionType.WIFI
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    gateway_id: Optional[str] = None
    location_description: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class IoTSensorUpdate(BaseModel):
    """IoT Sensor update schema."""
    sensor_type: Optional[SensorType] = None
    measurement_unit: Optional[str] = None
    sample_rate: Optional[int] = None
    thresholds: Optional[SensorThresholds] = None
    connection_type: Optional[ConnectionType] = None
    ip_address: Optional[str] = None
    status: Optional[SensorStatus] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
