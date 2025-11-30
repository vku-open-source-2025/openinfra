"""Notification domain model."""
from pydantic import BaseModel, Field, field_serializer, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum
from bson import ObjectId


class NotificationType(str, Enum):
    """Notification type enumeration."""
    MAINTENANCE_ASSIGNED = "maintenance_assigned"
    INCIDENT_REPORTED = "incident_reported"
    ALERT_TRIGGERED = "alert_triggered"
    BUDGET_APPROVED = "budget_approved"
    COMMENT_REPLY = "comment_reply"
    SYSTEM = "system"
    CUSTOM = "custom"


class NotificationChannel(str, Enum):
    """Notification channel enumeration."""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"


class DeliveryStatus(str, Enum):
    """Delivery status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class ChannelDelivery(BaseModel):
    """Channel delivery tracking."""
    type: NotificationChannel
    status: DeliveryStatus = DeliveryStatus.PENDING
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error: Optional[str] = None


class Notification(BaseModel):
    """Notification domain entity."""
    id: Optional[str] = Field(alias="_id", default=None)

    # Recipient
    user_id: str

    # Notification Details
    type: NotificationType
    title: str
    message: str

    # Related Resources
    resource_type: Optional[str] = None  # "asset" | "maintenance" | "incident" | "alert" | "budget"
    resource_id: Optional[str] = None

    # Action Link
    action_url: Optional[str] = None
    action_label: Optional[str] = None

    # Delivery
    channels: List[ChannelDelivery] = Field(default_factory=list)

    # Status
    read: bool = False
    read_at: Optional[datetime] = None

    # Priority
    priority: str = "normal"  # "low" | "normal" | "high" | "urgent"

    # Expiration
    expires_at: Optional[datetime] = None

    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

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


class NotificationCreate(BaseModel):
    """Notification creation schema."""
    user_id: str
    type: NotificationType
    title: str
    message: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    priority: str = "normal"
    channels: List[NotificationChannel] = Field(default_factory=lambda: [NotificationChannel.IN_APP])
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
