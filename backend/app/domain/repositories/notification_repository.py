"""Notification repository interface."""
from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.models.notification import Notification


class NotificationRepository(ABC):
    """Notification repository interface."""

    @abstractmethod
    async def create(self, notification_data: dict) -> Notification:
        """Create a new notification."""
        pass

    @abstractmethod
    async def find_by_id(self, notification_id: str) -> Optional[Notification]:
        """Find notification by ID."""
        pass

    @abstractmethod
    async def find_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        unread_only: bool = False
    ) -> List[Notification]:
        """Find notifications for a user."""
        pass

    @abstractmethod
    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read."""
        pass

    @abstractmethod
    async def mark_all_as_read(self, user_id: str) -> bool:
        """Mark all notifications as read for a user."""
        pass

    @abstractmethod
    async def update_delivery_status(
        self,
        notification_id: str,
        channel: str,
        status: str,
        error: Optional[str] = None
    ) -> bool:
        """Update delivery status for a channel."""
        pass

    @abstractmethod
    async def delete_expired(self) -> int:
        """Delete expired notifications."""
        pass
