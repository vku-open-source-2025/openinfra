"""MongoDB implementation of sensor data repository."""
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.domain.models.iot_sensor import SensorReading
from app.domain.repositories.sensor_data_repository import SensorDataRepository
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str
from datetime import datetime


class MongoSensorDataRepository(SensorDataRepository):
    """MongoDB sensor data repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["sensor_data"]

    async def create(self, reading_data: dict) -> SensorReading:
        """Create a new sensor reading."""
        result = await self.collection.insert_one(reading_data)
        reading_doc = await self.collection.find_one({"_id": result.inserted_id})
        reading_doc = convert_objectid_to_str(reading_doc)
        return SensorReading(**reading_doc)

    async def get_readings(
        self,
        sensor_id: str,
        from_time: datetime,
        to_time: datetime,
        limit: int = 1000
    ) -> List[SensorReading]:
        """Get sensor readings in time range."""
        query = {
            "sensor_id": sensor_id,
            "timestamp": {
                "$gte": from_time,
                "$lte": to_time
            }
        }

        cursor = self.collection.find(query).sort("timestamp", -1).limit(limit)
        readings = []
        async for reading_doc in cursor:
            reading_doc = convert_objectid_to_str(reading_doc)
            readings.append(SensorReading(**reading_doc))
        return readings

    async def aggregate_readings(
        self,
        sensor_id: str,
        from_time: datetime,
        to_time: datetime,
        granularity: str = "hour"
    ) -> List[dict]:
        """Aggregate sensor readings."""
        # Determine group key based on granularity
        if granularity == "minute":
            group_format = {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"},
                          "day": {"$dayOfMonth": "$timestamp"}, "hour": {"$hour": "$timestamp"},
                          "minute": {"$minute": "$timestamp"}}
        elif granularity == "hour":
            group_format = {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"},
                          "day": {"$dayOfMonth": "$timestamp"}, "hour": {"$hour": "$timestamp"}}
        else:  # day
            group_format = {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"},
                          "day": {"$dayOfMonth": "$timestamp"}}

        pipeline = [
            {
                "$match": {
                    "sensor_id": sensor_id,
                    "timestamp": {"$gte": from_time, "$lte": to_time}
                }
            },
            {
                "$group": {
                    "_id": group_format,
                    "min": {"$min": "$value"},
                    "max": {"$max": "$value"},
                    "avg": {"$avg": "$value"},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        results = []
        async for doc in self.collection.aggregate(pipeline):
            results.append({
                "timestamp": doc["_id"],
                "min": doc["min"],
                "max": doc["max"],
                "avg": doc["avg"],
                "count": doc["count"]
            })
        return results
