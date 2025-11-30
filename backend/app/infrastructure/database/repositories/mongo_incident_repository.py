"""MongoDB implementation of incident repository."""
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.domain.models.incident import Incident
from app.domain.repositories.incident_repository import IncidentRepository
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str
from datetime import datetime


class MongoIncidentRepository(IncidentRepository):
    """MongoDB incident repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["incidents"]

    async def create(self, incident_data: dict) -> Incident:
        """Create a new incident."""
        incident_data["created_at"] = datetime.utcnow()
        incident_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(incident_data)
        incident_doc = await self.collection.find_one({"_id": result.inserted_id})
        incident_doc = convert_objectid_to_str(incident_doc)
        return Incident(**incident_doc)

    async def find_by_id(self, incident_id: str) -> Optional[Incident]:
        """Find incident by ID."""
        if not ObjectId.is_valid(incident_id):
            return None
        incident_doc = await self.collection.find_one({"_id": ObjectId(incident_id)})
        if incident_doc:
            incident_doc = convert_objectid_to_str(incident_doc)
            return Incident(**incident_doc)
        return None

    async def find_by_number(self, incident_number: str) -> Optional[Incident]:
        """Find incident by number."""
        incident_doc = await self.collection.find_one({"incident_number": incident_number})
        if incident_doc:
            incident_doc = convert_objectid_to_str(incident_doc)
            return Incident(**incident_doc)
        return None

    async def update(self, incident_id: str, updates: dict) -> Optional[Incident]:
        """Update incident."""
        if not ObjectId.is_valid(incident_id):
            return None
        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(incident_id)}, {"$set": updates}
        )
        return await self.find_by_id(incident_id)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        asset_id: Optional[str] = None,
        reported_by: Optional[str] = None
    ) -> List[Incident]:
        """List incidents with filtering."""
        query = {}
        if status:
            query["status"] = status
        if severity:
            query["severity"] = severity
        if asset_id:
            query["asset_id"] = asset_id
        if reported_by:
            query["reported_by"] = reported_by

        cursor = self.collection.find(query).sort("reported_at", -1).skip(skip).limit(limit)
        incidents = []
        async for incident_doc in cursor:
            incident_doc = convert_objectid_to_str(incident_doc)
            incidents.append(Incident(**incident_doc))
        return incidents

    async def add_comment(self, incident_id: str, comment: dict) -> bool:
        """Add comment to incident."""
        if not ObjectId.is_valid(incident_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(incident_id)},
            {"$push": {"comments": comment}, "$set": {"updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def upvote(self, incident_id: str, user_id: str) -> bool:
        """Upvote an incident."""
        if not ObjectId.is_valid(incident_id):
            return False
        # Check if already upvoted
        incident = await self.find_by_id(incident_id)
        if incident and user_id in incident.upvoted_by:
            # Remove upvote
            result = await self.collection.update_one(
                {"_id": ObjectId(incident_id)},
                {
                    "$pull": {"upvoted_by": user_id},
                    "$inc": {"upvotes": -1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        else:
            # Add upvote
            result = await self.collection.update_one(
                {"_id": ObjectId(incident_id)},
                {
                    "$addToSet": {"upvoted_by": user_id},
                    "$inc": {"upvotes": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        return result.modified_count > 0
