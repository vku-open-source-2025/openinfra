"""MongoDB implementation of emergency repository."""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.models.emergency import EmergencyEvent
from app.domain.repositories.emergency_repository import EmergencyRepository
from app.infrastructure.database.repositories.base_repository import (
    convert_objectid_to_str,
)


class MongoEmergencyRepository(EmergencyRepository):
    """MongoDB emergency repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["emergency_events"]

    async def create(self, event_data: dict) -> EmergencyEvent:
        """Create a new emergency event."""
        now = datetime.utcnow()
        event_data["created_at"] = now
        event_data["updated_at"] = now

        result = await self.collection.insert_one(event_data)
        event_doc = await self.collection.find_one({"_id": result.inserted_id})
        event_doc = convert_objectid_to_str(event_doc)
        return EmergencyEvent(**event_doc)

    async def find_by_id(self, event_id: str) -> Optional[EmergencyEvent]:
        """Find event by ID."""
        if not ObjectId.is_valid(event_id):
            return None

        event_doc = await self.collection.find_one({"_id": ObjectId(event_id)})
        if not event_doc:
            return None

        event_doc = convert_objectid_to_str(event_doc)
        return EmergencyEvent(**event_doc)

    async def update(self, event_id: str, updates: dict) -> Optional[EmergencyEvent]:
        """Update event by ID."""
        if not ObjectId.is_valid(event_id):
            return None

        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one({"_id": ObjectId(event_id)}, {"$set": updates})
        return await self.find_by_id(event_id)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        query_text: Optional[str] = None,
    ) -> List[EmergencyEvent]:
        """List emergency events with filtering."""
        query = {}

        if status:
            query["status"] = status
        if severity:
            query["severity"] = severity
        if event_type:
            query["event_type"] = event_type
        if query_text:
            query["$or"] = [
                {"title": {"$regex": query_text, "$options": "i"}},
                {"description": {"$regex": query_text, "$options": "i"}},
                {"event_code": {"$regex": query_text, "$options": "i"}},
            ]

        cursor = (
            self.collection.find(query)
            .sort("updated_at", -1)
            .skip(skip)
            .limit(limit)
        )

        events: List[EmergencyEvent] = []
        async for event_doc in cursor:
            event_doc = convert_objectid_to_str(event_doc)
            events.append(EmergencyEvent(**event_doc))

        return events
