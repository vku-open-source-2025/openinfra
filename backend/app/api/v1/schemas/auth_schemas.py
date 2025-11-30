"""Authentication API schemas."""
from pydantic import BaseModel, EmailStr
from app.domain.models.user import UserResponse


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """Registration request schema."""
    username: str
    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    current_password: str
    new_password: str
