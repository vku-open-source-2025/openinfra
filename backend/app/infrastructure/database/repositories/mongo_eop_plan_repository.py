"""MongoDB implementation of EOP plan repository."""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.models.eop_plan import EOPPlan
from app.domain.repositories.eop_plan_repository import EOPPlanRepository
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str


class MongoEOPPlanRepository(EOPPlanRepository):
    """MongoDB EOP plan repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["eop_plans"]

    async def create(self, payload: dict) -> EOPPlan:
        """Create a new EOP plan."""
        now = datetime.utcnow()
        payload["created_at"] = now
        payload["updated_at"] = now

        result = await self.collection.insert_one(payload)
        doc = await self.collection.find_one({"_id": result.inserted_id})
        doc = convert_objectid_to_str(doc)
        return EOPPlan(**doc)

    async def find_by_id(self, plan_id: str) -> Optional[EOPPlan]:
        """Find EOP plan by id."""
        if not ObjectId.is_valid(plan_id):
            return None

        doc = await self.collection.find_one({"_id": ObjectId(plan_id)})
        if not doc:
            return None

        doc = convert_objectid_to_str(doc)
        return EOPPlan(**doc)

    async def update(self, plan_id: str, updates: dict) -> Optional[EOPPlan]:
        """Update EOP plan by id."""
        if not ObjectId.is_valid(plan_id):
            return None

        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one({"_id": ObjectId(plan_id)}, {"$set": updates})
        return await self.find_by_id(plan_id)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[EOPPlan]:
        """List EOP plans with filtering."""
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

        plans: List[EOPPlan] = []
        async for doc in cursor:
            doc = convert_objectid_to_str(doc)
            plans.append(EOPPlan(**doc))
        return plans
