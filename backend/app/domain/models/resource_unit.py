"""Resource unit domain models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer, field_validator


class ResourceType(str, Enum):
    """Resource categories for emergency response."""

    PERSONNEL = "personnel"
    VEHICLE = "vehicle"
    MEDICAL_SUPPLY = "medical_supply"
    RESCUE_EQUIPMENT = "rescue_equipment"
    SHELTER = "shelter"


class ResourceStatus(str, Enum):
    """Availability status of resources."""

    AVAILABLE = "available"
    DEPLOYED = "deployed"
    STANDBY = "standby"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class ResourceUnit(BaseModel):
    """Resource inventory entity."""

    id: Optional[str] = Field(
        validation_alias="_id", serialization_alias="id", default=None
    )
    resource_code: str
    name: str
    resource_type: ResourceType
    status: ResourceStatus = ResourceStatus.AVAILABLE
    capacity: Optional[float] = None
    capacity_unit: Optional[str] = None
    district: Optional[str] = None
    ward: Optional[str] = None
    current_location: Optional[dict] = None
    skills: List[str] = Field(default_factory=list)
    contact_phone: Optional[str] = None
    assigned_dispatch_order_id: Optional[str] = None
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


class ResourceUnitCreate(BaseModel):
    """Payload for creating resources."""

    resource_code: str
    name: str
    resource_type: ResourceType
    status: ResourceStatus = ResourceStatus.AVAILABLE
    capacity: Optional[float] = None
    capacity_unit: Optional[str] = None
    district: Optional[str] = None
    ward: Optional[str] = None
    current_location: Optional[dict] = None
    skills: List[str] = Field(default_factory=list)
    contact_phone: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResourceUnitUpdate(BaseModel):
    """Payload for updating resources."""

    name: Optional[str] = None
    resource_type: Optional[ResourceType] = None
    status: Optional[ResourceStatus] = None
    capacity: Optional[float] = None
    capacity_unit: Optional[str] = None
    district: Optional[str] = None
    ward: Optional[str] = None
    current_location: Optional[dict] = None
    skills: Optional[List[str]] = None
    contact_phone: Optional[str] = None
    assigned_dispatch_order_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
