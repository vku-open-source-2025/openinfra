"""Hazard layer domain models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer, field_validator


class HazardEventType(str, Enum):
    """Supported hazard event types."""

    FLOOD = "flood"
    STORM = "storm"
    LANDSLIDE = "landslide"
    FIRE = "fire"
    EARTHQUAKE = "earthquake"
    OUTAGE = "outage"
    POLLUTION = "pollution"
    DROUGHT = "drought"
    OTHER = "other"


class HazardSeverity(str, Enum):
    """Hazard severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HazardSource(str, Enum):
    """Source of hazard signal."""

    NCHMF = "nchmf"
    VNDMS = "vndms"
    IOT = "iot"
    MANUAL = "manual"
    OTHER = "other"


class HazardLayer(BaseModel):
    """Hazard layer entity for map and command-center workflows."""

    id: Optional[str] = Field(
        validation_alias="_id",
        serialization_alias="id",
        default=None,
    )
    hazard_id: str
    title: str
    description: Optional[str] = None
    event_type: HazardEventType
    severity: HazardSeverity
    source: HazardSource
    geometry: Optional[Dict[str, Any]] = None
    affected_polygon: Optional[Dict[str, Any]] = None
    intensity_level: Optional[float] = None
    forecast_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    affected_population: Optional[int] = Field(default=None, ge=0)
    district: Optional[str] = None
    ward: Optional[str] = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    ingest_timestamp: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    vector_embedding: Optional[List[float]] = None
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


class HazardLayerCreate(BaseModel):
    """Payload for manual hazard creation."""

    hazard_id: str
    title: str = Field(min_length=3, max_length=300)
    description: Optional[str] = None
    event_type: HazardEventType
    severity: HazardSeverity
    source: HazardSource = HazardSource.MANUAL
    geometry: Optional[Dict[str, Any]] = None
    affected_polygon: Optional[Dict[str, Any]] = None
    intensity_level: Optional[float] = None
    forecast_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    affected_population: Optional[int] = Field(default=None, ge=0)
    district: Optional[str] = None
    ward: Optional[str] = None
    detected_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HazardLayerUpdate(BaseModel):
    """Payload for hazard updates."""

    title: Optional[str] = Field(default=None, min_length=3, max_length=300)
    description: Optional[str] = None
    event_type: Optional[HazardEventType] = None
    severity: Optional[HazardSeverity] = None
    geometry: Optional[Dict[str, Any]] = None
    affected_polygon: Optional[Dict[str, Any]] = None
    intensity_level: Optional[float] = None
    forecast_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    affected_population: Optional[int] = Field(default=None, ge=0)
    district: Optional[str] = None
    ward: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
