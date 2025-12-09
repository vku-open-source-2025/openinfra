"""MongoDB implementation of merge suggestion repository."""
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.domain.models.merge_suggestion import MergeSuggestion, MergeSuggestionStatus
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str
from datetime import datetime


class MongoMergeSuggestionRepository:
    """MongoDB merge suggestion repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["merge_suggestions"]

    async def create(self, suggestion_data: dict) -> MergeSuggestion:
        """Create a new merge suggestion."""
        suggestion_data["created_at"] = datetime.utcnow()
        suggestion_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(suggestion_data)
        suggestion_doc = await self.collection.find_one({"_id": result.inserted_id})
        suggestion_doc = convert_objectid_to_str(suggestion_doc)
        return MergeSuggestion.from_dict(suggestion_doc)

    async def find_by_id(self, suggestion_id: str) -> Optional[MergeSuggestion]:
        """Find merge suggestion by ID."""
        if not ObjectId.is_valid(suggestion_id):
            return None
        suggestion_doc = await self.collection.find_one({"_id": ObjectId(suggestion_id)})
        if suggestion_doc:
            suggestion_doc = convert_objectid_to_str(suggestion_doc)
            return MergeSuggestion.from_dict(suggestion_doc)
        return None

    async def find_by_primary_incident(
        self,
        primary_incident_id: str,
        status: Optional[MergeSuggestionStatus] = None
    ) -> List[MergeSuggestion]:
        """Find merge suggestions for a primary incident."""
        query = {"primary_incident_id": primary_incident_id}
        if status:
            query["status"] = status.value

        cursor = self.collection.find(query).sort("created_at", -1)
        suggestions = []
        async for suggestion_doc in cursor:
            suggestion_doc = convert_objectid_to_str(suggestion_doc)
            suggestions.append(MergeSuggestion.from_dict(suggestion_doc))
        return suggestions

    async def update(self, suggestion_id: str, updates: dict) -> Optional[MergeSuggestion]:
        """Update merge suggestion."""
        if not ObjectId.is_valid(suggestion_id):
            return None
        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(suggestion_id)}, {"$set": updates}
        )
        return await self.find_by_id(suggestion_id)

    async def delete(self, suggestion_id: str) -> bool:
        """Delete merge suggestion."""
        if not ObjectId.is_valid(suggestion_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(suggestion_id)})
        return result.deleted_count > 0

