"""Alert domain model."""
from pydantic import BaseModel, Field, field_serializer, field_validator
from typing import Optional, Any, List, Dict
from datetime import datetime
from enum import Enum
from bson import ObjectId


class AlertSeverity(str, Enum):
    """Alert severity enumeration."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(str, Enum):
    """Alert status enumeration."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class AlertSourceType(str, Enum):
    """Alert source type."""
    SENSOR = "sensor"
    SYSTEM = "system"
    MANUAL = "manual"


class Alert(BaseModel):
    """Alert domain entity."""
    id: Optional[str] = Field(alias="_id", default=None)
    alert_code: str

    # Source
    source_type: AlertSourceType
    sensor_id: Optional[str] = None
    asset_id: Optional[str] = None

    # Alert Details
    type: str  # "threshold_exceeded" | "sensor_offline" | "maintenance_due" | "custom"
    severity: AlertSeverity
    title: str
    message: str

    # Trigger Conditions
    trigger_value: Optional[float] = None
    threshold_value: Optional[float] = None
    condition: Optional[str] = None  # "greater_than" | "less_than" | "equals"

    # Status
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None

    # Actions Taken
    incident_created: bool = False
    incident_id: Optional[str] = None
    maintenance_created: bool = False
    maintenance_id: Optional[str] = None

    # Notifications
    notifications_sent: List[Dict[str, Any]] = Field(default_factory=list)

    # Tracking
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    auto_created: bool = True

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
