"""Incident domain model."""
from pydantic import BaseModel, Field, field_serializer, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum
from bson import ObjectId
from app.domain.value_objects.coordinates import Coordinates


class IncidentCategory(str, Enum):
    """Incident category enumeration."""
    DAMAGE = "damage"
    MALFUNCTION = "malfunction"
    SAFETY_HAZARD = "safety_hazard"
    VANDALISM = "vandalism"
    OTHER = "other"


class IncidentSeverity(str, Enum):
    """Incident severity enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Incident status enumeration."""
    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ReporterType(str, Enum):
    """Reporter type enumeration."""
    CITIZEN = "citizen"
    TECHNICIAN = "technician"
    ADMIN = "admin"
    SYSTEM = "system"


class ResolutionType(str, Enum):
    """Resolution type enumeration."""
    FIXED = "fixed"
    DUPLICATE = "duplicate"
    NOT_AN_ISSUE = "not_an_issue"
    TRANSFERRED = "transferred"


class IncidentComment(BaseModel):
    """Incident comment model."""
    user_id: Optional[str] = None
    comment: str
    posted_at: datetime = Field(default_factory=datetime.utcnow)
    is_internal: bool = False  # Internal staff notes vs public comments


class IncidentAttachment(BaseModel):
    """Incident attachment model."""
    file_name: str
    file_url: str
    file_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class IncidentLocation(BaseModel):
    """Incident location value object."""
    geometry: Dict[str, Any]  # GeoJSON format
    address: Optional[str] = None
    description: Optional[str] = None


class ReporterContact(BaseModel):
    """Reporter contact information."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class AssetSummary(BaseModel):
    """Embedded asset summary for incident responses."""
    id: str
    asset_code: Optional[str] = None
    name: Optional[str] = None
    feature_type: str
    category: Optional[str] = None
    status: Optional[str] = None


class Incident(BaseModel):
    """Incident domain entity."""
    id: Optional[str] = Field(validation_alias="_id", serialization_alias="id", default=None)
    incident_number: str
    asset_id: Optional[str] = None
    asset: Optional[AssetSummary] = None  # Populated asset info

    # Incident Details
    title: str
    description: str
    category: IncidentCategory
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.REPORTED

    # Location
    location: Optional[IncidentLocation] = None

    # Reporter Information
    reported_by: Optional[str] = None
    reporter_type: ReporterType = ReporterType.CITIZEN
    reporter_contact: Optional[ReporterContact] = None
    reported_via: str = "web"  # "web" | "mobile" | "qr_code" | "phone" | "system"
    reported_at: datetime = Field(default_factory=datetime.utcnow)

    # Assignment & Resolution
    assigned_to: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolution_type: Optional[ResolutionType] = None

    # Linked Records
    maintenance_record_id: Optional[str] = None
    related_incidents: List[str] = Field(default_factory=list)

    # Media & Evidence
    photos: List[str] = Field(default_factory=list)
    videos: List[str] = Field(default_factory=list)
    attachments: List[IncidentAttachment] = Field(default_factory=list)

    # Citizen Engagement
    public_visible: bool = True
    upvotes: int = 0
    upvoted_by: List[str] = Field(default_factory=list)
    comments: List[IncidentComment] = Field(default_factory=list)

    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None

    # Analytics
    response_time_minutes: Optional[int] = None
    resolution_time_minutes: Optional[int] = None
    citizen_satisfaction: Optional[int] = None  # 1-5 rating

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


class IncidentCreate(BaseModel):
    """Incident creation schema."""
    asset_id: Optional[str] = None
    title: str
    description: str
    category: IncidentCategory
    severity: IncidentSeverity
    location: Optional[IncidentLocation] = None
    reporter_contact: Optional[ReporterContact] = None
    reported_via: str = "web"
    photos: List[str] = Field(default_factory=list)
    public_visible: bool = True


class IncidentUpdate(BaseModel):
    """Incident update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[IncidentCategory] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolution_type: Optional[ResolutionType] = None


class IncidentCommentRequest(BaseModel):
    """Incident comment request schema."""
    comment: str
    is_internal: bool = False
