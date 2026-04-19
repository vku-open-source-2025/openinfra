"""MongoDB implementation of dispatch order repository."""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.models.dispatch_order import DispatchOrder
from app.domain.repositories.dispatch_order_repository import DispatchOrderRepository
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str


class MongoDispatchOrderRepository(DispatchOrderRepository):
    """MongoDB dispatch order repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["dispatch_orders"]

    async def create(self, payload: dict) -> DispatchOrder:
        """Create a new dispatch order."""
        now = datetime.utcnow()
        payload["created_at"] = now
        payload["updated_at"] = now

        result = await self.collection.insert_one(payload)
        doc = await self.collection.find_one({"_id": result.inserted_id})
        doc = convert_objectid_to_str(doc)
        return DispatchOrder(**doc)

    async def find_by_id(self, order_id: str) -> Optional[DispatchOrder]:
        """Find dispatch order by id."""
        if not ObjectId.is_valid(order_id):
            return None

        doc = await self.collection.find_one({"_id": ObjectId(order_id)})
        if not doc:
            return None

        doc = convert_objectid_to_str(doc)
        return DispatchOrder(**doc)

    async def update(self, order_id: str, updates: dict) -> Optional[DispatchOrder]:
        """Update dispatch order by id."""
        if not ObjectId.is_valid(order_id):
            return None

        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one({"_id": ObjectId(order_id)}, {"$set": updates})
        return await self.find_by_id(order_id)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List[DispatchOrder]:
        """List dispatch orders with filtering."""
        query = {}
        if emergency_event_id:
            query["emergency_event_id"] = emergency_event_id
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority

        cursor = (
            self.collection.find(query)
            .sort("updated_at", -1)
            .skip(skip)
            .limit(limit)
        )

        orders: List[DispatchOrder] = []
        async for doc in cursor:
            doc = convert_objectid_to_str(doc)
            orders.append(DispatchOrder(**doc))
        return orders
