"""MongoDB implementation of notification repository."""

from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.domain.models.notification import Notification
from app.domain.repositories.notification_repository import NotificationRepository
from app.infrastructure.database.repositories.base_repository import (
    convert_objectid_to_str,
)
from datetime import datetime


class MongoNotificationRepository(NotificationRepository):
    """MongoDB notification repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["notifications"]

    async def create(self, notification_data: dict) -> Notification:
        """Create a new notification."""
        notification_data["created_at"] = datetime.utcnow()
        notification_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(notification_data)
        notification_doc = await self.collection.find_one({"_id": result.inserted_id})
        notification_doc = convert_objectid_to_str(notification_doc)
        return Notification(**notification_doc)

    async def find_by_id(self, notification_id: str) -> Optional[Notification]:
        """Find notification by ID."""
        if not ObjectId.is_valid(notification_id):
            return None
        notification_doc = await self.collection.find_one(
            {"_id": ObjectId(notification_id)}
        )
        if notification_doc:
            notification_doc = convert_objectid_to_str(notification_doc)
            return Notification(**notification_doc)
        return None

    async def find_by_user(
        self, user_id: str, skip: int = 0, limit: int = 100, unread_only: bool = False
    ) -> List[Notification]:
        """Find notifications for a user."""
        query = {"user_id": user_id}
        if unread_only:
            query["read"] = False

        # Filter out expired notifications
        query["$or"] = [
            {"expires_at": None},
            {"expires_at": {"$gt": datetime.utcnow()}},
        ]

        cursor = (
            self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        )
        notifications = []
        async for notification_doc in cursor:
            notification_doc = convert_objectid_to_str(notification_doc)
            notifications.append(Notification(**notification_doc))
        return notifications

    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read."""
        if not ObjectId.is_valid(notification_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(notification_id)},
            {
                "$set": {
                    "read": True,
                    "read_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    async def mark_all_as_read(self, user_id: str) -> bool:
        """Mark all notifications as read for a user."""
        result = await self.collection.update_many(
            {"user_id": user_id, "read": False},
            {
                "$set": {
                    "read": True,
                    "read_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    async def update_delivery_status(
        self,
        notification_id: str,
        channel: str,
        status: str,
        error: Optional[str] = None,
    ) -> bool:
        """Update delivery status for a channel."""
        if not ObjectId.is_valid(notification_id):
            return False

        update_fields = {
            f"channels.$[elem].status": status,
            "updated_at": datetime.utcnow(),
        }

        if status == "sent":
            update_fields[f"channels.$[elem].sent_at"] = datetime.utcnow()
        elif status == "delivered":
            update_fields[f"channels.$[elem].delivered_at"] = datetime.utcnow()
        elif status == "failed" and error:
            update_fields[f"channels.$[elem].error"] = error

        result = await self.collection.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": update_fields},
            array_filters=[{"elem.type": channel}],
        )
        return result.modified_count > 0

    async def delete_expired(self) -> int:
        """Delete expired notifications."""
        result = await self.collection.delete_many(
            {"expires_at": {"$lt": datetime.utcnow()}}
        )
        return result.deleted_count
