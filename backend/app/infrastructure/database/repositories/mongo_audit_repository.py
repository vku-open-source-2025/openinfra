"""MongoDB implementation of audit repository."""
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.domain.models.audit_log import AuditLog
from app.domain.repositories.audit_repository import AuditRepository
from datetime import datetime


class MongoAuditRepository(AuditRepository):
    """MongoDB audit repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["audit_logs"]

    async def create(self, audit_data: dict) -> AuditLog:
        """Create audit log entry."""
        audit_data["timestamp"] = datetime.utcnow()
        result = await self.collection.insert_one(audit_data)
        audit_doc = await self.collection.find_one({"_id": result.inserted_id})
        # Convert ObjectId to string for Pydantic model
        if audit_doc and "_id" in audit_doc:
            audit_doc["_id"] = str(audit_doc["_id"])
        return AuditLog(**audit_doc)

    async def get_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a resource."""
        cursor = self.collection.find(
            {"resource_type": resource_type, "resource_id": resource_id}
        ).sort("timestamp", -1).limit(limit)

        logs = []
        async for log_doc in cursor:
            # Convert ObjectId to string for Pydantic model
            if log_doc and "_id" in log_doc:
                log_doc["_id"] = str(log_doc["_id"])
            logs.append(AuditLog(**log_doc))
        return logs

    async def get_by_user(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a user."""
        cursor = self.collection.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit)

        logs = []
        async for log_doc in cursor:
            # Convert ObjectId to string for Pydantic model
            if log_doc and "_id" in log_doc:
                log_doc["_id"] = str(log_doc["_id"])
            logs.append(AuditLog(**log_doc))
        return logs
