"""MongoDB implementation of maintenance repository."""
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.domain.models.maintenance import Maintenance
from app.domain.repositories.maintenance_repository import MaintenanceRepository
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str
from datetime import datetime, timedelta


class MongoMaintenanceRepository(MaintenanceRepository):
    """MongoDB maintenance repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["maintenance_records"]

    async def create(self, maintenance_data: dict) -> Maintenance:
        """Create a new maintenance record."""
        maintenance_data["created_at"] = datetime.utcnow()
        maintenance_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(maintenance_data)
        maintenance_doc = await self.collection.find_one({"_id": result.inserted_id})
        maintenance_doc = convert_objectid_to_str(maintenance_doc)
        return Maintenance(**maintenance_doc)

    async def find_by_id(self, maintenance_id: str) -> Optional[Maintenance]:
        """Find maintenance by ID."""
        if not ObjectId.is_valid(maintenance_id):
            return None
        maintenance_doc = await self.collection.find_one({"_id": ObjectId(maintenance_id)})
        if maintenance_doc:
            maintenance_doc = convert_objectid_to_str(maintenance_doc)
            return Maintenance(**maintenance_doc)
        return None

    async def find_by_work_order_number(self, work_order_number: str) -> Optional[Maintenance]:
        """Find maintenance by work order number."""
        maintenance_doc = await self.collection.find_one({"work_order_number": work_order_number})
        if maintenance_doc:
            maintenance_doc = convert_objectid_to_str(maintenance_doc)
            return Maintenance(**maintenance_doc)
        return None

    async def update(self, maintenance_id: str, updates: dict) -> Optional[Maintenance]:
        """Update maintenance record."""
        if not ObjectId.is_valid(maintenance_id):
            return None
        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(maintenance_id)}, {"$set": updates}
        )
        return await self.find_by_id(maintenance_id)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        asset_id: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Maintenance]:
        """List maintenance records with filtering."""
        query = {}
        if asset_id:
            query["asset_id"] = asset_id
        if status:
            query["status"] = status
        if assigned_to:
            query["assigned_to"] = assigned_to
        if priority:
            query["priority"] = priority

        cursor = self.collection.find(query).sort("scheduled_date", 1).skip(skip).limit(limit)
        maintenance_records = []
        async for maintenance_doc in cursor:
            maintenance_doc = convert_objectid_to_str(maintenance_doc)
            maintenance_records.append(Maintenance(**maintenance_doc))
        return maintenance_records

    async def find_upcoming(self, days: int = 7) -> List[Maintenance]:
        """Find upcoming maintenance records."""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days)

        query = {
            "status": {"$in": ["scheduled", "in_progress"]},
            "scheduled_date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }

        cursor = self.collection.find(query).sort("scheduled_date", 1)
        maintenance_records = []
        async for maintenance_doc in cursor:
            maintenance_doc = convert_objectid_to_str(maintenance_doc)
            maintenance_records.append(Maintenance(**maintenance_doc))
        return maintenance_records
