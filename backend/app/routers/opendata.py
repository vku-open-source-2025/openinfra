"""
Open Data API - JSON-LD Format (Readonly)
License: OGL (Open Government Licence)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Any, Dict
from app.infrastructure.database.mongodb import get_database
from bson import ObjectId
from datetime import datetime

router = APIRouter()

# JSON-LD Context for GeoJSON infrastructure data
JSONLD_CONTEXT = {
    "@context": {
        "@vocab": "https://schema.org/",
        "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
        "geojson": "https://purl.org/geojson/vocab#",
        "dcterms": "http://purl.org/dc/terms/",
        "ogl": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        "id": "@id",
        "type": "@type",
        "Feature": "geojson:Feature",
        "FeatureCollection": "geojson:FeatureCollection",
        "Point": "geojson:Point",
        "LineString": "geojson:LineString",
        "Polygon": "geojson:Polygon",
        "MultiPoint": "geojson:MultiPoint",
        "MultiLineString": "geojson:MultiLineString",
        "MultiPolygon": "geojson:MultiPolygon",
        "coordinates": "geojson:coordinates",
        "geometry": "geojson:geometry",
        "properties": "geojson:properties",
        "features": "geojson:features",
        "feature_type": "dcterms:type",
        "feature_code": "dcterms:identifier",
        "created_at": "dcterms:created",
        "license": "dcterms:license",
        "publisher": "dcterms:publisher",
    }
}

LICENSE_INFO = {
    "license": "OGL",
    "license_url": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
    "license_name": "Open Government Licence",
    "publisher": "VKU.OneLove - OpenInfra",
    "attribution": "Data provided by OpenInfra (https://openinfra.space). Licensed under OGL.",
}


def asset_to_jsonld_feature(asset: dict, base_url: str) -> Dict[str, Any]:
    """Convert MongoDB asset document to JSON-LD GeoJSON Feature"""
    asset_id = str(asset["_id"])
    created_at = asset.get("created_at")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()

    return {
        "@type": "Feature",
        "@id": f"{base_url}/api/opendata/assets/{asset_id}",
        "geometry": {
            "@type": asset["geometry"]["type"],
            "coordinates": asset["geometry"]["coordinates"],
        },
        "properties": {
            "feature_type": asset.get("feature_type", ""),
            "feature_code": asset.get("feature_code", ""),
            "created_at": created_at,
            **LICENSE_INFO,
        },
    }


@router.get(
    "/",
    summary="API Information",
    description="Get information about the Open Data API and license terms",
)
async def api_info():
    """Return API information and license details"""
    return {
        **JSONLD_CONTEXT,
        "@type": "DataCatalog",
        "name": "OpenInfra Open Data API",
        "description": "Open infrastructure GIS data in JSON-LD format",
        "version": "1.0.0",
        **LICENSE_INFO,
        "endpoints": {
            "assets": "/api/opendata/assets",
            "asset_detail": "/api/opendata/assets/{id}",
            "feature_types": "/api/opendata/feature-types",
        },
        "formats": ["JSON-LD", "GeoJSON"],
        "documentation": "https://openinfra.space/docs",
    }


@router.get(
    "/assets",
    summary="List all assets (JSON-LD)",
    description="Get all infrastructure assets as a GeoJSON FeatureCollection in JSON-LD format. Licensed under OGL.",
)
async def list_assets_jsonld(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    feature_type: Optional[str] = Query(None, description="Filter by feature type"),
    feature_code: Optional[str] = Query(None, description="Filter by feature code"),
):
    """
    Returns infrastructure assets as JSON-LD GeoJSON FeatureCollection.

    **License:** OGL (Open Government Licence)

    **Attribution Required:** When using this data, please attribute:
    "Data provided by OpenInfra (https://openinfra.space)"
    """
    db = await get_database()
    query = {}

    if feature_type:
        query["feature_type"] = feature_type
    if feature_code:
        query["feature_code"] = feature_code

    cursor = db["assets"].find(query).skip(skip).limit(limit)
    total_count = await db["assets"].count_documents(query)

    features = []
    base_url = "https://api.openinfra.space"

    async for asset in cursor:
        features.append(asset_to_jsonld_feature(asset, base_url))

    return {
        **JSONLD_CONTEXT,
        "@type": "FeatureCollection",
        "features": features,
        "totalCount": total_count,
        "returned": len(features),
        **LICENSE_INFO,
    }


@router.get(
    "/assets/{asset_id}",
    summary="Get single asset (JSON-LD)",
    description="Get a specific infrastructure asset by ID in JSON-LD format",
)
async def get_asset_jsonld(asset_id: str):
    """
    Returns a single infrastructure asset as JSON-LD GeoJSON Feature.

    **License:** OGL (Open Government Licence)
    """
    db = await get_database()

    if not ObjectId.is_valid(asset_id):
        raise HTTPException(status_code=400, detail="Invalid asset ID format")

    asset = await db["assets"].find_one({"_id": ObjectId(asset_id)})

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    base_url = "https://api.openinfra.space"
    feature = asset_to_jsonld_feature(asset, base_url)

    return {**JSONLD_CONTEXT, **feature}


@router.get(
    "/feature-types",
    summary="List available feature types",
    description="Get all unique feature types and codes available in the dataset",
)
async def list_feature_types():
    """
    Returns available feature types and their counts.

    **License:** OGL (Open Government Licence)
    """
    db = await get_database()

    pipeline = [
        {
            "$group": {
                "_id": {
                    "feature_type": "$feature_type",
                    "feature_code": "$feature_code",
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
    ]

    cursor = db["assets"].aggregate(pipeline)

    feature_types = []
    async for doc in cursor:
        feature_types.append(
            {
                "feature_type": doc["_id"]["feature_type"],
                "feature_code": doc["_id"]["feature_code"],
                "count": doc["count"],
            }
        )

    return {
        **JSONLD_CONTEXT,
        "@type": "ItemList",
        "name": "Available Feature Types",
        "itemListElement": feature_types,
        "totalItems": len(feature_types),
        **LICENSE_INFO,
    }


@router.get(
    "/license",
    summary="License information",
    description="Get detailed license information for the open data",
)
async def license_info():
    """Return detailed OGL license information"""
    return {
        **JSONLD_CONTEXT,
        "@type": "CreativeWork",
        "name": "OGL License",
        **LICENSE_INFO,
        "terms": [
            "You are free to share, copy, and redistribute the data",
            "You are free to create and distribute adapted data",
            "You must attribute the source when using this data",
            "You must keep this license notice with the data",
        ],
        "attribution_example": "Data source: OpenInfra (https://openinfra.space) - Licensed under OGL",
    }
