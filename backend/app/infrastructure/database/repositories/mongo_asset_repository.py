"""MongoDB implementation of asset repository."""

from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.domain.models.asset import Asset
from app.domain.repositories.asset_repository import AssetRepository
from app.infrastructure.database.repositories.base_repository import (
    convert_objectid_to_str,
)
from datetime import datetime


class MongoAssetRepository(AssetRepository):
    """MongoDB asset repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["assets"]

    async def create(self, asset_data: dict) -> Asset:
        """Create a new asset."""
        asset_data["created_at"] = datetime.utcnow()
        asset_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(asset_data)
        asset_doc = await self.collection.find_one({"_id": result.inserted_id})
        asset_doc = convert_objectid_to_str(asset_doc)
        # Handle legacy data - generate missing fields
        if "asset_code" not in asset_doc or not asset_doc["asset_code"]:
            feature_code = asset_doc.get("feature_code", "ASSET")
            asset_doc["asset_code"] = (
                f"{feature_code}-{int(datetime.utcnow().timestamp())}"
            )
        if "name" not in asset_doc or not asset_doc["name"]:
            feature_type = asset_doc.get("feature_type", "Asset")
            asset_doc["name"] = f"{feature_type} (Legacy)"
        return Asset(**asset_doc)

    async def find_by_id(self, asset_id: str) -> Optional[Asset]:
        """Find asset by ID."""
        if not ObjectId.is_valid(asset_id):
            return None
        asset_doc = await self.collection.find_one({"_id": ObjectId(asset_id)})
        if asset_doc:
            asset_doc = convert_objectid_to_str(asset_doc)
            # Handle legacy data - generate missing fields
            if "asset_code" not in asset_doc or not asset_doc.get("asset_code"):
                feature_code = asset_doc.get("feature_code", "ASSET")
                asset_doc["asset_code"] = (
                    f"{feature_code}-{int(datetime.utcnow().timestamp())}"
                )
            if "name" not in asset_doc or not asset_doc.get("name"):
                feature_type = asset_doc.get("feature_type", "Asset")
                asset_doc["name"] = f"{feature_type} (Legacy)"
            return Asset(**asset_doc)
        return None

    async def find_by_code(self, asset_code: str) -> Optional[Asset]:
        """Find asset by code."""
        asset_doc = await self.collection.find_one({"asset_code": asset_code})
        if asset_doc:
            asset_doc = convert_objectid_to_str(asset_doc)
            # Handle legacy data - generate missing fields
            if "name" not in asset_doc or not asset_doc.get("name"):
                feature_type = asset_doc.get("feature_type", "Asset")
                asset_doc["name"] = f"{feature_type} (Legacy)"
            return Asset(**asset_doc)
        return None

    async def update(self, asset_id: str, updates: dict) -> Optional[Asset]:
        """Update asset."""
        if not ObjectId.is_valid(asset_id):
            return None
        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one({"_id": ObjectId(asset_id)}, {"$set": updates})
        return await self.find_by_id(asset_id)

    async def delete(self, asset_id: str) -> bool:
        """Delete asset (soft delete by setting status to retired)."""
        if not ObjectId.is_valid(asset_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(asset_id)},
            {"$set": {"status": "retired", "updated_at": datetime.utcnow()}},
        )
        return result.modified_count > 0

    async def list(
        self, skip: int = 0, limit: int = 10000, filters: Optional[dict] = None
    ) -> List[Asset]:
        """List assets with pagination and filtering."""
        query = filters or {}
        cursor = self.collection.find(query).skip(skip).limit(limit)
        assets = []
        async for asset_doc in cursor:
            asset_doc = convert_objectid_to_str(asset_doc)
            # Handle legacy data - generate missing fields
            if "asset_code" not in asset_doc or not asset_doc.get("asset_code"):
                feature_code = asset_doc.get("feature_code", "ASSET")
                asset_doc["asset_code"] = (
                    f"{feature_code}-{int(datetime.utcnow().timestamp())}"
                )
            if "name" not in asset_doc or not asset_doc.get("name"):
                feature_type = asset_doc.get("feature_type", "Asset")
                asset_doc["name"] = f"{feature_type} (Legacy)"
            assets.append(Asset(**asset_doc))
        return assets

    async def add_attachment(self, asset_id: str, attachment: dict) -> bool:
        """Add attachment to asset."""
        if not ObjectId.is_valid(asset_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(asset_id)},
            {
                "$push": {"attachments": attachment},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )
        return result.modified_count > 0

    async def remove_attachment(self, asset_id: str, attachment_url: str) -> bool:
        """Remove attachment from asset."""
        if not ObjectId.is_valid(asset_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(asset_id)},
            {
                "$pull": {"attachments": {"file_url": attachment_url}},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )
        return result.modified_count > 0
