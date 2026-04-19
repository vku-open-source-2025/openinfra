"""Geofence domain models."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer, field_validator

from app.domain.models.hazard_layer import HazardEventType, HazardSeverity


class Geofence(BaseModel):
    """Geofence configuration for hazard-based alerting."""

    id: Optional[str] = Field(
        validation_alias="_id",
        serialization_alias="id",
        default=None,
    )
    name: str
    description: Optional[str] = None
    polygon: Dict[str, Any]
    district: Optional[str] = None
    ward: Optional[str] = None
    min_severity: HazardSeverity = HazardSeverity.MEDIUM
    event_types: List[HazardEventType] = Field(default_factory=list)
    notification_channels: List[str] = Field(default_factory=lambda: ["in_app", "push"])
    target_roles: List[str] = Field(default_factory=lambda: ["admin", "technician"])
    is_active: bool = True
    created_by: Optional[str] = None
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


class GeofenceCreate(BaseModel):
    """Payload for creating geofences."""

    name: str = Field(min_length=3, max_length=140)
    description: Optional[str] = None
    polygon: Dict[str, Any]
    district: Optional[str] = None
    ward: Optional[str] = None
    min_severity: HazardSeverity = HazardSeverity.MEDIUM
    event_types: List[HazardEventType] = Field(default_factory=list)
    notification_channels: List[str] = Field(default_factory=lambda: ["in_app", "push"])
    target_roles: List[str] = Field(default_factory=lambda: ["admin", "technician"])
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GeofenceUpdate(BaseModel):
    """Payload for updating geofences."""

    name: Optional[str] = Field(default=None, min_length=3, max_length=140)
    description: Optional[str] = None
    polygon: Optional[Dict[str, Any]] = None
    district: Optional[str] = None
    ward: Optional[str] = None
    min_severity: Optional[HazardSeverity] = None
    event_types: Optional[List[HazardEventType]] = None
    notification_channels: Optional[List[str]] = None
    target_roles: Optional[List[str]] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
