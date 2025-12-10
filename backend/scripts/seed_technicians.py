#!/usr/bin/env python3
"""Script to seed technicians in the database."""
import asyncio
import sys
import os
import random
from datetime import datetime, timedelta
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.security import get_password_hash
from app.core.logging import setup_logging
from app.domain.models.user import UserRole, UserStatus
from app.db.mongodb import db

logger = setup_logging()


# Vietnamese first names (common)
VIETNAMESE_FIRST_NAMES = [
    "Van",
    "Thi",
    "Duc",
    "Minh",
    "Anh",
    "Hai",
    "Quang",
    "Hung",
    "Tuan",
    "Nam",
    "Long",
    "Khanh",
    "Dung",
    "Phuong",
    "Linh",
    "Hoa",
    "Lan",
    "Mai",
    "Huong",
    "Nga",
    "Thanh",
    "Tien",
    "Hoang",
    "Trung",
    "Kien",
    "Cuong",
    "Son",
    "Dai",
    "Binh",
    "Khoa",
]

# Vietnamese last names (common)
VIETNAMESE_LAST_NAMES = [
    "Nguyen",
    "Tran",
    "Le",
    "Pham",
    "Hoang",
    "Vu",
    "Vo",
    "Dang",
    "Bui",
    "Do",
    "Ho",
    "Ngo",
    "Duong",
    "Ly",
    "Phan",
    "Truong",
    "Dinh",
    "Dao",
    "Lam",
    "Ninh",
]

# Departments for technicians
DEPARTMENTS = [
    "Maintenance",
    "Operations",
    "Field Service",
    "Electrical",
    "Infrastructure",
    "Traffic Management",
    "Public Works",
    "Emergency Response",
    "Quality Assurance",
    "Technical Support",
]

# Technician permissions
TECHNICIAN_PERMISSIONS = [
    "maintenance:read",
    "maintenance:write",
    "assets:read",
    "assets:update",
    "incidents:read",
    "incidents:update",
    "work_orders:read",
    "work_orders:write",
]


def generate_phone() -> str:
    """Generate a Vietnamese phone number."""
    return f"0{random.randint(3, 9)}{random.randint(10000000, 99999999)}"


def generate_vietnamese_name() -> str:
    """Generate a realistic Vietnamese full name."""
    last_name = random.choice(VIETNAMESE_LAST_NAMES)
    first_name = random.choice(VIETNAMESE_FIRST_NAMES)
    # Sometimes add a middle name
    if random.random() > 0.5:
        middle_name = random.choice(VIETNAMESE_FIRST_NAMES)
        return f"{last_name} {middle_name} {first_name}"
    return f"{last_name} {first_name}"


