"""User repository interface."""
from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.models.user import User


class UserRepository(ABC):
    """User repository interface."""

    @abstractmethod
    async def create(self, user_data: dict) -> User:
        """Create a new user."""
        pass

    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID."""
        pass

    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username."""
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        pass

    @abstractmethod
    async def update(self, user_id: str, updates: dict) -> Optional[User]:
        """Update user."""
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete user (soft delete)."""
        pass

    @abstractmethod
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[User]:
        """List users with pagination and filtering."""
        pass
