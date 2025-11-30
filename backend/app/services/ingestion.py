
import pandas as pd
import json
from app.infrastructure.database.mongodb import get_database
from app.models.asset import AssetCreate
from datetime import datetime
import io

async def ingest_csv_data(file_content: bytes):
    df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8-sig')

    db = await get_database()
    collection = db["assets"]

    # Create 2dsphere index for geospatial queries
    await collection.create_index([("geometry", "2dsphere")])

    assets_to_insert = []

    for _, row in df.iterrows():
        try:
            # Custom geometry parsing: "TYPE [coordinates]"
            geo_str = row['geometry']
            if not geo_str:
                continue

            # Split into Type and Coordinates
            # Example: "POINT [108.2, 15.9]" -> type_str="POINT", coords_str="[108.2, 15.9]"
            parts = geo_str.split(' ', 1)
            if len(parts) != 2:
                print(f"Invalid geometry format: {geo_str}")
                continue

            type_str = parts[0].upper()
            coords_str = parts[1]

            # Map WKT-like types to GeoJSON types
            type_map = {
                "POINT": "Point",
                "LINESTRING": "LineString",
                "POLYGON": "Polygon",
                "MULTIPOINT": "MultiPoint",
                "MULTILINESTRING": "MultiLineString",
                "MULTIPOLYGON": "MultiPolygon"
            }

            if type_str not in type_map:
                print(f"Unknown geometry type: {type_str}")
                continue

            coordinates = json.loads(coords_str)

            geojson_geometry = {
                "type": type_map[type_str],
                "coordinates": coordinates
            }

            # Parse datetime
            created_at = pd.to_datetime(row['created_at'])

            asset = {
                "feature_type": row['feature_type'],
                "feature_code": row['feature_code'],
                "geometry": geojson_geometry,
                "created_at": created_at
            }
            assets_to_insert.append(asset)
        except Exception as e:
            print(f"Error processing row: {row}. Error: {e}")
            continue

    if assets_to_insert:
        # Clear existing data? Or append?
        # For this task, let's clear to avoid duplicates if re-running seed
        # await collection.delete_many({})
        # Actually, let's just insert. The user might want to add more data.

        result = await collection.insert_many(assets_to_insert)
        return len(result.inserted_ids)

    return 0
