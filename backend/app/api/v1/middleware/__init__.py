"""API v1 middleware."""

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.infrastructure.security.jwt import decode_token, get_user_id_from_token
from app.domain.services.user_service import UserService
from app.api.v1.dependencies import get_user_service
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(get_user_service),
):
    """Get current authenticated user."""
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        user = await user_service.get_user_by_id(user_id)
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
            )
        return user
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    user_service: UserService = Depends(get_user_service),
):
    """Get current user if authenticated, else None."""
    if not credentials:
        return None
    
    return await get_current_user(credentials, user_service)


def require_permission(permission: str):
    """Decorator factory for permission checking."""

    async def permission_checker(current_user=Depends(get_current_user)):
        if "*" in current_user.permissions:
            return current_user

        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}",
            )
        return current_user

    return permission_checker


def require_role(role: str):
    """Decorator factory for role checking."""

    async def role_checker(current_user=Depends(get_current_user)):
        if current_user.role.value != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {role}",
            )
        return current_user

    return role_checker
