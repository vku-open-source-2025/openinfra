"""Geospatial API router."""
from fastapi import APIRouter, Query, Body, Depends
from typing import List, Optional
from app.domain.value_objects.coordinates import Coordinates
from app.domain.services.geospatial_service import GeospatialService
from app.infrastructure.external.osm_service import OSMService
from app.domain.models.asset import Asset
from app.api.v1.dependencies import get_geospatial_service, get_osm_service
from pydantic import BaseModel

router = APIRouter()


class GeocodeRequest(BaseModel):
    """Geocode request schema."""
    address: str
    country: str = "Vietnam"


class ReverseGeocodeRequest(BaseModel):
    """Reverse geocode request schema."""
    longitude: float
    latitude: float


class PolygonRequest(BaseModel):
    """Polygon search request schema."""
    coordinates: List[List[float]]  # List of [lng, lat] pairs
    feature_type: Optional[str] = None


@router.get("/assets/nearby", response_model=List[Asset])
async def find_nearby_assets(
    lng: float = Query(..., description="Longitude"),
    lat: float = Query(..., description="Latitude"),
    radius_meters: int = Query(1000, ge=1, le=50000, description="Search radius in meters"),
    feature_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    geo_service: GeospatialService = Depends(get_geospatial_service)
):
    """Find assets near coordinates."""
    coords = Coordinates(longitude=lng, latitude=lat)
    return await geo_service.find_nearby_assets(coords, radius_meters, feature_type, limit)


@router.get("/assets/within-bounds", response_model=List[Asset])
async def find_assets_in_bounds(
    min_lng: float = Query(..., description="Minimum longitude"),
    min_lat: float = Query(..., description="Minimum latitude"),
    max_lng: float = Query(..., description="Maximum longitude"),
    max_lat: float = Query(..., description="Maximum latitude"),
    feature_type: Optional[str] = None,
    limit: int = Query(1000, ge=1, le=10000),
    geo_service: GeospatialService = Depends(get_geospatial_service)
):
    """Find assets within bounding box."""
    return await geo_service.find_assets_in_bounds(
        min_lng, min_lat, max_lng, max_lat, feature_type, limit
    )


@router.post("/assets/within-polygon", response_model=List[Asset])
async def find_assets_in_polygon(
    request: PolygonRequest,
    limit: int = Query(1000, ge=1, le=10000),
    geo_service: GeospatialService = Depends(get_geospatial_service)
):
    """Find assets within polygon."""
    return await geo_service.find_assets_in_polygon(
        request.coordinates, request.feature_type, limit
    )


@router.post("/geocode")
async def geocode_address(
    request: GeocodeRequest,
    osm_service: OSMService = Depends(get_osm_service)
):
    """Convert address to coordinates."""
    coords = await osm_service.geocode(request.address, request.country)
    if coords:
        return {
            "coordinates": {
                "longitude": coords.longitude,
                "latitude": coords.latitude
            },
            "geojson": coords.to_geojson()
        }
    return {"error": "Address not found"}


@router.post("/reverse-geocode")
async def reverse_geocode(
    request: ReverseGeocodeRequest,
    osm_service: OSMService = Depends(get_osm_service)
):
    """Convert coordinates to address."""
    coords = Coordinates(longitude=request.longitude, latitude=request.latitude)
    address_info = await osm_service.reverse_geocode(coords)
    if address_info:
        return address_info
    return {"error": "Address not found"}


@router.get("/search-address")
async def search_address(
    q: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20),
    osm_service: OSMService = Depends(get_osm_service)
):
    """Search for addresses (autocomplete)."""
    return await osm_service.search_address(q, limit)


@router.get("/assets/{asset_id}/distance-to")
async def calculate_distance_to_asset(
    asset_id: str,
    lng: float = Query(..., description="Longitude"),
    lat: float = Query(..., description="Latitude"),
    geo_service: GeospatialService = Depends(get_geospatial_service)
):
    """Calculate distance from coordinates to asset."""
    from app.api.v1.dependencies import get_asset_service
    asset_service = await get_asset_service()
    asset = await asset_service.get_asset_by_id(asset_id)

    # Extract coordinates from asset geometry
    geometry = asset.geometry
    if geometry.get("type") != "Point":
        return {"error": "Asset geometry must be a Point"}

    coords = geometry.get("coordinates", [])
    if len(coords) < 2:
        return {"error": "Invalid coordinates"}

    asset_coords = Coordinates(longitude=coords[0], latitude=coords[1])
    point_coords = Coordinates(longitude=lng, latitude=lat)

    distance = await geo_service.calculate_distance(asset_coords, point_coords)

    return {
        "asset_id": asset_id,
        "distance_meters": round(distance, 2),
        "distance_km": round(distance / 1000, 2)
    }
