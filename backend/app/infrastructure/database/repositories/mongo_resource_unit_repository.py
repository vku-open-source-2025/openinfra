"""MongoDB implementation of resource unit repository."""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.models.resource_unit import ResourceUnit
from app.domain.repositories.resource_unit_repository import ResourceUnitRepository
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str


class MongoResourceUnitRepository(ResourceUnitRepository):
    """MongoDB resource unit repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["resource_units"]

    async def create(self, payload: dict) -> ResourceUnit:
        """Create a new resource unit."""
        now = datetime.utcnow()
        payload["created_at"] = now
        payload["updated_at"] = now

        result = await self.collection.insert_one(payload)
        doc = await self.collection.find_one({"_id": result.inserted_id})
        doc = convert_objectid_to_str(doc)
        return ResourceUnit(**doc)

    async def find_by_id(self, resource_id: str) -> Optional[ResourceUnit]:
        """Find resource unit by id."""
        if not ObjectId.is_valid(resource_id):
            return None

        doc = await self.collection.find_one({"_id": ObjectId(resource_id)})
        if not doc:
            return None

        doc = convert_objectid_to_str(doc)
        return ResourceUnit(**doc)

    async def update(self, resource_id: str, updates: dict) -> Optional[ResourceUnit]:
        """Update resource unit by id."""
        if not ObjectId.is_valid(resource_id):
            return None

        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(resource_id)},
            {"$set": updates},
        )
        return await self.find_by_id(resource_id)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        resource_type: Optional[str] = None,
        district: Optional[str] = None,
    ) -> List[ResourceUnit]:
        """List resource units with filtering."""
        query = {}
        if status:
            query["status"] = status
        if resource_type:
            query["resource_type"] = resource_type
        if district:
            query["district"] = district

        cursor = (
            self.collection.find(query)
            .sort("updated_at", -1)
            .skip(skip)
            .limit(limit)
        )

        resources: List[ResourceUnit] = []
        async for doc in cursor:
            doc = convert_objectid_to_str(doc)
            resources.append(ResourceUnit(**doc))
        return resources
