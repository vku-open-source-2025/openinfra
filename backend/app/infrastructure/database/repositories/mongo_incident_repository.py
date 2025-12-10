"""MongoDB implementation of incident repository."""

from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.domain.models.incident import Incident, AssetSummary
from app.domain.repositories.incident_repository import IncidentRepository
from app.infrastructure.database.repositories.base_repository import (
    convert_objectid_to_str,
)
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MongoIncidentRepository(IncidentRepository):
    """MongoDB incident repository implementation."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["incidents"]
        self.assets_collection = db["assets"]
        self.users_collection = db["users"]

    async def _populate_asset(self, incident_doc: dict) -> dict:
        """Populate asset summary for an incident."""
        if incident_doc.get("asset_id") and ObjectId.is_valid(incident_doc["asset_id"]):
            asset_doc = await self.assets_collection.find_one(
                {"_id": ObjectId(incident_doc["asset_id"])},
                {
                    "_id": 1,
                    "asset_code": 1,
                    "name": 1,
                    "feature_type": 1,
                    "category": 1,
                    "status": 1,
                },
            )
            if asset_doc:
                incident_doc["asset"] = {
                    "id": str(asset_doc["_id"]),
                    "asset_code": asset_doc.get("asset_code"),
                    "name": asset_doc.get("name"),
                    "feature_type": asset_doc.get("feature_type", "Unknown"),
                    "category": asset_doc.get("category"),
                    "status": asset_doc.get("status"),
                }
        return incident_doc

    async def _populate_comment_users(self, incident_doc: dict) -> dict:
        """Populate user names in comments."""
        if not incident_doc.get("comments"):
            return incident_doc

        # Collect unique user IDs from comments
        user_ids = set()
        for comment in incident_doc["comments"]:
            user_id = comment.get("user_id")
            if user_id:
                # Handle both ObjectId and string formats
                if isinstance(user_id, ObjectId):
                    user_id_str = str(user_id)
                    user_ids.add(user_id_str)
                elif isinstance(user_id, str) and ObjectId.is_valid(user_id):
                    user_ids.add(user_id)
                else:
                    logger.debug(
                        f"Invalid user_id format in comment: {user_id} (type: {type(user_id)})"
                    )

        # Fetch all users at once
        user_map = {}
        if user_ids:
            try:
                object_ids = [
                    ObjectId(uid) for uid in user_ids if ObjectId.is_valid(uid)
                ]
                if object_ids:
                    user_cursor = self.users_collection.find(
                        {"_id": {"$in": object_ids}},
                        {"_id": 1, "full_name": 1, "username": 1},
                    )
                    async for user_doc in user_cursor:
                        user_id_str = str(user_doc["_id"])
                        user_map[user_id_str] = {
                            "full_name": user_doc.get("full_name"),
                            "username": user_doc.get("username"),
                        }
                    logger.debug(
                        f"Populated {len(user_map)} user names from {len(user_ids)} user IDs"
                    )
            except Exception as e:
                logger.warning(f"Error populating comment users: {e}", exc_info=True)

        # Populate user names in comments
        for comment in incident_doc["comments"]:
            user_id = comment.get("user_id")
            if user_id:
                # Normalize user_id to string for comparison
                user_id_str = str(user_id) if isinstance(user_id, ObjectId) else user_id
                if user_id_str in user_map:
                    user_info = user_map[user_id_str]
                    comment["user_name"] = user_info.get("full_name") or user_info.get(
                        "username"
                    )
                    logger.debug(
                        f"Populated user_name '{comment.get('user_name')}' for user_id '{user_id_str}'"
                    )
                else:
                    logger.debug(
                        f"User not found for user_id '{user_id_str}' in comment"
                    )

        return incident_doc

    async def create(self, incident_data: dict) -> Incident:
        """Create a new incident."""
        incident_data["created_at"] = datetime.utcnow()
        incident_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(incident_data)
        incident_doc = await self.collection.find_one({"_id": result.inserted_id})
        incident_doc = convert_objectid_to_str(incident_doc)
        return Incident(**incident_doc)

    async def find_by_id(
        self, incident_id: str, populate_asset: bool = False
    ) -> Optional[Incident]:
        """Find incident by ID."""
        if not ObjectId.is_valid(incident_id):
            return None
        incident_doc = await self.collection.find_one({"_id": ObjectId(incident_id)})
        if incident_doc:
            if populate_asset:
                incident_doc = await self._populate_asset(incident_doc)
            incident_doc = await self._populate_comment_users(incident_doc)
            incident_doc = convert_objectid_to_str(incident_doc)
            return Incident(**incident_doc)
        return None

    async def find_by_number(self, incident_number: str) -> Optional[Incident]:
        """Find incident by number."""
        incident_doc = await self.collection.find_one(
            {"incident_number": incident_number}
        )
        if incident_doc:
            incident_doc = await self._populate_comment_users(incident_doc)
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
        # Use find_by_id which will populate comment users
        return await self.find_by_id(incident_id, populate_asset=False)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        asset_id: Optional[str] = None,
        reported_by: Optional[str] = None,
        populate_asset: bool = False,
        verification_status: Optional[str] = None,
    ) -> List[Incident]:
        """List incidents with filtering, sorted by severity (critical > high > medium > low).
        Excludes incidents with status 'closed' unless explicitly requested."""
        query = {}
        if status:
            # If status is explicitly set, use it (even if it's 'closed')
            query["status"] = status
        else:
            # Exclude closed incidents when no status filter is provided
            query["status"] = {"$ne": "closed"}
        if severity:
            query["severity"] = severity
        if asset_id:
            query["asset_id"] = asset_id
        if reported_by:
            query["reported_by"] = reported_by
        if verification_status:
            query["ai_verification_status"] = verification_status

        # Use aggregation pipeline to sort by severity order
        # Map severity to numeric value: critical=0, high=1, medium=2, low=3
        pipeline = [
            {"$match": query},
            {
                "$addFields": {
                    "severity_order": {
                        "$switch": {
                            "branches": [
                                {"case": {"$eq": ["$severity", "critical"]}, "then": 0},
                                {"case": {"$eq": ["$severity", "high"]}, "then": 1},
                                {"case": {"$eq": ["$severity", "medium"]}, "then": 2},
                                {"case": {"$eq": ["$severity", "low"]}, "then": 3},
                            ],
                            "default": 99,
                        }
                    }
                }
            },
            {"$sort": {"severity_order": 1, "reported_at": -1}},
            {"$skip": skip},
            {"$limit": limit},
            {"$project": {"severity_order": 0}},  # Remove temporary field
        ]

        incidents = []
        async for incident_doc in self.collection.aggregate(pipeline):
            if populate_asset:
                incident_doc = await self._populate_asset(incident_doc)
            incident_doc = await self._populate_comment_users(incident_doc)
            incident_doc = convert_objectid_to_str(incident_doc)
            incidents.append(Incident(**incident_doc))

        return incidents

    async def add_comment(self, incident_id: str, comment: dict) -> bool:
        """Add comment to incident."""
        if not ObjectId.is_valid(incident_id):
            return False
        result = await self.collection.update_one(
            {"_id": ObjectId(incident_id)},
            {"$push": {"comments": comment}, "$set": {"updated_at": datetime.utcnow()}},
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
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )
        else:
            # Add upvote
            result = await self.collection.update_one(
                {"_id": ObjectId(incident_id)},
                {
                    "$addToSet": {"upvoted_by": user_id},
                    "$inc": {"upvotes": 1},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )
        return result.modified_count > 0

    async def find_potential_duplicates(
        self,
        asset_id: Optional[str] = None,
        location: Optional[dict] = None,
        location_radius_meters: float = 50.0,
        time_window_hours: int = 168,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        exclude_incident_ids: Optional[List[str]] = None,
        limit: int = 50,
        include_resolved: bool = True,
        resolved_time_window_hours: int = 720,  # 30 days for resolved incidents
    ) -> List[Incident]:
        """Find potential duplicate incidents based on filters.

        Args:
            include_resolved: If True, also search resolved incidents (for recurrence detection)
            resolved_time_window_hours: Time window for resolved incidents (longer than active ones)
        """
        query = {}

        # Filter by asset_id if provided
        if asset_id:
            query["asset_id"] = asset_id

        # Filter by category if provided
        if category:
            query["category"] = category

        # Filter by severity if provided
        if severity:
            query["severity"] = severity

        # Handle status filtering - include resolved if requested
        if include_resolved:
            # Include all statuses except closed (closed means permanently resolved)
            # But exclude incidents resolved as duplicates
            # Use $or to handle different time windows for active vs resolved incidents
            time_threshold_active = (
                datetime.utcnow() - timedelta(hours=time_window_hours)
                if time_window_hours > 0
                else None
            )
            time_threshold_resolved = datetime.utcnow() - timedelta(
                hours=resolved_time_window_hours
            )

            or_conditions = []

            # Active incidents (not resolved/closed) within time window
            if time_threshold_active:
                or_conditions.append(
                    {
                        "status": {"$nin": ["resolved", "closed"]},
                        "reported_at": {"$gte": time_threshold_active},
                    }
                )
            else:
                or_conditions.append({"status": {"$nin": ["resolved", "closed"]}})

            # Resolved incidents (not duplicates) within longer time window
            resolved_condition = {
                "status": "resolved",
                "resolution_type": {"$ne": "duplicate"},
                "reported_at": {"$gte": time_threshold_resolved},
            }
            or_conditions.append(resolved_condition)

            query["$or"] = or_conditions
        else:
            # Original behavior: exclude resolved/closed incidents
            query["status"] = {"$nin": ["resolved", "closed"]}
            # Filter by time window for active incidents
            if time_window_hours > 0:
                time_threshold = datetime.utcnow() - timedelta(hours=time_window_hours)
                query["reported_at"] = {"$gte": time_threshold}

        # Exclude specific incident IDs
        if exclude_incident_ids:
            exclude_object_ids = [
                ObjectId(inc_id)
                for inc_id in exclude_incident_ids
                if ObjectId.is_valid(inc_id)
            ]
            if exclude_object_ids:
                query["_id"] = {"$nin": exclude_object_ids}

        # Build geospatial query if location provided
        # Note: MongoDB $near cannot be used with $or queries directly
        # We'll use aggregation pipeline with $geoNear if $or is present, otherwise use $near
        use_geospatial = location and "geometry" in location
        geometry_coords = None

        if use_geospatial:
            geometry = location["geometry"]
            if geometry.get("type") == "Point" and "coordinates" in geometry:
                geometry_coords = geometry["coordinates"]
                # If we have $or query, we need to use aggregation pipeline
                if "$or" in query:
                    # Use aggregation pipeline with $geoNear for $or queries
                    pipeline = [
                        {
                            "$geoNear": {
                                "near": {
                                    "type": "Point",
                                    "coordinates": geometry_coords,
                                },
                                "distanceField": "distance",
                                "maxDistance": location_radius_meters,
                                "spherical": True,
                            }
                        },
                        {"$match": query},
                        {"$sort": {"reported_at": -1}},
                        {"$limit": limit},
                    ]
                    incidents = []
                    async for incident_doc in self.collection.aggregate(pipeline):
                        incident_doc = convert_objectid_to_str(incident_doc)
                        try:
                            incidents.append(Incident(**incident_doc))
                        except Exception as e:
                            logger.warning(f"Error parsing incident document: {e}")
                            continue
                    return incidents
                else:
                    # Use simple $near query when no $or
                    query["location.geometry"] = {
                        "$near": {
                            "$geometry": {
                                "type": "Point",
                                "coordinates": geometry_coords,
                            },
                            "$maxDistance": location_radius_meters,
                        }
                    }

        # Execute query
        cursor = self.collection.find(query).sort("reported_at", -1).limit(limit)
        incidents = []
        async for incident_doc in cursor:
            incident_doc = convert_objectid_to_str(incident_doc)
            try:
                incidents.append(Incident(**incident_doc))
            except Exception as e:
                logger.warning(f"Error parsing incident document: {e}")
                continue
        return incidents
