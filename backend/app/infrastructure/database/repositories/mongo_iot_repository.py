"""MongoDB implementation of IoT sensor repository."""
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.domain.models.iot_sensor import IoTSensor
from app.domain.repositories.iot_repository import IoTSensorRepository
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str
from datetime import datetime, timedelta


class MongoIoTSensorRepository(IoTSensorRepository):
    """MongoDB IoT sensor repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["iot_sensors"]

    async def create(self, sensor_data: dict) -> IoTSensor:
        """Create a new sensor."""
        sensor_data["created_at"] = datetime.utcnow()
        sensor_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(sensor_data)
        sensor_doc = await self.collection.find_one({"_id": result.inserted_id})
        sensor_doc = convert_objectid_to_str(sensor_doc)
        return IoTSensor(**sensor_doc)

    async def find_by_id(self, sensor_id: str) -> Optional[IoTSensor]:
        """Find sensor by ID."""
        if not ObjectId.is_valid(sensor_id):
            return None
        sensor_doc = await self.collection.find_one({"_id": ObjectId(sensor_id)})
        if sensor_doc:
            sensor_doc = convert_objectid_to_str(sensor_doc)
            return IoTSensor(**sensor_doc)
        return None

    async def find_by_code(self, sensor_code: str) -> Optional[IoTSensor]:
        """Find sensor by code."""
        sensor_doc = await self.collection.find_one({"sensor_code": sensor_code})
        if sensor_doc:
            sensor_doc = convert_objectid_to_str(sensor_doc)
            return IoTSensor(**sensor_doc)
        return None

    async def update(self, sensor_id: str, updates: dict) -> Optional[IoTSensor]:
        """Update sensor."""
        if not ObjectId.is_valid(sensor_id):
            return None
        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(sensor_id)}, {"$set": updates}
        )
        return await self.find_by_id(sensor_id)

    async def delete(self, sensor_id: str) -> bool:
        """Delete sensor."""
        if not ObjectId.is_valid(sensor_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(sensor_id)})
        return result.deleted_count > 0

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        asset_id: Optional[str] = None,
        sensor_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[IoTSensor]:
        """List sensors with filtering."""
        query = {}
        if asset_id:
            query["asset_id"] = asset_id
        if sensor_type:
            query["sensor_type"] = sensor_type
        if status:
            query["status"] = status

        cursor = self.collection.find(query).skip(skip).limit(limit)
        sensors = []
        async for sensor_doc in cursor:
            sensor_doc = convert_objectid_to_str(sensor_doc)
            sensors.append(IoTSensor(**sensor_doc))
        return sensors

    async def update_last_seen(self, sensor_id: str, timestamp: datetime) -> bool:
        """Update sensor last seen timestamp."""
        if not ObjectId.is_valid(sensor_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(sensor_id)},
            {"$set": {"last_seen": timestamp, "status": "online", "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def find_offline_sensors(self, threshold_minutes: int = 15) -> List[IoTSensor]:
        """Find sensors that haven't reported in threshold minutes."""
        threshold_time = datetime.utcnow() - timedelta(minutes=threshold_minutes)
        query = {
            "$or": [
                {"last_seen": {"$lt": threshold_time}},
                {"last_seen": None}
            ],
            "status": {"$ne": "maintenance"}
        }

        cursor = self.collection.find(query)
        sensors = []
        async for sensor_doc in cursor:
            sensor_doc = convert_objectid_to_str(sensor_doc)
            sensors.append(IoTSensor(**sensor_doc))
        return sensors
