"""Emergency operation plan domain models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer, field_validator


class EOPPlanStatus(str, Enum):
    """Lifecycle state for emergency operation plans."""

    DRAFT = "draft"
    REVIEW_PENDING = "review_pending"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class EOPAction(BaseModel):
    """A single executable action in an EOP plan."""

    action_id: str
    title: str
    description: Optional[str] = None
    phase: str = "response"
    priority: str = "medium"
    owner_role: Optional[str] = None
    estimated_minutes: Optional[int] = None
    dependencies: List[str] = Field(default_factory=list)


class EOPAssignment(BaseModel):
    """Assignment row for mapping actions to responders/resources."""

    action_id: str
    resource_unit_id: Optional[str] = None
    assignee_id: Optional[str] = None
    status: str = "pending"
    notes: Optional[str] = None


class EOPPlan(BaseModel):
    """Emergency operation plan aggregate."""

    id: Optional[str] = Field(
        validation_alias="_id", serialization_alias="id", default=None
    )
    emergency_event_id: str
    version: int = 1
    title: str
    summary: Optional[str] = None
    objectives: List[str] = Field(default_factory=list)
    operational_phases: List[str] = Field(default_factory=list)
    actions: List[EOPAction] = Field(default_factory=list)
    assignment_matrix: List[EOPAssignment] = Field(default_factory=list)
    evacuation_plan: List[str] = Field(default_factory=list)
    fallback_plan: List[str] = Field(default_factory=list)
    communications_plan: List[str] = Field(default_factory=list)
    status: EOPPlanStatus = EOPPlanStatus.DRAFT
    review_notes: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
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


class EOPPlanCreate(BaseModel):
    """Payload for creating an EOP plan."""

    emergency_event_id: str
    title: str = Field(min_length=3, max_length=200)
    summary: Optional[str] = None
    objectives: List[str] = Field(default_factory=list)
    operational_phases: List[str] = Field(default_factory=list)
    actions: List[EOPAction] = Field(default_factory=list)
    assignment_matrix: List[EOPAssignment] = Field(default_factory=list)
    evacuation_plan: List[str] = Field(default_factory=list)
    fallback_plan: List[str] = Field(default_factory=list)
    communications_plan: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EOPPlanUpdate(BaseModel):
    """Payload for updating an EOP plan."""

    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    summary: Optional[str] = None
    objectives: Optional[List[str]] = None
    operational_phases: Optional[List[str]] = None
    actions: Optional[List[EOPAction]] = None
    assignment_matrix: Optional[List[EOPAssignment]] = None
    evacuation_plan: Optional[List[str]] = None
    fallback_plan: Optional[List[str]] = None
    communications_plan: Optional[List[str]] = None
    review_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EOPGenerateRequest(BaseModel):
    """Payload for AI-assisted EOP draft generation."""

    emergency_event_id: str
    additional_context: Optional[str] = Field(default=None, max_length=4000)
    force_new_version: bool = True
