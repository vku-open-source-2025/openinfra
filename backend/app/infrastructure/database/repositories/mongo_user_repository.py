"""MongoDB implementation of user repository."""

from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.domain.models.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.repositories.base_repository import (
    convert_objectid_to_str,
)
from datetime import datetime


class MongoUserRepository(UserRepository):
    """MongoDB user repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["users"]

    async def create(self, user_data: dict) -> User:
        """Create a new user."""
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(user_data)
        user_doc = await self.collection.find_one({"_id": result.inserted_id})
        user_doc = convert_objectid_to_str(user_doc)
        return User(**user_doc)

    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID."""
        if not ObjectId.is_valid(user_id):
            return None
        user_doc = await self.collection.find_one({"_id": ObjectId(user_id)})
        if user_doc:
            user_doc = convert_objectid_to_str(user_doc)
            return User(**user_doc)
        return None

    async def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username."""
        user_doc = await self.collection.find_one({"username": username})
        if user_doc:
            user_doc = convert_objectid_to_str(user_doc)
            return User(**user_doc)
        return None

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        user_doc = await self.collection.find_one({"email": email})
        if user_doc:
            user_doc = convert_objectid_to_str(user_doc)
            return User(**user_doc)
        return None

    async def update(self, user_id: str, updates: dict) -> Optional[User]:
        """Update user."""
        if not ObjectId.is_valid(user_id):
            return None
        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
        return await self.find_by_id(user_id)

    async def delete(self, user_id: str) -> bool:
        """Delete user (soft delete by setting status to inactive)."""
        if not ObjectId.is_valid(user_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"status": "inactive", "updated_at": datetime.utcnow()}},
        )
        return result.modified_count > 0

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[User]:
        """List users with pagination and filtering."""
        import logging
        logger = logging.getLogger(__name__)
        
        query = {}
        if role:
            query["role"] = role
        if status:
            query["status"] = status

        logger.debug(f"Querying users with filter: {query}")
        cursor = self.collection.find(query).skip(skip).limit(limit)
        users = []
        async for user_doc in cursor:
            user_doc = convert_objectid_to_str(user_doc)
            users.append(User(**user_doc))
        logger.debug(f"Found {len(users)} users matching query")
        return users
