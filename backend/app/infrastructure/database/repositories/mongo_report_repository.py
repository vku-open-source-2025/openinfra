"""MongoDB implementation of report repository."""
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.domain.models.report import Report
from app.domain.repositories.report_repository import ReportRepository
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str
from datetime import datetime


class MongoReportRepository(ReportRepository):
    """MongoDB report repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["reports"]

    async def create(self, report_data: dict) -> Report:
        """Create a new report."""
        report_data["created_at"] = datetime.utcnow()
        result = await self.collection.insert_one(report_data)
        report_doc = await self.collection.find_one({"_id": result.inserted_id})
        report_doc = convert_objectid_to_str(report_doc)
        return Report(**report_doc)

    async def find_by_id(self, report_id: str) -> Optional[Report]:
        """Find report by ID."""
        if not ObjectId.is_valid(report_id):
            return None
        report_doc = await self.collection.find_one({"_id": ObjectId(report_id)})
        if report_doc:
            report_doc = convert_objectid_to_str(report_doc)
            return Report(**report_doc)
        return None

    async def find_by_code(self, report_code: str) -> Optional[Report]:
        """Find report by code."""
        report_doc = await self.collection.find_one({"report_code": report_code})
        if report_doc:
            report_doc = convert_objectid_to_str(report_doc)
            return Report(**report_doc)
        return None

    async def update(self, report_id: str, updates: dict) -> Optional[Report]:
        """Update report."""
        if not ObjectId.is_valid(report_id):
            return None
        await self.collection.update_one(
            {"_id": ObjectId(report_id)}, {"$set": updates}
        )
        return await self.find_by_id(report_id)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Report]:
        """List reports with filtering."""
        query = {}
        if type:
            query["type"] = type
        if status:
            query["status"] = status

        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        reports = []
        async for report_doc in cursor:
            report_doc = convert_objectid_to_str(report_doc)
            reports.append(Report(**report_doc))
        return reports

    async def find_scheduled_reports(self) -> List[Report]:
        """Find reports that need to be generated."""
        query = {
            "scheduled": True,
            "status": {"$in": ["pending", "completed"]},
            "$or": [
                {"next_run": {"$lte": datetime.utcnow()}},
                {"next_run": None}
            ]
        }

        cursor = self.collection.find(query)
        reports = []
        async for report_doc in cursor:
            report_doc = convert_objectid_to_str(report_doc)
            reports.append(Report(**report_doc))
        return reports
