import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import pymongo

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from app.core.config import settings
from app.core.security import get_password_hash


def main():
    load_dotenv()  # load .env if present

    username = os.getenv("ADMIN_DEFAULT_USERNAME", settings.ADMIN_DEFAULT_USERNAME)
    password = os.getenv("ADMIN_DEFAULT_PASSWORD", settings.ADMIN_DEFAULT_PASSWORD)
    email = os.getenv("ADMIN_DEFAULT_EMAIL", f"{username}@openinfra.space")

    client = pymongo.MongoClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    users = db.users

    users.create_index("username", unique=True)
    users.create_index("email", unique=True)

    # Check if admin user exists
    existing = users.find_one({"username": username})
    if existing:
        print(f"Superuser already exists: username='{username}'")
        return

    hashed = get_password_hash(password)
    
    # Admin permissions
    admin_permissions = [
        "view_all_assets", "create_asset", "update_asset", "delete_asset",
        "view_all_maintenance", "create_maintenance", "update_maintenance",
        "view_all_incidents", "assign_incidents",
        "manage_users", "manage_budgets", "approve_budgets",
        "view_all_reports", "generate_reports", "manage_iot"
    ]

    now = datetime.utcnow()
    users.insert_one({
        "username": username,
        "email": email,
        "password_hash": hashed,
        "full_name": "System Administrator",
        "phone": None,
        "role": "admin",
        "permissions": admin_permissions,
        "department": None,
        "avatar_url": None,
        "status": "active",
        "language": "vi",
        "notification_preferences": {"email": True, "push": True, "sms": False},
        "last_login": None,
        "created_at": now,
        "updated_at": now,
        "created_by": None,
        "metadata": {}
    })

    print(f"Superuser created: username='{username}', password='{password}'")


if __name__ == "__main__":
    main()
