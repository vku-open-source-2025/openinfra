"""
CSV Service Module
Handles CSV download, parsing, and database operations for infrastructure data import.
Uses synchronous pymongo for Celery compatibility.
"""

import requests
import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Any
import io
import pymongo
import os


def download_csv(url: str) -> str:
    """
    Download CSV from URL
    
    Args:
        url: CSV download URL
        
    Returns:
        CSV content as string
    """
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.text


def parse_geometry(geo_str: str) -> Dict[str, Any] | None:
    """
    Parse geometry string to GeoJSON format
    Supports: POINT [lon, lat]
    
    Args:
        geo_str: Geometry string from CSV
        
    Returns:
        GeoJSON object or None if invalid
    """
    if pd.isna(geo_str) or not geo_str:
        return None
    
    try:
        # Handle format: "POINT [108.2, 15.9]"
        parts = geo_str.split(' ', 1)
        if len(parts) != 2:
            return None
            
        type_str = parts[0].upper()
        coords_str = parts[1]
        
        type_map = {
            "POINT": "Point",
            "LINESTRING": "LineString",
            "POLYGON": "Polygon",
            "MULTIPOINT": "MultiPoint",
            "MULTILINESTRING": "MultiLineString",
            "MULTIPOLYGON": "MultiPolygon"
        }
        
        if type_str not in type_map:
            return None
            
        coordinates = json.loads(coords_str)
        
        return {
            "type": type_map[type_str],
            "coordinates": coordinates
        }
    except Exception as e:
        print(f"Error parsing geometry: {geo_str}, Error: {e}")
        return None


def parse_csv_to_assets(csv_content: str) -> List[Dict[str, Any]]:
    """
    Parse CSV content to list of asset documents
    
    Args:
        csv_content: CSV content as string
        
    Returns:
        List of asset documents ready for insertion
    """
    df = pd.read_csv(io.StringIO(csv_content))
    
    assets = []
    for _, row in df.iterrows():
        geometry = parse_geometry(row.get('geometry'))
        if not geometry:
            continue
            
        asset = {
            "feature_type": str(row.get('feature_type', 'Unknown')),
            "feature_code": str(row.get('feature_code', 'UNKNOWN')),
            "geometry": geometry,
            "created_at": datetime.utcnow()
        }
        assets.append(asset)
    
    return assets


def get_sync_db():
    """
    Get synchronous MongoDB connection for Celery tasks
    
    Returns:
        MongoDB database instance
    """
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://mongo:27017")
    database_name = os.getenv("DATABASE_NAME", "openinfra")
    
    client = pymongo.MongoClient(mongodb_url)
    return client[database_name]


def check_duplicate_coordinates(collection, coordinates: List[float]) -> bool:
    """
    Check if asset with same coordinates already exists
    
    Args:
        collection: MongoDB collection
        coordinates: [longitude, latitude]
        
    Returns:
        True if duplicate exists, False otherwise
    """
    existing = collection.find_one({
        "geometry.type": "Point",
        "geometry.coordinates": coordinates
    })
    return existing is not None


def insert_assets_skip_duplicates(db, assets: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Insert assets into database, skipping duplicates based on coordinates
    
    Args:
        db: Database connection (not used, get fresh connection)
        assets: List of asset documents
        
    Returns:
        Dictionary with statistics (total, inserted, skipped, errors)
    """
    # Get synchronous database connection
    sync_db = get_sync_db()
    collection = sync_db.assets
    
    total = len(assets)
    inserted = 0
    skipped = 0
    errors = 0
    
    for asset in assets:
        try:
            # Check if Point type
            if asset["geometry"]["type"] != "Point":
                # For non-Point geometries, insert without duplicate check
                collection.insert_one(asset)
                inserted += 1
                continue
            
            # Check for duplicate coordinates
            coordinates = asset["geometry"]["coordinates"]
            if check_duplicate_coordinates(collection, coordinates):
                skipped += 1
                continue
            
            # Insert new asset
            collection.insert_one(asset)
            inserted += 1
            
        except Exception as e:
            print(f"Error inserting asset: {e}")
            errors += 1
    
    return {
        "total": total,
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors
    }
