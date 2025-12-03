"""Asset domain model."""

from pydantic import BaseModel, Field, field_serializer, field_validator
from typing import Any, Optional, List, Dict
from datetime import datetime
from enum import Enum
from bson import ObjectId
from app.domain.value_objects.specifications import AssetSpecifications
from app.domain.value_objects.location import Location


class AssetStatus(str, Enum):
    """Asset status enumeration."""

    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    DAMAGED = "damaged"
    RETIRED = "retired"


class AssetCondition(str, Enum):
    """Asset condition enumeration."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class LifecycleStage(str, Enum):
    """Lifecycle stage enumeration."""

    PLANNING = "planning"
    CONSTRUCTION = "construction"
    OPERATIONAL = "operational"
    DECOMMISSIONED = "decommissioned"


class Attachment(BaseModel):
    """Asset attachment model."""

    file_name: str
    file_url: str
    file_type: str
    uploaded_at: datetime
    uploaded_by: str


class Asset(BaseModel):
    """Asset domain entity."""

    id: Optional[str] = Field(
        validation_alias="_id", serialization_alias="id", default=None
    )
    asset_code: Optional[str] = None  # Optional for legacy data migration
    name: Optional[str] = None  # Optional for legacy data migration
    feature_type: str
    feature_code: str
    category: Optional[str] = None

    # Geospatial
    geometry: Dict[str, Any]  # GeoJSON format

    # Location
    location: Optional[Location] = None

    # Specifications
    specifications: Optional[AssetSpecifications] = None

    # Lifecycle
    status: AssetStatus = AssetStatus.OPERATIONAL
    condition: Optional[AssetCondition] = None
    lifecycle_stage: LifecycleStage = LifecycleStage.OPERATIONAL
    installation_cost: Optional[float] = None
    current_value: Optional[float] = None
    depreciation_rate: Optional[float] = None

    # Ownership & Management
    owner: Optional[str] = None
    manager_id: Optional[str] = None

    # QR/NFC
    qr_code: Optional[str] = None
    nfc_tag_id: Optional[str] = None
    public_info_visible: bool = False

    # IoT
    iot_enabled: bool = False
    sensor_ids: List[str] = Field(default_factory=list)

    # Metadata
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    attachments: List[Attachment] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

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


class AssetCreate(BaseModel):
    """Asset creation schema."""

    asset_code: str
    name: str
    feature_type: str
    feature_code: str
    category: Optional[str] = None
    geometry: Dict[str, Any]
    location: Optional[Location] = None
    specifications: Optional[AssetSpecifications] = None
    status: AssetStatus = AssetStatus.OPERATIONAL
    condition: Optional[AssetCondition] = None
    lifecycle_stage: LifecycleStage = LifecycleStage.OPERATIONAL
    owner: Optional[str] = None
    manager_id: Optional[str] = None
    qr_code: Optional[str] = None
    nfc_tag_id: Optional[str] = None
    public_info_visible: bool = False
    iot_enabled: bool = False
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class AssetUpdate(BaseModel):
    """Asset update schema."""

    name: Optional[str] = None
    feature_type: Optional[str] = None
    category: Optional[str] = None
    geometry: Optional[Dict[str, Any]] = None
    location: Optional[Location] = None
    specifications: Optional[AssetSpecifications] = None
    status: Optional[AssetStatus] = None
    condition: Optional[AssetCondition] = None
    lifecycle_stage: Optional[LifecycleStage] = None
    owner: Optional[str] = None
    manager_id: Optional[str] = None
    public_info_visible: Optional[bool] = None
    iot_enabled: Optional[bool] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
