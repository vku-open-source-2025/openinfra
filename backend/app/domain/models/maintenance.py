"""Maintenance domain model."""
from pydantic import BaseModel, Field, field_serializer, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum
from bson import ObjectId


class MaintenanceType(str, Enum):
    """Maintenance type enumeration."""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"
    EMERGENCY = "emergency"


class MaintenancePriority(str, Enum):
    """Maintenance priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MaintenanceStatus(str, Enum):
    """Maintenance status enumeration."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class RecurrencePattern(str, Enum):
    """Recurrence pattern enumeration."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class PartUsed(BaseModel):
    """Part used in maintenance value object."""
    part_name: str
    part_code: Optional[str] = None
    quantity: float
    unit_cost: Optional[float] = None
    total_cost: Optional[float] = None


class SafetyIncident(BaseModel):
    """Safety incident value object."""
    description: str
    severity: str  # "low" | "medium" | "high" | "critical"
    reported_at: datetime = Field(default_factory=datetime.utcnow)
    reported_by: str


class QualityCheck(BaseModel):
    """Quality check value object."""
    performed: bool = False
    passed: Optional[bool] = None
    checked_by: Optional[str] = None
    checked_at: Optional[datetime] = None
    notes: Optional[str] = None


class MaintenanceAttachment(BaseModel):
    """Maintenance attachment model."""
    file_name: str
    file_url: str
    file_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class Maintenance(BaseModel):
    """Maintenance record domain entity."""
    id: Optional[str] = Field(alias="_id", default=None)
    work_order_number: str
    asset_id: str

    # Work Order Details
    type: MaintenanceType
    priority: MaintenancePriority
    title: str
    description: str

    # Scheduling
    status: MaintenanceStatus = MaintenanceStatus.SCHEDULED
    scheduled_date: datetime
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    estimated_duration: int  # in minutes
    actual_duration: Optional[int] = None  # in minutes

    # Assignment
    assigned_to: Optional[str] = None
    assigned_team: List[str] = Field(default_factory=list)
    supervisor_id: Optional[str] = None

    # Execution Details
    work_performed: Optional[str] = None
    parts_used: List[PartUsed] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)

    # Financial
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    other_costs: Optional[float] = None
    total_cost: float = 0.0
    budget_id: Optional[str] = None

    # Quality & Safety
    quality_check: Optional[QualityCheck] = None
    safety_incidents: List[SafetyIncident] = Field(default_factory=list)

    # Documentation
    before_photos: List[str] = Field(default_factory=list)
    after_photos: List[str] = Field(default_factory=list)
    attachments: List[MaintenanceAttachment] = Field(default_factory=list)

    # Follow-up
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = None
    recurring: bool = False
    recurrence_pattern: Optional[RecurrencePattern] = None
    next_maintenance_date: Optional[datetime] = None

    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    completed_by: Optional[str] = None
    cancelled_by: Optional[str] = None
    cancellation_reason: Optional[str] = None

    # Analytics
    downtime_minutes: Optional[int] = None
    impact_assessment: Optional[str] = None

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


class MaintenanceCreate(BaseModel):
    """Maintenance creation schema."""
    asset_id: str
    type: MaintenanceType
    priority: MaintenancePriority
    title: str
    description: str
    scheduled_date: datetime
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    estimated_duration: int
    assigned_to: Optional[str] = None
    assigned_team: List[str] = Field(default_factory=list)
    supervisor_id: Optional[str] = None
    budget_id: Optional[str] = None
    recurring: bool = False
    recurrence_pattern: Optional[RecurrencePattern] = None
    follow_up_required: bool = False


class MaintenanceUpdate(BaseModel):
    """Maintenance update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[MaintenancePriority] = None
    scheduled_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    assigned_team: Optional[List[str]] = None
    status: Optional[MaintenanceStatus] = None


class MaintenanceStartRequest(BaseModel):
    """Maintenance start request schema."""
    actual_start_time: Optional[datetime] = None
    notes: Optional[str] = None


class MaintenanceCompleteRequest(BaseModel):
    """Maintenance completion request schema."""
    work_performed: str
    actual_end_time: Optional[datetime] = None
    parts_used: List[PartUsed] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    labor_cost: Optional[float] = None
    other_costs: Optional[float] = None
    quality_check: Optional[QualityCheck] = None
    follow_up_required: bool = False
    follow_up_notes: Optional[str] = None
    impact_assessment: Optional[str] = None
