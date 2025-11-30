"""MongoDB implementation of alert repository."""
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.domain.models.alert import Alert
from app.domain.repositories.alert_repository import AlertRepository
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str
from datetime import datetime


class MongoAlertRepository(AlertRepository):
    """MongoDB alert repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["alerts"]

    async def create(self, alert_data: dict) -> Alert:
        """Create a new alert."""
        alert_data["created_at"] = datetime.utcnow()
        alert_data["updated_at"] = datetime.utcnow()
        if "triggered_at" not in alert_data:
            alert_data["triggered_at"] = datetime.utcnow()
        result = await self.collection.insert_one(alert_data)
        alert_doc = await self.collection.find_one({"_id": result.inserted_id})
        alert_doc = convert_objectid_to_str(alert_doc)
        return Alert(**alert_doc)

    async def find_by_id(self, alert_id: str) -> Optional[Alert]:
        """Find alert by ID."""
        if not ObjectId.is_valid(alert_id):
            return None
        alert_doc = await self.collection.find_one({"_id": ObjectId(alert_id)})
        if alert_doc:
            alert_doc = convert_objectid_to_str(alert_doc)
            return Alert(**alert_doc)
        return None

    async def update(self, alert_id: str, updates: dict) -> Optional[Alert]:
        """Update alert."""
        if not ObjectId.is_valid(alert_id):
            return None
        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(alert_id)}, {"$set": updates}
        )
        return await self.find_by_id(alert_id)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        asset_id: Optional[str] = None
    ) -> List[Alert]:
        """List alerts with filtering."""
        query = {}
        if status:
            query["status"] = status
        if severity:
            query["severity"] = severity
        if asset_id:
            query["asset_id"] = asset_id

        cursor = self.collection.find(query).sort("triggered_at", -1).skip(skip).limit(limit)
        alerts = []
        async for alert_doc in cursor:
            alert_doc = convert_objectid_to_str(alert_doc)
            alerts.append(Alert(**alert_doc))
        return alerts
