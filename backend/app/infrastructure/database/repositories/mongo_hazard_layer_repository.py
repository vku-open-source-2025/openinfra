"""MongoDB implementation of hazard layer repository."""

from datetime import datetime
from typing import Dict, List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from app.domain.models.hazard_layer import HazardLayer
from app.domain.repositories.hazard_layer_repository import HazardLayerRepository
from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str


class MongoHazardLayerRepository(HazardLayerRepository):
    """MongoDB hazard layer repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["hazard_layers"]

    async def ensure_indexes(self):
        """Ensure indexes for hazard queries."""
        await self.collection.create_index(
            [("source", ASCENDING), ("hazard_id", ASCENDING)],
            unique=True,
            name="uq_source_hazard_id",
        )
        await self.collection.create_index(
            [("geometry", "2dsphere")],
            name="idx_hazard_geometry",
            sparse=True,
        )
        await self.collection.create_index(
            [("is_active", ASCENDING), ("updated_at", DESCENDING)],
            name="idx_hazard_active_updated",
        )
        await self.collection.create_index(
            [("event_type", ASCENDING), ("severity", ASCENDING)],
            name="idx_hazard_event_severity",
        )
        await self.collection.create_index(
            [("expires_at", ASCENDING)],
            name="idx_hazard_expires_at",
        )

    async def create(self, payload: dict) -> HazardLayer:
        """Create a hazard layer record."""
        now = datetime.utcnow()
        payload["created_at"] = now
        payload["updated_at"] = now

        result = await self.collection.insert_one(payload)
        doc = await self.collection.find_one({"_id": result.inserted_id})
        doc = convert_objectid_to_str(doc)
        return HazardLayer(**doc)

    async def find_by_id(self, hazard_db_id: str) -> Optional[HazardLayer]:
        """Find hazard by database id."""
        if not ObjectId.is_valid(hazard_db_id):
            return None

        doc = await self.collection.find_one({"_id": ObjectId(hazard_db_id)})
        if not doc:
            return None

        doc = convert_objectid_to_str(doc)
        return HazardLayer(**doc)

    async def find_by_source_hazard_id(
        self,
        source: str,
        hazard_id: str,
    ) -> Optional[HazardLayer]:
        """Find hazard by source + source hazard id."""
        doc = await self.collection.find_one({"source": source, "hazard_id": hazard_id})
        if not doc:
            return None

        doc = convert_objectid_to_str(doc)
        return HazardLayer(**doc)

    async def update(self, hazard_db_id: str, updates: dict) -> Optional[HazardLayer]:
        """Update hazard by database id."""
        if not ObjectId.is_valid(hazard_db_id):
            return None

        updates["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(hazard_db_id)},
            {"$set": updates},
        )
        return await self.find_by_id(hazard_db_id)

    async def bulk_upsert(self, payloads: List[dict]) -> Dict[str, int]:
        """Bulk upsert hazards by source + hazard_id."""
        inserted = 0
        updated = 0
        affected_ids: List[str] = []

        for payload in payloads:
            source = payload.get("source")
            hazard_id = payload.get("hazard_id")
            if not source or not hazard_id:
                continue

            now = datetime.utcnow()
            payload["updated_at"] = now
            result = await self.collection.update_one(
                {"source": source, "hazard_id": hazard_id},
                {
                    "$set": payload,
                    "$setOnInsert": {"created_at": now},
                },
                upsert=True,
            )

            if result.upserted_id is not None:
                inserted += 1
                affected_ids.append(str(result.upserted_id))
            elif result.matched_count > 0:
                updated += 1
                existing = await self.collection.find_one(
                    {"source": source, "hazard_id": hazard_id},
                    {"_id": 1},
                )
                if existing and existing.get("_id"):
                    affected_ids.append(str(existing["_id"]))

        return {
            "total": inserted + updated,
            "inserted": inserted,
            "updated": updated,
            "hazard_db_ids": affected_ids,
        }

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        source: Optional[str] = None,
        district: Optional[str] = None,
        ward: Optional[str] = None,
    ) -> List[HazardLayer]:
        """List hazards with optional filtering."""
        query = {}
        if active_only:
            query["is_active"] = True
        if event_type:
            query["event_type"] = event_type
        if severity:
            query["severity"] = severity
        if source:
            query["source"] = source
        if district:
            query["district"] = district
        if ward:
            query["ward"] = ward

        cursor = (
            self.collection.find(query)
            .sort("updated_at", -1)
            .skip(skip)
            .limit(limit)
        )

        hazards: List[HazardLayer] = []
        async for doc in cursor:
            doc = convert_objectid_to_str(doc)
            hazards.append(HazardLayer(**doc))

        return hazards

    async def list_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int,
        limit: int = 100,
    ) -> List[HazardLayer]:
        """List hazards near a coordinate."""
        pipeline = [
            {
                "$geoNear": {
                    "near": {
                        "type": "Point",
                        "coordinates": [longitude, latitude],
                    },
                    "distanceField": "distance_meters",
                    "maxDistance": radius_meters,
                    "spherical": True,
                    "query": {"is_active": True, "geometry": {"$ne": None}},
                }
            },
            {"$sort": {"distance_meters": 1}},
            {"$limit": limit},
        ]

        hazards: List[HazardLayer] = []
        try:
            async for doc in self.collection.aggregate(pipeline):
                doc = convert_objectid_to_str(doc)
                hazards.append(HazardLayer(**doc))
        except Exception:
            # Fallback to non-geo list when geo index is not ready.
            hazards = await self.list(skip=0, limit=limit, active_only=True)

        return hazards

    async def list_in_polygon(self, polygon: dict, limit: int = 500) -> List[HazardLayer]:
        """List hazards inside a polygon geometry."""
        query = {
            "is_active": True,
            "geometry": {
                "$geoWithin": {
                    "$geometry": polygon,
                }
            },
        }

        cursor = self.collection.find(query).limit(limit)
        hazards: List[HazardLayer] = []
        async for doc in cursor:
            doc = convert_objectid_to_str(doc)
            hazards.append(HazardLayer(**doc))

        return hazards

    async def deactivate_expired(self, cutoff: Optional[datetime] = None) -> int:
        """Deactivate expired hazards and return updated count."""
        cutoff_time = cutoff or datetime.utcnow()
        result = await self.collection.update_many(
            {
                "is_active": True,
                "expires_at": {"$lte": cutoff_time},
            },
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return int(result.modified_count)
