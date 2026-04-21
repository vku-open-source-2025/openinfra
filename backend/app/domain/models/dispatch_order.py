"""Dispatch order domain models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer, field_validator


class DispatchPriority(str, Enum):
    """Priority levels for dispatch orders."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DispatchStatus(str, Enum):
    """Lifecycle state of dispatch orders."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    ON_SCENE = "on_scene"
    COMPLETED = "completed"
    REASSIGNED = "reassigned"
    CANCELED = "canceled"


class DispatchAssignment(BaseModel):
    """Resource assignment for dispatch execution."""

    resource_unit_id: Optional[str] = None
    assigned_user_id: Optional[str] = None
    role: Optional[str] = None
    quantity: float = 1.0
    notes: Optional[str] = None


class DispatchOrder(BaseModel):
    """Dispatch order aggregate."""

    id: Optional[str] = Field(
        validation_alias="_id", serialization_alias="id", default=None
    )
    emergency_event_id: str
    eop_plan_id: Optional[str] = None
    task_title: str
    task_description: Optional[str] = None
    target_location: Optional[dict] = None
    priority: DispatchPriority = DispatchPriority.MEDIUM
    status: DispatchStatus = DispatchStatus.PENDING
    assignments: List[DispatchAssignment] = Field(default_factory=list)
    assigned_user_id: Optional[str] = None
    eta_minutes: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_by: Optional[str] = None
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


class DispatchOrderCreate(BaseModel):
    """Payload for creating dispatch orders."""

    emergency_event_id: str
    eop_plan_id: Optional[str] = None
    task_title: str = Field(min_length=3, max_length=200)
    task_description: Optional[str] = None
    target_location: Optional[dict] = None
    priority: DispatchPriority = DispatchPriority.MEDIUM
    assignments: List[DispatchAssignment] = Field(default_factory=list)
    eta_minutes: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DispatchOrderUpdate(BaseModel):
    """Payload for updating dispatch orders."""

    task_title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    task_description: Optional[str] = None
    target_location: Optional[dict] = None
    priority: Optional[DispatchPriority] = None
    status: Optional[DispatchStatus] = None
    assignments: Optional[List[DispatchAssignment]] = None
    eta_minutes: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
