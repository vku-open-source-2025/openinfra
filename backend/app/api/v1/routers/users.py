"""Users API router."""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional
from app.api.v1.schemas.user_schemas import UserResponse, UserCreateRequest, UserUpdateRequest
from app.domain.services.user_service import UserService
from app.domain.models.user import UserCreate, UserUpdate
from app.api.v1.dependencies import get_user_service
from app.api.v1.middleware import get_current_user, require_role, require_permission
from app.core.exceptions import NotFoundError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get current user profile."""
    return user_service.to_response(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    updates: UserUpdateRequest,
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update current user profile."""
    user_update = UserUpdate(**updates.dict(exclude_unset=True))
    updated_user = await user_service.update_user(str(current_user.id), user_update)
    return user_service.to_response(updated_user)


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    role: Optional[str] = None,
    status: Optional[str] = None,
    current_user = Depends(require_permission("manage_users")),
    user_service: UserService = Depends(get_user_service)
):
    """List users (admin only)."""
    users = await user_service.list_users(skip, limit, role, status)
    return [user_service.to_response(user) for user in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    current_user = Depends(require_permission("manage_users")),
    user_service: UserService = Depends(get_user_service)
):
    """Create a new user (admin only)."""
    user_create = UserCreate(**user_data.dict())
    user = await user_service.create_user(user_create, created_by=str(current_user.id))
    return user_service.to_response(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user = Depends(require_permission("manage_users")),
    user_service: UserService = Depends(get_user_service)
):
    """Get user by ID (admin only)."""
    user = await user_service.get_user_by_id(user_id)
    return user_service.to_response(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    updates: UserUpdateRequest,
    current_user = Depends(require_permission("manage_users")),
    user_service: UserService = Depends(get_user_service)
):
    """Update user (admin only)."""
    user_update = UserUpdate(**updates.dict(exclude_unset=True))
    updated_user = await user_service.update_user(user_id, user_update)
    return user_service.to_response(updated_user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user = Depends(require_permission("manage_users")),
    user_service: UserService = Depends(get_user_service)
):
    """Delete user (admin only - soft delete)."""
    await user_service.deactivate_user(user_id)
    return {"message": "User deactivated successfully"}
