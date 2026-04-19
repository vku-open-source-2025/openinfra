"""MongoDB implementation of SITREP repository."""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.models.sitrep import Sitrep, SitrepDelta
from app.domain.repositories.sitrep_repository import SitrepRepository
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str


class MongoSitrepRepository(SitrepRepository):
    """MongoDB SITREP repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["sitreps"]

    async def create(self, payload: dict) -> Sitrep:
        """Create a new sitrep."""
        now = datetime.utcnow()
        payload["created_at"] = now
        payload["updated_at"] = now

        result = await self.collection.insert_one(payload)
        doc = await self.collection.find_one({"_id": result.inserted_id})
        doc = convert_objectid_to_str(doc)
        return Sitrep(**doc)

    async def find_by_id(self, sitrep_id: str) -> Optional[Sitrep]:
        """Find sitrep by id."""
        if not ObjectId.is_valid(sitrep_id):
            return None

        doc = await self.collection.find_one({"_id": ObjectId(sitrep_id)})
        if not doc:
            return None

        doc = convert_objectid_to_str(doc)
        return Sitrep(**doc)

    async def update(self, sitrep_id: str, updates: dict) -> Optional[Sitrep]:
        """Update sitrep by id."""
        if not ObjectId.is_valid(sitrep_id):
            return None

        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one({"_id": ObjectId(sitrep_id)}, {"$set": updates})
        return await self.find_by_id(sitrep_id)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Sitrep]:
        """List sitreps with filtering."""
        query = {}
        if emergency_event_id:
            query["emergency_event_id"] = emergency_event_id
        if status:
            query["status"] = status

        cursor = (
            self.collection.find(query)
            .sort("updated_at", -1)
            .skip(skip)
            .limit(limit)
        )

        sitreps: List[Sitrep] = []
        async for doc in cursor:
            doc = convert_objectid_to_str(doc)
            sitreps.append(Sitrep(**doc))
        return sitreps

    async def append_delta(self, sitrep_id: str, delta: SitrepDelta) -> Optional[Sitrep]:
        """Append timeline delta and return updated sitrep."""
        if not ObjectId.is_valid(sitrep_id):
            return None

        await self.collection.update_one(
            {"_id": ObjectId(sitrep_id)},
            {
                "$push": {"deltas": delta.model_dump(exclude_unset=True)},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )
        return await self.find_by_id(sitrep_id)
