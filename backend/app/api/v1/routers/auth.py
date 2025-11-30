"""Authentication API router."""
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta
from app.api.v1.schemas.auth_schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordChangeRequest
)
from app.domain.services.user_service import UserService
from app.domain.models.user import UserCreate
from app.infrastructure.security.jwt import create_access_token, create_refresh_token, decode_token
from app.api.v1.dependencies import get_user_service
from app.api.v1.middleware import get_current_user
from app.core.config import settings
from app.core.exceptions import UnauthorizedError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Register a new user."""
    user_create = UserCreate(
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        phone=request.phone,
        role="citizen"  # Default role for registration
    )

    user = await user_service.create_user(user_create)

    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "username": user.username}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_service.to_response(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Authenticate user and get tokens."""
    user = await user_service.authenticate(request.username, request.password)

    if not user:
        raise UnauthorizedError("Invalid username or password")

    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "username": user.username}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_service.to_response(user)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Refresh access token."""
    payload = decode_token(request.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    user = await user_service.get_user_by_id(user_id)

    # Create new tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "username": user.username}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_service.to_response(user)
    )


@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    """Logout user (client should discard tokens)."""
    return {"message": "Logged out successfully"}


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Change user password."""
    await user_service.change_password(
        str(current_user.id),
        request.current_password,
        request.new_password
    )
    return {"message": "Password changed successfully"}
