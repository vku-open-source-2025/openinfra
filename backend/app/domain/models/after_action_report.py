"""After-action report domain models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer, field_validator


class AfterActionStatus(str, Enum):
    """Lifecycle state of after-action reports."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AfterActionTimelineEntry(BaseModel):
    """One timeline entry in after-action report."""

    timestamp: datetime
    source: str
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)


class AfterActionKPI(BaseModel):
    """Computed KPI values for post-incident evaluation."""

    response_time_minutes: Optional[float] = None
    response_speed_score: float = 0.0
    dispatch_completion_rate: float = 0.0
    sitrep_coverage_rate: float = 0.0
    resource_efficiency_score: float = 0.0
    overall_score: float = 0.0


class AfterActionReport(BaseModel):
    """After-action report aggregate."""

    id: Optional[str] = Field(
        validation_alias="_id",
        serialization_alias="id",
        default=None,
    )
    report_code: str
    emergency_event_id: str
    title: str
    summary: str
    status: AfterActionStatus = AfterActionStatus.DRAFT
    timeline: List[AfterActionTimelineEntry] = Field(default_factory=list)
    kpi: AfterActionKPI = Field(default_factory=AfterActionKPI)
    lessons_learned: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    generated_by: Optional[str] = None
    published_by: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
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


class AfterActionGenerateRequest(BaseModel):
    """Payload for generating after-action report."""

    emergency_event_id: str
    title: Optional[str] = Field(default=None, min_length=5, max_length=240)
    summary_override: Optional[str] = None
    lessons_learned: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    force_regenerate: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AfterActionReportUpdate(BaseModel):
    """Payload for updating draft after-action report."""

    title: Optional[str] = Field(default=None, min_length=5, max_length=240)
    summary: Optional[str] = None
    lessons_learned: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    status: Optional[AfterActionStatus] = None
    metadata: Optional[Dict[str, Any]] = None
