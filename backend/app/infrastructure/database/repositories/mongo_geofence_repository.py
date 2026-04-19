"""MongoDB implementation of geofence repository."""

from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from app.domain.models.geofence import Geofence
from app.domain.models.geofence_alert_event import GeofenceAlertEvent
from app.domain.repositories.geofence_repository import GeofenceRepository
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str


class MongoGeofenceRepository(GeofenceRepository):
    """MongoDB geofence repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["geofences"]
        self.alert_event_collection = db["geofence_alert_events"]

    async def ensure_indexes(self):
        """Ensure geofence indexes."""
        await self.collection.create_index(
            [("polygon", "2dsphere")],
            name="idx_geofence_polygon",
        )
        await self.collection.create_index(
            [("is_active", ASCENDING), ("updated_at", DESCENDING)],
            name="idx_geofence_active_updated",
        )
        await self.alert_event_collection.create_index(
            [("geofence_id", ASCENDING), ("hazard_layer_id", ASCENDING), ("triggered_at", DESCENDING)],
            name="idx_geofence_alert_recent",
        )

    async def create(self, payload: dict) -> Geofence:
        """Create geofence."""
        now = datetime.utcnow()
        payload["created_at"] = now
        payload["updated_at"] = now

        result = await self.collection.insert_one(payload)
        doc = await self.collection.find_one({"_id": result.inserted_id})
        doc = convert_objectid_to_str(doc)
        return Geofence(**doc)

    async def find_by_id(self, geofence_id: str) -> Optional[Geofence]:
        """Find geofence by id."""
        if not ObjectId.is_valid(geofence_id):
            return None

        doc = await self.collection.find_one({"_id": ObjectId(geofence_id)})
        if not doc:
            return None

        doc = convert_objectid_to_str(doc)
        return Geofence(**doc)

    async def update(self, geofence_id: str, updates: dict) -> Optional[Geofence]:
        """Update geofence by id."""
        if not ObjectId.is_valid(geofence_id):
            return None

        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(geofence_id)},
            {"$set": updates},
        )
        return await self.find_by_id(geofence_id)

    async def delete(self, geofence_id: str) -> bool:
        """Delete geofence by id."""
        if not ObjectId.is_valid(geofence_id):
            return False

        result = await self.collection.delete_one({"_id": ObjectId(geofence_id)})
        return result.deleted_count > 0

    async def list(self, skip: int = 0, limit: int = 100) -> List[Geofence]:
        """List geofences."""
        cursor = self.collection.find({}).sort("updated_at", -1).skip(skip).limit(limit)
        items: List[Geofence] = []
        async for doc in cursor:
            doc = convert_objectid_to_str(doc)
            items.append(Geofence(**doc))
        return items

    async def list_active(self) -> List[Geofence]:
        """List active geofences."""
        cursor = self.collection.find({"is_active": True})
        items: List[Geofence] = []
        async for doc in cursor:
            doc = convert_objectid_to_str(doc)
            items.append(Geofence(**doc))
        return items

    async def find_matching_hazard(
        self,
        hazard_geometry: Optional[dict],
        district: Optional[str] = None,
        ward: Optional[str] = None,
    ) -> List[Geofence]:
        """Find geofences matching hazard location context."""
        matched: List[Geofence] = []
        seen_ids = set()

        if hazard_geometry:
            geo_query = {
                "is_active": True,
                "polygon": {
                    "$geoIntersects": {
                        "$geometry": hazard_geometry,
                    }
                },
            }
            cursor = self.collection.find(geo_query)
            async for doc in cursor:
                doc = convert_objectid_to_str(doc)
                geofence = Geofence(**doc)
                if geofence.id and geofence.id not in seen_ids:
                    matched.append(geofence)
                    seen_ids.add(geofence.id)

        fallback_query = {"is_active": True}
        district_or_ward = []
        if district:
            district_or_ward.append({"district": district})
        if ward:
            district_or_ward.append({"ward": ward})

        if district_or_ward:
            fallback_query["$or"] = district_or_ward
            cursor = self.collection.find(fallback_query)
            async for doc in cursor:
                doc = convert_objectid_to_str(doc)
                geofence = Geofence(**doc)
                if geofence.id and geofence.id not in seen_ids:
                    matched.append(geofence)
                    seen_ids.add(geofence.id)

        return matched

    async def has_recent_alert(
        self,
        geofence_id: str,
        hazard_layer_id: str,
        since: datetime,
    ) -> bool:
        """Check if alert was already triggered recently."""
        doc = await self.alert_event_collection.find_one(
            {
                "geofence_id": geofence_id,
                "hazard_layer_id": hazard_layer_id,
                "triggered_at": {"$gte": since},
            }
        )
        return doc is not None

    async def create_alert_event(self, payload: dict) -> GeofenceAlertEvent:
        """Create geofence alert event audit row."""
        payload["triggered_at"] = payload.get("triggered_at") or datetime.utcnow()
        result = await self.alert_event_collection.insert_one(payload)
        doc = await self.alert_event_collection.find_one({"_id": result.inserted_id})
        doc = convert_objectid_to_str(doc)
        return GeofenceAlertEvent(**doc)
