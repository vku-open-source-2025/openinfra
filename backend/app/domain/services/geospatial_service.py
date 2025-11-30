"""Geospatial service for location-based queries."""
from typing import List, Optional
from app.domain.models.asset import Asset
from app.domain.value_objects.coordinates import Coordinates
from app.domain.repositories.asset_repository import AssetRepository
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.infrastructure.database.mongodb import get_database
import logging

logger = logging.getLogger(__name__)


class GeospatialService:
    """Service for geospatial queries."""

    def __init__(self, asset_repository: AssetRepository):
        self.asset_repository = asset_repository

    async def find_nearby_assets(
        self,
        coordinates: Coordinates,
        radius_meters: int = 1000,
        feature_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Asset]:
        """Find assets within radius of coordinates."""
        db = await get_database()
        collection = db["assets"]

        query = {
            "geometry": {
                "$near": {
                    "$geometry": coordinates.to_geojson(),
                    "$maxDistance": radius_meters
                }
            }
        }

        if feature_type:
            query["feature_type"] = feature_type

        cursor = collection.find(query).limit(limit)
        assets = []
        async for asset_doc in cursor:
            from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str
            asset_doc = convert_objectid_to_str(asset_doc)
            # Handle legacy data
            if "asset_code" not in asset_doc or not asset_doc.get("asset_code"):
                feature_code = asset_doc.get("feature_code", "ASSET")
                from datetime import datetime
                asset_doc["asset_code"] = f"{feature_code}-{int(datetime.utcnow().timestamp())}"
            if "name" not in asset_doc or not asset_doc.get("name"):
                feature_type_val = asset_doc.get("feature_type", "Asset")
                asset_doc["name"] = f"{feature_type_val} (Legacy)"
            assets.append(Asset(**asset_doc))

        return assets

    async def find_assets_in_bounds(
        self,
        min_lng: float,
        min_lat: float,
        max_lng: float,
        max_lat: float,
        feature_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[Asset]:
        """Find assets within bounding box."""
        db = await get_database()
        collection = db["assets"]

        query = {
            "geometry": {
                "$geoWithin": {
                    "$box": [
                        [min_lng, min_lat],
                        [max_lng, max_lat]
                    ]
                }
            }
        }

        if feature_type:
            query["feature_type"] = feature_type

        cursor = collection.find(query).limit(limit)
        assets = []
        async for asset_doc in cursor:
            from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str
            asset_doc = convert_objectid_to_str(asset_doc)
            # Handle legacy data
            if "asset_code" not in asset_doc or not asset_doc.get("asset_code"):
                feature_code = asset_doc.get("feature_code", "ASSET")
                from datetime import datetime
                asset_doc["asset_code"] = f"{feature_code}-{int(datetime.utcnow().timestamp())}"
            if "name" not in asset_doc or not asset_doc.get("name"):
                feature_type_val = asset_doc.get("feature_type", "Asset")
                asset_doc["name"] = f"{feature_type_val} (Legacy)"
            assets.append(Asset(**asset_doc))

        return assets

    async def find_assets_in_polygon(
        self,
        polygon_coordinates: List[List[float]],
        feature_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[Asset]:
        """Find assets within polygon."""
        db = await get_database()
        collection = db["assets"]

        # Ensure polygon is closed (first point == last point)
        if polygon_coordinates[0] != polygon_coordinates[-1]:
            polygon_coordinates.append(polygon_coordinates[0])

        query = {
            "geometry": {
                "$geoWithin": {
                    "$geometry": {
                        "type": "Polygon",
                        "coordinates": [polygon_coordinates]
                    }
                }
            }
        }

        if feature_type:
            query["feature_type"] = feature_type

        cursor = collection.find(query).limit(limit)
        assets = []
        async for asset_doc in cursor:
            from app.infrastructure.database.repositories.base_repository import convert_objectid_to_str
            asset_doc = convert_objectid_to_str(asset_doc)
            # Handle legacy data
            if "asset_code" not in asset_doc or not asset_doc.get("asset_code"):
                feature_code = asset_doc.get("feature_code", "ASSET")
                from datetime import datetime
                asset_doc["asset_code"] = f"{feature_code}-{int(datetime.utcnow().timestamp())}"
            if "name" not in asset_doc or not asset_doc.get("name"):
                feature_type_val = asset_doc.get("feature_type", "Asset")
                asset_doc["name"] = f"{feature_type_val} (Legacy)"
            assets.append(Asset(**asset_doc))

        return assets

    async def calculate_distance(
        self,
        coords1: Coordinates,
        coords2: Coordinates
    ) -> float:
        """Calculate distance between two coordinates in meters (Haversine formula)."""
        from math import radians, cos, sin, asin, sqrt

        # Convert to radians
        lat1, lon1 = radians(coords1.latitude), radians(coords1.longitude)
        lat2, lon2 = radians(coords2.latitude), radians(coords2.longitude)

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        # Earth radius in meters
        R = 6371000
        distance = R * c

        return distance
