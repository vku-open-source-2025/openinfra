#!/usr/bin/env python3
"""Backup script for OpenInfra DataCollector.

This script connects to the MongoDB instance defined by the `MONGO_URL` environment
variable (fallback to the default used by the application) and dumps each
collection to a JSON file. The files are stored in a `backup` directory under the
project root with a timestamped sub‑directory.

Usage:
    python backup_db.py

The script is asynchronous using `motor` to stay consistent with the rest of the
codebase, but it runs synchronously via `asyncio.run`.
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables (same as the app)
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

async def dump_collection(collection, output_path: Path):
    """Dump all documents from a collection to a JSON file.

    Args:
        collection: Motor collection object.
        output_path: Path to the JSON file to write.
    """
    cursor = collection.find({})
    docs = []
    async for doc in cursor:
        # Convert ObjectId to string for JSON serialisation
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        docs.append(doc)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2, default=str)

async def main():
    client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=2000)
    try:
        db = client.get_default_database()
    except Exception:
        db = client.openinfra_gis

    # Create backup directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(__file__).parent / "backup" / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Iterate over collections
    collection_names = await db.list_collection_names()
    print(f"Found collections: {collection_names}")
    for name in collection_names:
        col = db[name]
        out_file = backup_dir / f"{name}.json"
        print(f"Backing up collection '{name}' to {out_file}")
        await dump_collection(col, out_file)
    print(f"Backup completed. Files stored in {backup_dir}")

if __name__ == "__main__":
    asyncio.run(main())
