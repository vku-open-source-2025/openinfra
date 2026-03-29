import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")

async def migrate():
    print(f"Connecting to MongoDB at {MONGO_URL}...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.openinfra_gis
    collection = db.contributions

    # 1. Update all documents that don't have 'unit' to have 'unit': 'VKU'
    print("Setting default unit to 'VKU' for all contributions...")
    result = await collection.update_many(
        {"unit": {"$exists": False}},
        {"$set": {"unit": "VKU"}}
    )
    print(f"Updated {result.modified_count} documents with default unit 'VKU'.")

    # 2. Update specific user: Hồ Trịnh Thảo My (THPT Đông Hà)
    print("Updating specific contributor 'Hồ Trịnh Thảo My (THPT Đông Hà)'...")
    target_name = "Hồ Trịnh Thảo My (THPT Đông Hà)"
    new_name = "Hồ Trịnh Thảo My"
    new_unit = "THPT Đông Hà - Quảng Trị"

    result_specific = await collection.update_many(
        {"contributor_name": target_name},
        {"$set": {
            "contributor_name": new_name,
            "unit": new_unit
        }}
    )
    print(f"Updated {result_specific.modified_count} documents for {target_name}.")

    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