async def seed_technicians(
    db, count: int = 10, clear_existing: bool = False, default_password: str = "tech123"
) -> List[str]:
    """
    Seed technicians in the database.

    Args:
        db: MongoDB database instance
        count: Number of technicians to create
        clear_existing: Whether to clear existing technicians before seeding
        default_password: Default password for all technicians

    Returns:
        List of created technician IDs
    """
    logger.info(f"Seeding {count} technicians...")

    if clear_existing:
        logger.info("Clearing existing technicians...")
        result = await db.users.delete_many({"role": UserRole.TECHNICIAN.value})
        logger.info(f"Deleted {result.deleted_count} existing technicians")

    # Check existing technician count
    existing_count = await db.users.count_documents({"role": UserRole.TECHNICIAN.value})
    logger.info(f"Found {existing_count} existing technicians")

    technicians_data = []

    # Generate unique usernames and emails
    used_usernames = set()
    used_emails = set()

    # Get existing usernames and emails to avoid duplicates
    existing_users = await db.users.find({}, {"username": 1, "email": 1}).to_list(
        length=1000
    )
    for user in existing_users:
        used_usernames.add(user.get("username", "").lower())
        used_emails.add(user.get("email", "").lower())

    for i in range(count):
        # Generate unique username
        base_username = f"tech{existing_count + i + 1}"
        username = base_username
        counter = 1
        while username.lower() in used_usernames:
            username = f"{base_username}{counter}"
            counter += 1
        used_usernames.add(username.lower())

        # Generate unique email
        base_email = f"tech{existing_count + i + 1}@openinfra.space"
        email = base_email
        counter = 1
        while email.lower() in used_emails:
            email = f"tech{existing_count + i + 1 + counter}@openinfra.space"
            counter += 1
        used_emails.add(email.lower())

        # Generate technician data
        full_name = generate_vietnamese_name()
        department = random.choice(DEPARTMENTS)

        # Vary creation dates
        created_days_ago = random.randint(1, 365)
        created_at = datetime.utcnow() - timedelta(days=created_days_ago)

        # Most technicians are active, some might be inactive
        status_weights = [UserStatus.ACTIVE] * 9 + [UserStatus.INACTIVE] * 1
        status = random.choice(status_weights)

        technician = {
            "username": username,
            "email": email,
            "password_hash": get_password_hash(default_password),
            "full_name": full_name,
            "phone": generate_phone(),
            "role": UserRole.TECHNICIAN.value,
            "status": status.value,
            "department": department,
            "permissions": TECHNICIAN_PERMISSIONS.copy(),
            "language": random.choice(["vi", "en"]),
            "notification_preferences": {
                "email": True,
                "push": True,
                "sms": random.choice([True, False]),
            },
            "created_at": created_at,
            "updated_at": created_at,
            "created_by": None,
            "metadata": {"seeded": True, "seeded_at": datetime.utcnow().isoformat()},
        }

        # Add last_login for some technicians (simulating active users)
        if status == UserStatus.ACTIVE and random.random() > 0.3:
            login_days_ago = random.randint(0, 30)
            technician["last_login"] = datetime.utcnow() - timedelta(
                days=login_days_ago
            )

        technicians_data.append(technician)

    # Insert technicians
    if technicians_data:
        result = await db.users.insert_many(technicians_data)
        technician_ids = [str(id) for id in result.inserted_ids]
        logger.info(f"Created {len(technician_ids)} technicians")

        # Log summary
        logger.info("Technician summary:")
        for tech in technicians_data:
            logger.info(
                f"  - {tech['username']}: {tech['full_name']} ({tech['department']})"
            )

        return technician_ids
    else:
        logger.warning("No technicians to create")
        return []


async def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed technicians in the database")
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of technicians to create (default: 10)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all existing technicians before seeding",
    )
    parser.add_argument(
        "--password",
        type=str,
        default="tech123",
        help="Default password for technicians (default: tech123)",
    )

    args = parser.parse_args()

    # Connect to database
    try:
        db.connect()
        database = db.get_db()
        # Test connection
        await database.command("ping")
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error("=" * 60)
        logger.error("FAILED TO CONNECT TO DATABASE")
        logger.error("=" * 60)
        logger.error(f"Error: {e}")
        logger.error("=" * 60)
        logger.error("Troubleshooting:")
        logger.error("1. Make sure MongoDB is running")
        logger.error("2. If running locally, set MONGODB_URL environment variable:")
        logger.error("   export MONGODB_URL=mongodb://localhost:27017")
        logger.error("3. Or create a .env file with:")
        logger.error("   MONGODB_URL=mongodb://localhost:27017")
        logger.error(
            "4. If using Docker, make sure you're running inside Docker network"
        )
        logger.error("=" * 60)
        raise

    try:
        logger.info("=" * 60)
        logger.info("TECHNICIAN SEEDING STARTED")
        logger.info("=" * 60)
        logger.info(f"Database: {settings.DATABASE_NAME}")
        logger.info(f"MongoDB URL: {settings.MONGODB_URL}")
        logger.info(f"Count: {args.count}")
        logger.info(f"Clear existing: {args.clear}")
        logger.info("=" * 60)

        technician_ids = await seed_technicians(
            database,
            count=args.count,
            clear_existing=args.clear,
            default_password=args.password,
        )

        # Final summary
        total_count = await database.users.count_documents(
            {"role": UserRole.TECHNICIAN.value}
        )
        logger.info("=" * 60)
        logger.info("TECHNICIAN SEEDING COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Total technicians in database: {total_count}")
        logger.info(f"Created in this run: {len(technician_ids)}")
        logger.info("=" * 60)
        logger.info(f"Default password for all technicians: {args.password}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Technician seeding failed: {e}", exc_info=True)
        raise
    finally:
        db.close()
        logger.info("Database connection closed")


if __name__ == "__main__":
    asyncio.run(main())
