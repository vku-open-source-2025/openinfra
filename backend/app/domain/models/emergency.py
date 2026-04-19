"""Emergency domain models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer, field_validator


class EmergencyEventType(str, Enum):
    """Emergency event type."""

    FLOOD = "flood"
    STORM = "storm"
    LANDSLIDE = "landslide"
    FIRE = "fire"
    EARTHQUAKE = "earthquake"
    OUTAGE = "outage"
    POLLUTION = "pollution"
    OTHER = "other"


class EmergencySeverity(str, Enum):
    """Emergency severity level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EmergencyStatus(str, Enum):
    """Emergency event lifecycle state."""

    MONITORING = "monitoring"
    ACTIVE = "active"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CANCELED = "canceled"


class EmergencySource(str, Enum):
    """Source of emergency signal."""

    MANUAL = "manual"
    IOT = "iot"
    FORECAST = "forecast"
    SOSCONN = "sosconn"
    OTHER = "other"


class EmergencyLocation(BaseModel):
    """Location payload for an emergency event."""

    geometry: Optional[dict] = None
    address: Optional[str] = None
    ward: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None


class EOPAction(BaseModel):
    """A single draft action in an EOP plan."""

    objective: str
    owner: Optional[str] = None
    eta_minutes: Optional[int] = None
    resources: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class EOPDraftStatus(str, Enum):
    """EOP draft status."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class EOPDraft(BaseModel):
    """Draft emergency operation plan."""

    id: Optional[str] = Field(
        validation_alias="_id", serialization_alias="id", default=None
    )
    event_id: str
    assumptions: List[str] = Field(default_factory=list)
    actions: List[EOPAction] = Field(default_factory=list)
    status: EOPDraftStatus = EOPDraftStatus.DRAFT
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value: Any):
        if isinstance(value, ObjectId):
            return str(value)
        return value

    @field_serializer("id")
    def serialize_id(self, value: Any, _info):
        if value is None:
            return None
        return str(value)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class EmergencyEvent(BaseModel):
    """Emergency event entity."""

    id: Optional[str] = Field(
        validation_alias="_id", serialization_alias="id", default=None
    )
    event_code: Optional[str] = None
    title: str
    description: Optional[str] = None
    event_type: EmergencyEventType
    severity: EmergencySeverity
    status: EmergencyStatus = EmergencyStatus.MONITORING
    source: EmergencySource = EmergencySource.MANUAL
    location: Optional[EmergencyLocation] = None
    affected_asset_ids: List[str] = Field(default_factory=list)
    affected_area_km2: Optional[float] = None
    estimated_impact: Dict[str, Any] = Field(default_factory=dict)
    instructions: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("id", mode="before")
    @classmethod
    def validate_id(cls, value: Any):
        if isinstance(value, ObjectId):
            return str(value)
        return value

    @field_serializer("id")
    def serialize_id(self, value: Any, _info):
        if value is None:
            return None
        return str(value)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class EmergencyEventCreate(BaseModel):
    """Request schema for creating emergency events."""

    title: str = Field(min_length=3, max_length=200)
    description: Optional[str] = None
    event_type: EmergencyEventType
    severity: EmergencySeverity
    source: EmergencySource = EmergencySource.MANUAL
    location: Optional[EmergencyLocation] = None
    affected_asset_ids: List[str] = Field(default_factory=list)
    affected_area_km2: Optional[float] = None
    estimated_impact: Dict[str, Any] = Field(default_factory=dict)
    instructions: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EmergencyEventUpdate(BaseModel):
    """Request schema for updating emergency events."""

    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = None
    event_type: Optional[EmergencyEventType] = None
    severity: Optional[EmergencySeverity] = None
    status: Optional[EmergencyStatus] = None
    source: Optional[EmergencySource] = None
    location: Optional[EmergencyLocation] = None
    affected_asset_ids: Optional[List[str]] = None
    affected_area_km2: Optional[float] = None
    estimated_impact: Optional[Dict[str, Any]] = None
    instructions: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
