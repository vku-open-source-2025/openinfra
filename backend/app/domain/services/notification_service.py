"""Notification service for managing notifications."""

from typing import Optional, List
from datetime import datetime, timedelta
from app.domain.models.notification import (
    Notification,
    NotificationCreate,
    NotificationChannel,
    DeliveryStatus,
)
from app.domain.repositories.notification_repository import NotificationRepository
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.notifications.email_service import EmailService
from app.infrastructure.notifications.sms_service import SMSService
from app.infrastructure.notifications.push_service import PushService
from app.core.exceptions import NotFoundError
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Notification service for business logic."""

    def __init__(
        self,
        notification_repository: NotificationRepository,
        user_repository: Optional[UserRepository] = None,
        email_service: Optional[EmailService] = None,
        sms_service: Optional[SMSService] = None,
        push_service: Optional[PushService] = None,
    ):
        self.repository = notification_repository
        self.user_repository = user_repository
        self.email_service = email_service or EmailService()
        self.sms_service = sms_service or SMSService()
        self.push_service = push_service or PushService()

    async def create_notification(
        self, notification_data: NotificationCreate
    ) -> Notification:
        """Create and send a notification."""
        # Create notification record
        notification_dict = notification_data.dict(exclude_unset=True)

        # Initialize channels
        channels = []
        for channel in notification_data.channels:
            channels.append(
                {"type": channel.value, "status": DeliveryStatus.PENDING.value}
            )
        notification_dict["channels"] = channels

        notification = await self.repository.create(notification_dict)

        # Send notifications via configured channels
        await self._send_notification(notification)

        logger.info(
            f"Created notification: {notification.id} for user {notification.user_id}"
        )
        return notification

    async def _send_notification(self, notification: Notification):
        """Send notification via all configured channels."""
        # Get user preferences if user repository available
        user_preferences = {}
        if self.user_repository:
            try:
                user = await self.user_repository.find_by_id(notification.user_id)
                if user:
                    user_preferences = user.notification_preferences or {}
            except:
                pass

        # Send via each channel
        for channel_delivery in notification.channels:
            channel_type = channel_delivery.type.value

            # Check user preferences
            if user_preferences.get(channel_type, True) is False:
                logger.info(
                    f"Skipping {channel_type} for user {notification.user_id} (preference disabled)"
                )
                continue

            try:
                if channel_type == NotificationChannel.EMAIL.value:
                    await self._send_email(notification, channel_delivery)
                elif channel_type == NotificationChannel.SMS.value:
                    await self._send_sms(notification, channel_delivery)
                elif channel_type == NotificationChannel.PUSH.value:
                    await self._send_push(notification, channel_delivery)
                elif channel_type == NotificationChannel.IN_APP.value:
                    # In-app notifications are automatically available
                    await self.repository.update_delivery_status(
                        str(notification.id),
                        channel_type,
                        DeliveryStatus.DELIVERED.value,
                    )
            except Exception as e:
                logger.error(f"Error sending {channel_type} notification: {e}")
                await self.repository.update_delivery_status(
                    str(notification.id),
                    channel_type,
                    DeliveryStatus.FAILED.value,
                    str(e),
                )

    async def _send_email(self, notification: Notification, channel: dict):
        """Send email notification."""
        if not self.user_repository:
            return

        user = await self.user_repository.find_by_id(notification.user_id)
        if not user or not user.email:
            return

        # Create HTML email body
        html_body = f"""
        <html>
            <body>
                <h2>{notification.title}</h2>
                <p>{notification.message}</p>
                {f'<p><a href="{notification.action_url}">{notification.action_label or "View Details"}</a></p>' if notification.action_url else ''}
            </body>
        </html>
        """

        success = await self.email_service.send_email(
            user.email, notification.title, notification.message, html_body
        )

        status = DeliveryStatus.SENT.value if success else DeliveryStatus.FAILED.value
        await self.repository.update_delivery_status(
            str(notification.id), NotificationChannel.EMAIL.value, status
        )

    async def _send_sms(self, notification: Notification, channel: dict):
        """Send SMS notification."""
        if not self.user_repository:
            return

        user = await self.user_repository.find_by_id(notification.user_id)
        if not user or not user.phone:
            return

        message = f"{notification.title}: {notification.message}"
        if notification.action_url:
            message += f" {notification.action_url}"

        success = await self.sms_service.send_sms(user.phone, message)

        status = DeliveryStatus.SENT.value if success else DeliveryStatus.FAILED.value
        await self.repository.update_delivery_status(
            str(notification.id), NotificationChannel.SMS.value, status
        )

    async def _send_push(self, notification: Notification, channel: dict):
        """Send push notification."""
        # In a real implementation, you'd fetch device tokens from user profile
        # For now, this is a placeholder
        device_tokens = []  # TODO: Get from user profile

        if not device_tokens:
            return

        data = {}
        if notification.resource_type and notification.resource_id:
            data = {
                "resource_type": notification.resource_type,
                "resource_id": notification.resource_id,
                "action_url": notification.action_url or "",
            }

        result = await self.push_service.send_push(
            device_tokens, notification.title, notification.message, data
        )

        # Update status based on result
        if result["success"] > 0:
            await self.repository.update_delivery_status(
                str(notification.id),
                NotificationChannel.PUSH.value,
                DeliveryStatus.SENT.value,
            )
        else:
            await self.repository.update_delivery_status(
                str(notification.id),
                NotificationChannel.PUSH.value,
                DeliveryStatus.FAILED.value,
            )

    async def get_user_notifications(
        self, user_id: str, skip: int = 0, limit: int = 100, unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user."""
        return await self.repository.find_by_user(user_id, skip, limit, unread_only)

    async def mark_as_read(self, notification_id: str) -> Notification:
        """Mark notification as read."""
        success = await self.repository.mark_as_read(notification_id)
        if not success:
            raise NotFoundError("Notification", notification_id)
        notification = await self.repository.find_by_id(notification_id)
        if not notification:
            raise NotFoundError("Notification", notification_id)
        return notification

    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user."""
        success = await self.repository.mark_all_as_read(user_id)
        return 1 if success else 0

    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications."""
        notifications = await self.repository.find_by_user(
            user_id, skip=0, limit=1000, unread_only=True
        )
        return len(notifications)
