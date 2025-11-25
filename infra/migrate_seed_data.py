"""
MongoDB Migration Script for Infrastructure Management System
This script seeds the database with sample assets and maintenance logs.

Usage:
    python migrate_seed_data.py

Requirements:
    pip install pymongo pandas
"""

import pymongo
import pandas as pd
import json
import random
from datetime import datetime, timedelta
from bson import ObjectId

# Configuration
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "infrastructure_db"
CSV_FILE_PATH = "../sample_data.csv"

# Connect to MongoDB
client = pymongo.MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]

def clear_collections():
    """Clear existing data from collections"""
    print("Clearing existing data...")
    db.assets.delete_many({})
    db.maintenance_logs.delete_many({})
    print("✓ Collections cleared")

def parse_geometry(geo_str):
    """Parse geometry string to GeoJSON format"""
    if pd.isna(geo_str):
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

def seed_assets():
    """Seed assets from CSV file"""
    print(f"\nSeeding assets from {CSV_FILE_PATH}...")
    
    try:
        df = pd.read_csv(CSV_FILE_PATH)
        print(f"Found {len(df)} rows in CSV")
        
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
        
        if assets:
            result = db.assets.insert_many(assets)
            print(f"✓ Inserted {len(result.inserted_ids)} assets")
            return list(db.assets.find())
        else:
            print("⚠ No valid assets to insert")
            return []
            
    except Exception as e:
        print(f"✗ Error seeding assets: {e}")
        return []

def seed_maintenance_logs(assets):
    """Generate and seed maintenance logs"""
    print("\nSeeding maintenance logs...")
    
    if not assets:
        print("⚠ No assets found, skipping maintenance logs")
        return
    
    statuses = ["Pending", "In Progress", "Completed", "Scheduled"]
    technicians = [
        "Nguyen Van A", 
        "Tran Thi B", 
        "Le Van C", 
        "Pham Thi D", 
        "Hoang Van E",
        "Vo Van F",
        "Dang Thi G"
    ]
    descriptions = [
        "Routine inspection",
        "Replace broken component",
        "Safety check",
        "Firmware update",
        "Cleaning and maintenance",
        "Emergency repair",
        "Voltage check",
        "Structural integrity assessment",
        "Preventive maintenance",
        "Performance optimization",
        "Cable replacement",
        "Sensor calibration",
        "Power supply check",
        "Network connectivity test"
    ]
    
    logs = []
    
    # Generate logs for 40% of assets
    target_assets = random.sample(assets, int(len(assets) * 0.4))
    
    for asset in target_assets:
        # Generate 1-3 logs per asset
        num_logs = random.randint(1, 3)
        
        for _ in range(num_logs):
            status = random.choice(statuses)
            scheduled_date = datetime.utcnow() - timedelta(days=random.randint(0, 365))
            
            log = {
                "asset_id": str(asset["_id"]),
                "description": random.choice(descriptions),
                "technician": random.choice(technicians),
                "status": status,
                "scheduled_date": scheduled_date,
                "completed_date": scheduled_date + timedelta(hours=random.randint(1, 48)) if status == "Completed" else None,
                "created_at": datetime.utcnow()
            }
            logs.append(log)
    
    if logs:
        result = db.maintenance_logs.insert_many(logs)
        print(f"✓ Inserted {len(result.inserted_ids)} maintenance logs")
    else:
        print("⚠ No maintenance logs to insert")

def create_indexes():
    """Create database indexes for better performance"""
    print("\nCreating indexes...")
    
    # Asset indexes
    db.assets.create_index([("geometry", pymongo.GEOSPHERE)])
    db.assets.create_index([("feature_code", pymongo.ASCENDING)])
    db.assets.create_index([("feature_type", pymongo.ASCENDING)])
    
    # Maintenance log indexes
    db.maintenance_logs.create_index([("asset_id", pymongo.ASCENDING)])
    db.maintenance_logs.create_index([("status", pymongo.ASCENDING)])
    db.maintenance_logs.create_index([("scheduled_date", pymongo.DESCENDING)])
    
    print("✓ Indexes created")

def print_summary():
    """Print database summary"""
    print("\n" + "="*50)
    print("DATABASE SUMMARY")
    print("="*50)
    
    asset_count = db.assets.count_documents({})
    log_count = db.maintenance_logs.count_documents({})
    
    print(f"Total Assets: {asset_count}")
    print(f"Total Maintenance Logs: {log_count}")
    
    # Count by status
    print("\nMaintenance Logs by Status:")
    for status in ["Pending", "In Progress", "Completed", "Scheduled"]:
        count = db.maintenance_logs.count_documents({"status": status})
        print(f"  {status}: {count}")
    
    # Count by feature type
    print("\nAssets by Feature Type:")
    pipeline = [
        {"$group": {"_id": "$feature_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    for doc in db.assets.aggregate(pipeline):
        print(f"  {doc['_id']}: {doc['count']}")
    
    print("="*50)

def main():
    """Main migration function"""
    print("="*50)
    print("INFRASTRUCTURE MANAGEMENT SYSTEM")
    print("Database Migration & Seeding")
    print("="*50)
    
    try:
        # Step 1: Clear existing data
        clear_collections()
        
        # Step 2: Seed assets
        assets = seed_assets()
        
        # Step 3: Seed maintenance logs
        seed_maintenance_logs(assets)
        
        # Step 4: Create indexes
        create_indexes()
        
        # Step 5: Print summary
        print_summary()
        
        print("\n✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    main()
