"""Create admin accounts for OpenInfra.

Run inside the backend container:
  docker compose exec backend python /app/scripts/create_admins.py
"""

import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os
import bcrypt

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongo:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "openinfra")

ADMIN_PERMISSIONS = [
    "view_all_assets", "create_asset", "update_asset", "delete_asset",
    "view_all_maintenance", "create_maintenance", "update_maintenance",
    "view_all_incidents", "assign_incidents",
    "manage_users", "manage_budgets", "approve_budgets",
    "view_all_reports", "generate_reports", "manage_iot",
]

ACCOUNTS = [
    {
        "username": "admin",
        "email": "admin@openinfra.space",
        "password": "admin123@nhanhobede",
        "full_name": "System Administrator",
        "role": "admin",
    },
    {
        "username": "baonhan",
        "email": "baonhan@openinfra.space",
        "password": "BaoNhan@2025!",
        "full_name": "Hồ Sỹ Bảo Nhân",
        "role": "admin",
    },
    {
        "username": "demo_admin",
        "email": "demo@openinfra.space",
        "password": "Demo@OpenInfra2025",
        "full_name": "Demo Admin",
        "role": "admin",
    },
    {
        "username": "judge",
        "email": "judge@openinfra.space",
        "password": "Judge@VKU2025!",
        "full_name": "Judge / Reviewer",
        "role": "admin",
    },
]


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


async def main():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    users = db["users"]

    # Ensure unique indexes
    await users.create_index("username", unique=True)
    await users.create_index("email", unique=True)

    now = datetime.utcnow()

    for acct in ACCOUNTS:
        existing = await users.find_one({"username": acct["username"]})
        if existing:
            print(f"  [SKIP] {acct['username']} already exists")
            continue

        doc = {
            "username": acct["username"],
            "email": acct["email"],
            "password_hash": hash_password(acct["password"]),
            "full_name": acct["full_name"],
            "phone": None,
            "role": acct["role"],
            "permissions": ADMIN_PERMISSIONS,
            "department": None,
            "avatar_url": None,
            "status": "active",
            "language": "vi",
            "notification_preferences": {"email": True, "push": True, "sms": False},
            "last_login": None,
            "created_at": now,
            "updated_at": now,
            "created_by": None,
            "metadata": {},
        }
        await users.insert_one(doc)
        print(f"  [OK]   {acct['username']}  ({acct['email']})")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
