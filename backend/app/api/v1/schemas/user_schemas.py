"""User API schemas."""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from app.domain.models.user import UserRole


class UserCreateRequest(BaseModel):
    """User creation request schema."""

    username: str
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.CITIZEN
    department: Optional[str] = None


class UserUpdateRequest(BaseModel):
    """User update request schema."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    avatar_url: Optional[str] = None
    language: Optional[str] = None


class UserResponse(BaseModel):
    """User response schema."""

    id: str
    username: str
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: UserRole
    department: Optional[str] = None
    avatar_url: Optional[str] = None
    language: Optional[str] = None

    class Config:
        from_attributes = True
