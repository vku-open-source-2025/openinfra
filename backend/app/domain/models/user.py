"""User domain model."""

from pydantic import BaseModel, EmailStr, Field, field_serializer, field_validator
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId


class UserRole(str, Enum):
    """User roles."""

    ADMIN = "admin"
    TECHNICIAN = "technician"
    CITIZEN = "citizen"


class UserStatus(str, Enum):
    """User status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(BaseModel):
    """User domain entity."""

    id: Optional[str] = Field(alias="_id", default=None)
    username: str
    email: EmailStr
    password_hash: str
    full_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.CITIZEN
    permissions: List[str] = Field(default_factory=list)
    department: Optional[str] = None
    avatar_url: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE
    language: str = "vi"
    notification_preferences: dict = Field(
        default_factory=lambda: {"email": True, "push": True, "sms": False}
    )
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    metadata: dict = Field(default_factory=dict)

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


class UserCreate(BaseModel):
    """User creation schema."""

    username: str
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.CITIZEN
    department: Optional[str] = None


class UserUpdate(BaseModel):
    """User update schema."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    avatar_url: Optional[str] = None
    language: Optional[str] = None
    notification_preferences: Optional[dict] = None


class UserResponse(BaseModel):
    """User response schema (without password)."""

    id: str
    username: str
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: UserRole
    permissions: List[str]
    department: Optional[str] = None
    avatar_url: Optional[str] = None
    status: UserStatus
    language: str
    notification_preferences: dict
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
