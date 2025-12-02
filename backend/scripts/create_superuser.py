import os
import sys
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

    client = pymongo.MongoClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    admins = db.admins

    admins.create_index("username", unique=True)

    # Remove existing admins to ensure a clean reset
    admins.delete_many({})

    hashed = get_password_hash(password)
    admins.insert_one(
        {
            "username": username,
            "password_hash": hashed,
            "role": "admin",
        }
    )

    print(f"Superuser ensured: username='{username}', password='{password}'")


if __name__ == "__main__":
    main()
