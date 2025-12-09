"""MongoDB implementation of SOSA Sensor Metadata repository."""
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from app.domain.models.sosa_metadata import SensorMetadata
from app.domain.repositories.sosa_metadata_repository import SensorMetadataRepository
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str


class MongoSensorMetadataRepository(SensorMetadataRepository):
    """MongoDB SOSA Sensor Metadata repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["sensors_metadata"]

    async def create(self, metadata: dict) -> SensorMetadata:
        """Create sensor metadata entry."""
        metadata["created_at"] = datetime.utcnow()
        metadata["updated_at"] = datetime.utcnow()
        
        # Use sensor_id as _id for direct lookup
        if "sensor_id" in metadata and "_id" not in metadata:
            metadata["_id"] = metadata.pop("sensor_id")
        
        await self.collection.insert_one(metadata)
        return SensorMetadata(**metadata)

    async def find_by_sensor_id(self, sensor_id: str) -> Optional[SensorMetadata]:
        """Find metadata by sensor ID (same as _id)."""
        doc = await self.collection.find_one({"_id": sensor_id})
        if doc:
            return SensorMetadata(**doc)
        return None

    async def find_by_feature_of_interest(self, feature_id: str) -> List[SensorMetadata]:
        """Find all sensors observing a specific feature (asset)."""
        cursor = self.collection.find({"has_feature_of_interest.id": feature_id})
        result = []
        async for doc in cursor:
            result.append(SensorMetadata(**doc))
        return result

    async def find_by_observable_property(self, property_uri: str) -> List[SensorMetadata]:
        """Find all sensors measuring a specific property."""
        cursor = self.collection.find({"observes": property_uri})
        result = []
        async for doc in cursor:
            result.append(SensorMetadata(**doc))
        return result

    async def find_by_platform(self, platform_id: str) -> List[SensorMetadata]:
        """Find all sensors on a platform."""
        cursor = self.collection.find({"is_hosted_by": platform_id})
        result = []
        async for doc in cursor:
            result.append(SensorMetadata(**doc))
        return result

    async def update(self, sensor_id: str, updates: dict) -> Optional[SensorMetadata]:
        """Update sensor metadata."""
        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one({"_id": sensor_id}, {"$set": updates})
        return await self.find_by_sensor_id(sensor_id)

    async def delete(self, sensor_id: str) -> bool:
        """Delete sensor metadata."""
        result = await self.collection.delete_one({"_id": sensor_id})
        return result.deleted_count > 0

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        observes: Optional[str] = None,
        feature_id: Optional[str] = None
    ) -> List[SensorMetadata]:
        """List sensor metadata with filtering."""
        query = {}
        if observes:
            query["observes"] = observes
        if feature_id:
            query["has_feature_of_interest.id"] = feature_id

        cursor = self.collection.find(query).skip(skip).limit(limit)
        result = []
        async for doc in cursor:
            result.append(SensorMetadata(**doc))
        return result

    async def exists(self, sensor_id: str) -> bool:
        """Check if metadata exists for sensor."""
        count = await self.collection.count_documents({"_id": sensor_id}, limit=1)
        return count > 0

    async def bulk_create(self, metadata_list: List[dict]) -> int:
        """Bulk create metadata entries. Returns count of created entries."""
        if not metadata_list:
            return 0
        
        now = datetime.utcnow()
        for metadata in metadata_list:
            metadata["created_at"] = now
            metadata["updated_at"] = now
            if "sensor_id" in metadata and "_id" not in metadata:
                metadata["_id"] = metadata.pop("sensor_id")
        
        # Use ordered=False to continue on duplicates
        try:
            result = await self.collection.insert_many(metadata_list, ordered=False)
            return len(result.inserted_ids)
        except Exception as e:
            # Handle duplicate key errors
            if "duplicate key" in str(e).lower():
                # Count successful inserts from the error
                return getattr(e, "details", {}).get("nInserted", 0)
            raise

    async def ensure_indexes(self):
        """Create indexes for efficient queries."""
        await self.collection.create_index("observes")
        await self.collection.create_index("has_feature_of_interest.id")
        await self.collection.create_index("is_hosted_by")
        await self.collection.create_index("type")
