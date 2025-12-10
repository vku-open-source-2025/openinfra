#!/usr/bin/env python3
"""
SOSA Metadata Migration Script for Backend.

Creates SOSA-compliant metadata for existing IoT sensors.
Run this after seeding IoT data.

Usage:
    # From backend container
    python -m scripts.migrate_sosa_metadata
    
    # Dry run (no changes)
    python -m scripts.migrate_sosa_metadata --dry-run
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app.domain.models.sosa_metadata import (
    sensor_type_to_observable_property,
    unit_to_qudt_uri,
    unit_to_label,
    ObservableProperty,
)


# Vietnamese labels for sensor types
SENSOR_TYPE_LABELS = {
    "temperature": "Nhiệt độ",
    "humidity": "Độ ẩm",
    "pressure": "Áp suất",
    "water_level": "Mực nước",
    "flow_rate": "Lưu lượng",
    "air_quality": "Chất lượng không khí",
    "vibration": "Độ rung",
    "power": "Công suất",
    "voltage": "Điện áp",
    "current": "Dòng điện",
    "custom": "Tùy chỉnh",
}


async def get_asset_info(db, asset_id: str) -> dict:
    """Get asset information for FeatureOfInterest."""
    from bson import ObjectId
    
    try:
        if ObjectId.is_valid(asset_id):
            asset = await db.assets.find_one({"_id": ObjectId(asset_id)})
        else:
            asset = await db.assets.find_one({"_id": asset_id})
        
        if asset:
            return {
                "id": str(asset["_id"]),
                "name": asset.get("ten", asset.get("name", f"Asset {asset_id}")),
                "description": asset.get("mo_ta", asset.get("description", "")),
                "feature_type": asset.get("feature_type", ""),
                "feature_code": asset.get("feature_code", ""),
                "location": asset.get("geometry", None),
            }
    except Exception as e:
        print(f"Warning: Could not get asset info for {asset_id}: {e}")
    
    return {
        "id": asset_id,
        "name": f"Asset {asset_id}",
        "description": "",
        "feature_type": "unknown",
        "feature_code": "unknown",
        "location": None,
    }


def create_sosa_metadata(sensor: dict, asset_info: dict) -> dict:
    """Create SOSA metadata document from sensor and asset info."""
    sensor_id = str(sensor["_id"])
    sensor_type = sensor.get("sensor_type", "custom")
    unit = sensor.get("measurement_unit", "")
    
    # Get observable property URI
    observable_property = sensor_type_to_observable_property(sensor_type)
    
    # Create human-readable label
    type_label = SENSOR_TYPE_LABELS.get(sensor_type, sensor_type)
    location_desc = sensor.get("location_description", "")
    label = f"Cảm biến {type_label}"
    if location_desc:
        label += f" - {location_desc}"
    elif asset_info.get("name"):
        label += f" - {asset_info['name']}"
    
    # Build SOSA metadata document
    metadata = {
        "_id": sensor_id,
        "type": "sosa:Sensor",
        "label": label,
        "description": sensor.get("notes", f"Cảm biến đo {type_label.lower()}"),
        
        # SOSA Core Properties
        "observes": observable_property.value if hasattr(observable_property, 'value') else str(observable_property),
        "has_feature_of_interest": {
            "id": asset_info["id"],
            "type": "sosa:FeatureOfInterest",
            "name": asset_info["name"],
            "description": asset_info.get("description", ""),
            "location": asset_info.get("location"),
            "properties": {
                "feature_type": asset_info.get("feature_type", ""),
                "feature_code": asset_info.get("feature_code", ""),
            }
        },
        
        # Observation configuration
        "observation_config": {
            "unit": {
                "symbol": unit,
                "qudt_uri": unit_to_qudt_uri(unit),
                "label": unit_to_label(unit),
            },
            "result_type": "xsd:float",
            "sampling_interval": sensor.get("sample_rate"),
            "accuracy": None,
            "precision": None,
        },
        
        # Optional SSN extensions
        "implements_procedure": None,
        "has_deployment": None,
        "is_hosted_by": sensor.get("gateway_id"),
        
        # Links
        "same_as": [],
        "see_also": [],
        
        # Tracking
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": "migration_script",
        
        # Custom properties from original sensor
        "custom_properties": {
            "sensor_code": sensor.get("sensor_code"),
            "manufacturer": sensor.get("manufacturer"),
            "model": sensor.get("model"),
            "firmware_version": sensor.get("firmware_version"),
            "connection_type": sensor.get("connection_type"),
            "thresholds": sensor.get("thresholds"),
            "tags": sensor.get("tags", []),
        }
    }
    
    return metadata


async def migrate_sensors_to_sosa(dry_run: bool = False):
    """Migrate all sensors to SOSA metadata."""
    print("\n" + "=" * 60)
    print("SOSA Metadata Migration")
    print("=" * 60)
    
    # Connect to MongoDB directly
    from motor.motor_asyncio import AsyncIOMotorClient
    import os
    
    mongo_url = os.getenv("MONGODB_URL", "mongodb://mongo:27017")
    db_name = os.getenv("DATABASE_NAME", "gis_db")
    
    print(f"Connecting to MongoDB: {mongo_url}")
    print(f"Database: {db_name}")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Get all sensors
    sensors = await db.iot_sensors.find({}).to_list(length=10000)
    print(f"\nFound {len(sensors)} sensors to migrate")
    
    if not sensors:
        print("No sensors found. Please seed IoT data first.")
        return
    
    # Check existing metadata
    existing_count = await db.sensors_metadata.count_documents({})
    print(f"Existing metadata entries: {existing_count}")
    
    # Prepare metadata documents
    metadata_docs = []
    skipped = 0
    
    for sensor in sensors:
        sensor_id = str(sensor["_id"])
        
        # Check if metadata already exists
        existing = await db.sensors_metadata.find_one({"_id": sensor_id})
        if existing:
            skipped += 1
            continue
        
        # Get asset info
        asset_info = await get_asset_info(db, sensor.get("asset_id", ""))
        
        # Create SOSA metadata
        metadata = create_sosa_metadata(sensor, asset_info)
        metadata_docs.append(metadata)
        
        if not dry_run and len(metadata_docs) % 50 == 0:
            print(f"  Processed {len(metadata_docs) + skipped} sensors...")
    
    print(f"\nSkipped (already migrated): {skipped}")
    print(f"New metadata to create: {len(metadata_docs)}")
    
    if dry_run:
        print("\n[DRY RUN] No changes made.")
        if metadata_docs:
            print("\nSample metadata document:")
            import json
            sample = metadata_docs[0].copy()
            sample["_id"] = str(sample["_id"])
            sample["created_at"] = sample["created_at"].isoformat()
            sample["updated_at"] = sample["updated_at"].isoformat()
            print(json.dumps(sample, indent=2, ensure_ascii=False))
        return
    
    if not metadata_docs:
        print("\nNo new metadata to create.")
        return
    
    # Insert metadata documents
    print("\nInserting metadata documents...")
    try:
        result = await db.sensors_metadata.insert_many(metadata_docs, ordered=False)
        print(f"Successfully created {len(result.inserted_ids)} metadata entries")
    except Exception as e:
        if "duplicate key" in str(e).lower():
            print(f"Some entries were duplicates (already existed)")
        else:
            raise
    
    # Create indexes
    print("\nCreating indexes...")
    await db.sensors_metadata.create_index("observes")
    await db.sensors_metadata.create_index("has_feature_of_interest.id")
    await db.sensors_metadata.create_index("is_hosted_by")
    await db.sensors_metadata.create_index("type")
    print("Indexes created!")
    
    # Final count
    final_count = await db.sensors_metadata.count_documents({})
    print(f"\nTotal metadata entries: {final_count}")


async def main():
    """Main entry point."""
    dry_run = "--dry-run" in sys.argv
    
    print("=" * 60)
    print("OpenInfra SOSA Metadata Migration")
    print("=" * 60)
    
    await migrate_sensors_to_sosa(dry_run=dry_run)
    
    print("\n" + "=" * 60)
    print("Migration completed!")
    print("=" * 60)
    print("\nHybrid Store Architecture:")
    print("┌─────────────────────────────────────────────────────┐")
    print("│  Raw Data (High Performance)                        │")
    print("│  - iot_sensors: Device registry                     │")
    print("│  - sensor_readings: Time-series measurements        │")
    print("├─────────────────────────────────────────────────────┤")
    print("│  Semantic Layer (SOSA Compliance)                   │")
    print("│  - sensors_metadata: SOSA vocabulary                │")
    print("│  - API: JSON-LD with @context                       │")
    print("└─────────────────────────────────────────────────────┘")
    print("\nAPI endpoints with SOSA:")
    print("- GET /api/v1/ld/sosa/context - SOSA JSON-LD context")
    print("- GET /api/v1/ld/sosa/observable-properties - Observable properties")
    print("- GET /api/v1/ld/sensors - Sensors with SOSA semantics")
    print("- GET /api/v1/ld/sensors/{id}/observations - SOSA observations")


if __name__ == "__main__":
    asyncio.run(main())
