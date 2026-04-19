"""Emergency SLA breach domain model."""

from datetime import datetime
from typing import Any, Dict, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer, field_validator


class SLABreachRecord(BaseModel):
    """SLA breach record for emergency event monitoring."""

    id: Optional[str] = Field(
        validation_alias="_id",
        serialization_alias="id",
        default=None,
    )
    event_id: str
    event_code: Optional[str] = None
    severity: str
    threshold_minutes: int
    active_minutes: int
    status: str
    breached_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

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
