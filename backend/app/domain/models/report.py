"""Report domain model."""
from pydantic import BaseModel, Field, field_serializer, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum
from bson import ObjectId


class ReportType(str, Enum):
    """Report type enumeration."""
    MAINTENANCE_SUMMARY = "maintenance_summary"
    ASSET_INVENTORY = "asset_inventory"
    INCIDENT_REPORT = "incident_report"
    BUDGET_UTILIZATION = "budget_utilization"
    IOT_SENSOR_DATA = "iot_sensor_data"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Report format enumeration."""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class ReportStatus(str, Enum):
    """Report status enumeration."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class Report(BaseModel):
    """Report domain entity."""
    id: Optional[str] = Field(alias="_id", default=None)
    report_code: str

    # Report Details
    type: ReportType
    name: str
    description: Optional[str] = None

    # Parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)  # Filters, date ranges, etc.

    # Output
    format: ReportFormat = ReportFormat.PDF
    file_url: Optional[str] = None
    file_size: Optional[int] = None

    # Status
    status: ReportStatus = ReportStatus.PENDING
    generated_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # Scheduling
    scheduled: bool = False
    schedule_pattern: Optional[str] = None  # Cron expression
    next_run: Optional[datetime] = None

    # Recipients
    recipients: List[str] = Field(default_factory=list)  # User IDs

    # Expiration
    expires_at: Optional[datetime] = None

    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

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


class ReportCreate(BaseModel):
    """Report creation schema."""
    type: ReportType
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    format: ReportFormat = ReportFormat.PDF
    recipients: List[str] = Field(default_factory=list)
    scheduled: bool = False
    schedule_pattern: Optional[str] = None
