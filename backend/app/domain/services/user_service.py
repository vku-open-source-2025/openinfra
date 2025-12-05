"""User domain service."""
from typing import Optional, List
from datetime import datetime
from app.domain.models.user import User, UserCreate, UserUpdate, UserResponse
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.security.password import hash_password, verify_password
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)

# Permission definitions
PERMISSIONS = {
    "admin": [
        "view_all_assets", "create_asset", "update_asset", "delete_asset",
        "view_all_maintenance", "create_maintenance", "update_maintenance",
        "view_all_incidents", "assign_incidents",
        "manage_users", "manage_budgets", "approve_budgets",
        "view_all_reports", "generate_reports", "manage_iot"
    ],
    "technician": [
        "view_assigned_assets", "update_asset_status",
        "view_assigned_maintenance", "update_maintenance",
        "view_assigned_incidents", "update_incidents",
        "upload_photos"
    ],
    "citizen": [
        "view_public_assets", "scan_qr_code",
        "create_incident", "view_own_incidents", "comment_incidents"
    ]
}


class UserService:
    """User service for business logic."""

    def __init__(self, user_repository: UserRepository):
        self.repository = user_repository

    def _get_permissions_for_role(self, role: str) -> List[str]:
        """Get permissions for a role."""
        return PERMISSIONS.get(role, [])

    async def create_user(self, user_data: UserCreate, created_by: Optional[str] = None) -> User:
        """Create a new user."""
        # Check if username exists
        existing = await self.repository.find_by_username(user_data.username)
        if existing:
            raise ConflictError(f"Username '{user_data.username}' already exists")

        # Check if email exists
        existing = await self.repository.find_by_email(user_data.email)
        if existing:
            raise ConflictError(f"Email '{user_data.email}' already exists")

        # Hash password
        password_hash = hash_password(user_data.password)

        # Get permissions for role
        permissions = self._get_permissions_for_role(user_data.role.value)

        # Create user document
        user_dict = {
            "username": user_data.username,
            "email": user_data.email,
            "password_hash": password_hash,
            "full_name": user_data.full_name,
            "phone": user_data.phone,
            "role": user_data.role.value,
            "permissions": permissions,
            "department": user_data.department,
            "created_by": created_by
        }

        user = await self.repository.create(user_dict)
        logger.info(f"Created user: {user.username} ({user.role})")
        return user

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user by username or email."""
        # Try to find by username first
        user = await self.repository.find_by_username(username)
        # If not found, try by email
        if not user:
            user = await self.repository.find_by_email(username)
        if not user:
            return None

        if user.status != "active":
            return None

        if verify_password(password, user.password_hash):
            # Update last login
            await self.repository.update(str(user.id), {"last_login": datetime.utcnow()})
            return user

        return None

    async def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID."""
        user = await self.repository.find_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return user

    async def get_user_by_username(self, username: str) -> User:
        """Get user by username."""
        user = await self.repository.find_by_username(username)
        if not user:
            raise NotFoundError("User", username)
        return user

    async def update_user(self, user_id: str, updates: UserUpdate) -> User:
        """Update user."""
        user = await self.get_user_by_id(user_id)

        update_dict = updates.dict(exclude_unset=True)

        # Check email uniqueness if updating email
        if "email" in update_dict:
            existing = await self.repository.find_by_email(update_dict["email"])
            if existing and str(existing.id) != user_id:
                raise ConflictError(f"Email '{update_dict['email']}' already exists")

        updated_user = await self.repository.update(user_id, update_dict)
        if not updated_user:
            raise NotFoundError("User", user_id)

        return updated_user

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password."""
        user = await self.get_user_by_id(user_id)

        if not verify_password(current_password, user.password_hash):
            raise ValidationError("Current password is incorrect")

        new_hash = hash_password(new_password)
        await self.repository.update(user_id, {"password_hash": new_hash})
        return True

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[User]:
        """List users."""
        return await self.repository.list_users(skip, limit, role, status)

    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user."""
        return await self.repository.delete(user_id)

    def to_response(self, user: User) -> UserResponse:
        """Convert User entity to UserResponse."""
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role,
            permissions=user.permissions,
            department=user.department,
            avatar_url=user.avatar_url,
            status=user.status,
            language=user.language,
            notification_preferences=user.notification_preferences,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
