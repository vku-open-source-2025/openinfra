#!/usr/bin/env python3
"""Restore script for OpenInfra DataCollector.

This script restores the MongoDB database from a backup directory containing JSON files.
It connects to the MongoDB instance defined by the `MONGO_URL` environment variable.

Usage:
    python restore_db.py <backup_directory>

WARNING: This script will DROP existing collections before restoring data.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    user = os.getenv("MONGO_USERNAME")
    password = os.getenv("MONGO_PASSWORD")
    if user and password:
        MONGO_URL = f"mongodb://{user}:{password}@localhost:27017/openinfra_gis"
    else:
        MONGO_URL = "mongodb://localhost:27017/openinfra_gis"

async def restore_collection(db, collection_name: str, input_path: Path):
    """Restore a collection from a JSON file.

    Args:
        db: Motor database object.
        collection_name: Name of the collection to restore.
        input_path: Path to the JSON file to read.
    """
    print(f"Restoring collection '{collection_name}' from {input_path}...")
    
    # Drop existing collection
    await db.drop_collection(collection_name)
    
    with open(input_path, "r", encoding="utf-8") as f:
        docs = json.load(f)
    
    if not docs:
        print(f"  No documents found in {input_path}. Skipping insert.")
        return

    # Process documents
    processed_docs = []
    for doc in docs:
        # Convert _id back to ObjectId
        if "_id" in doc and isinstance(doc["_id"], str):
            try:
                doc["_id"] = ObjectId(doc["_id"])
            except Exception:
                # Keep as string if not a valid ObjectId
                pass
        processed_docs.append(doc)
    
    # Insert documents
    if processed_docs:
        result = await db[collection_name].insert_many(processed_docs)
        print(f"  Inserted {len(result.inserted_ids)} documents.")

async def main():
    if len(sys.argv) != 2:
        print("Usage: python restore_db.py <backup_directory>")
        sys.exit(1)

    backup_dir = Path(sys.argv[1])
    if not backup_dir.exists() or not backup_dir.is_dir():
        print(f"Error: Backup directory '{backup_dir}' does not exist.")
        sys.exit(1)

    client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=2000)
    try:
        # Check connection
        await client.server_info()
        db = client.get_default_database()
    except Exception:
        # Fallback if get_default_database fails or connection issue (though server_info should catch it)
        db = client.openinfra_gis
        print(f"Connected to database: {db.name}")

    # Iterate over JSON files in the backup directory
    json_files = list(backup_dir.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {backup_dir}")
        return

    print(f"Found {len(json_files)} backup files.")
    
    for json_file in json_files:
        collection_name = json_file.stem  # filename without extension
        await restore_collection(db, collection_name, json_file)

    print("Restore completed successfully.")

if __name__ == "__main__":
    asyncio.run(main())
