"""Situation report (SITREP) domain models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer, field_validator


class SitrepStatus(str, Enum):
    """Lifecycle state of a situation report."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SitrepDelta(BaseModel):
    """Single timeline delta entry in SITREP."""

    actor_id: Optional[str] = None
    action_type: str
    changes: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Sitrep(BaseModel):
    """Situation report aggregate."""

    id: Optional[str] = Field(
        validation_alias="_id", serialization_alias="id", default=None
    )
    emergency_event_id: str
    title: str
    snapshot: Dict[str, Any] = Field(default_factory=dict)
    deltas: List[SitrepDelta] = Field(default_factory=list)
    status: SitrepStatus = SitrepStatus.DRAFT
    published_by: Optional[str] = None
    published_at: Optional[datetime] = None
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


class SitrepCreate(BaseModel):
    """Payload for creating a SITREP."""

    emergency_event_id: str
    title: str = Field(min_length=3, max_length=200)
    snapshot: Dict[str, Any] = Field(default_factory=dict)
    deltas: List[SitrepDelta] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SitrepUpdate(BaseModel):
    """Payload for updating a SITREP."""

    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    snapshot: Optional[Dict[str, Any]] = None
    status: Optional[SitrepStatus] = None
    metadata: Optional[Dict[str, Any]] = None
