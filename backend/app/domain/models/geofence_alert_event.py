"""Geofence alert event model."""

from datetime import datetime
from typing import Any, Dict, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer, field_validator


class GeofenceAlertEvent(BaseModel):
    """Audit event generated when hazard triggers geofence alert."""

    id: Optional[str] = Field(
        validation_alias="_id",
        serialization_alias="id",
        default=None,
    )
    geofence_id: str
    hazard_layer_id: str
    severity: str
    event_type: str
    title: str
    message: str
    notification_stats: Dict[str, int] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

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
