"""MongoDB implementation for after-action report repository."""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import DESCENDING

from app.domain.models.after_action_report import AfterActionReport
from app.domain.repositories.after_action_report_repository import AfterActionReportRepository
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str


class MongoAfterActionReportRepository(AfterActionReportRepository):
    """Mongo repository for after-action reports."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["after_action_reports"]

    async def ensure_indexes(self):
        """Ensure indexes for query patterns."""
        await self.collection.create_index(
            [("emergency_event_id", DESCENDING), ("created_at", DESCENDING)],
            name="idx_aar_event_created",
        )
        await self.collection.create_index(
            [("status", DESCENDING), ("updated_at", DESCENDING)],
            name="idx_aar_status_updated",
        )
        await self.collection.create_index("report_code", unique=True, name="uidx_aar_report_code")

    async def create(self, payload: dict) -> AfterActionReport:
        """Create after-action report."""
        now = datetime.utcnow()
        payload["created_at"] = now
        payload["updated_at"] = now

        result = await self.collection.insert_one(payload)
        doc = await self.collection.find_one({"_id": result.inserted_id})
        doc = convert_objectid_to_str(doc)
        return AfterActionReport(**doc)

    async def find_by_id(self, report_id: str) -> Optional[AfterActionReport]:
        """Find report by id."""
        if not ObjectId.is_valid(report_id):
            return None

        doc = await self.collection.find_one({"_id": ObjectId(report_id)})
        if not doc:
            return None

        doc = convert_objectid_to_str(doc)
        return AfterActionReport(**doc)

    async def find_latest_by_event(self, emergency_event_id: str) -> Optional[AfterActionReport]:
        """Find latest report for one event."""
        doc = await self.collection.find_one(
            {"emergency_event_id": emergency_event_id},
            sort=[("created_at", -1)],
        )
        if not doc:
            return None

        doc = convert_objectid_to_str(doc)
        return AfterActionReport(**doc)

    async def update(self, report_id: str, updates: dict) -> Optional[AfterActionReport]:
        """Update report by id."""
        if not ObjectId.is_valid(report_id):
            return None

        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one({"_id": ObjectId(report_id)}, {"$set": updates})
        return await self.find_by_id(report_id)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[AfterActionReport]:
        """List reports with optional filtering."""
        query = {}
        if emergency_event_id:
            query["emergency_event_id"] = emergency_event_id
        if status:
            query["status"] = status

        cursor = self.collection.find(query).sort("updated_at", -1).skip(skip).limit(limit)

        items: List[AfterActionReport] = []
        async for doc in cursor:
            doc = convert_objectid_to_str(doc)
            items.append(AfterActionReport(**doc))
        return items
