#!/usr/bin/env python3
"""Database seeding script - creates sample data for development and testing."""
import asyncio
import sys
import os
import random
from datetime import datetime, timedelta
from typing import List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.security import get_password_hash
from app.core.logging import setup_logging
from app.domain.models.user import UserRole, UserStatus
from app.domain.models.asset import AssetStatus, AssetCondition, LifecycleStage
from app.domain.models.incident import (
    IncidentCategory,
    IncidentSeverity,
    IncidentStatus,
    ReporterType,
)
from app.domain.models.maintenance import (
    MaintenanceType,
    MaintenancePriority,
    MaintenanceStatus,
)
from app.domain.models.budget import (
    BudgetCategory,
    BudgetStatus,
    BudgetPeriodType,
)

logger = setup_logging()


# Sample data generators
def generate_phone() -> str:
    """Generate a Vietnamese phone number."""
    return f"0{random.randint(3, 9)}{random.randint(10000000, 99999999)}"


def generate_asset_code(feature_code: str, index: int) -> str:
    """Generate asset code."""
    return f"{feature_code.upper()}-{index:04d}"


def generate_incident_number(index: int) -> str:
    """Generate incident number."""
    year = datetime.now().year
    return f"INC-{year}-{index:05d}"


def generate_work_order_number(index: int) -> str:
    """Generate work order number."""
    year = datetime.now().year
    return f"WO-{year}-{index:05d}"


def generate_budget_code(fiscal_year: int, category: str, index: int) -> str:
    """Generate budget code."""
    return f"BUD-{fiscal_year}-{category.upper()[:3]}-{index:03d}"


def generate_transaction_number(index: int) -> str:
    """Generate transaction number."""
    year = datetime.now().year
    return f"TXN-{year}-{index:06d}"


# Sample locations (Da Nang, Vietnam coordinates)
SAMPLE_LOCATIONS = [
    {"lat": 16.0544, "lng": 108.2022},  # Da Nang city center
    {"lat": 16.0678, "lng": 108.2208},  # Hai Chau district
    {"lat": 16.0479, "lng": 108.2068},  # Thanh Khe district
    {"lat": 16.0600, "lng": 108.2300},  # Son Tra district
    {"lat": 16.0400, "lng": 108.1900},  # Ngu Hanh Son district
]

# Sample feature types and codes
FEATURE_TYPES = [
    {
        "feature_type": "drainage",
        "feature_code": "cong_thoat_nuoc",
        "category": "infrastructure",
    },
    {
        "feature_type": "street_light",
        "feature_code": "den_chieu_sang",
        "category": "lighting",
    },
    {
        "feature_type": "traffic_sign",
        "feature_code": "bien_bao_giao_thong",
        "category": "traffic",
    },
    {"feature_type": "bench", "feature_code": "ghe_da", "category": "furniture"},
    {"feature_type": "tree", "feature_code": "cay_xanh", "category": "greenery"},
    {
        "feature_type": "waste_bin",
        "feature_code": "thung_rac",
        "category": "sanitation",
    },
]


async def seed_users(db, count: int = 20) -> List[str]:
    """Seed users with different roles."""
    logger.info(f"Seeding {count} users...")

    users_data = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "password_hash": get_password_hash("admin123"),
            "full_name": "System Administrator",
            "phone": generate_phone(),
            "role": UserRole.ADMIN.value,
            "status": UserStatus.ACTIVE.value,
            "department": "IT",
            "permissions": ["*"],
            "created_at": datetime.utcnow() - timedelta(days=365),
        },
        {
            "username": "technician1",
            "email": "tech1@example.com",
            "password_hash": get_password_hash("tech123"),
            "full_name": "Nguyen Van A",
            "phone": generate_phone(),
            "role": UserRole.TECHNICIAN.value,
            "status": UserStatus.ACTIVE.value,
            "department": "Maintenance",
            "permissions": ["maintenance:read", "maintenance:write"],
            "created_at": datetime.utcnow() - timedelta(days=180),
        },
        {
            "username": "technician2",
            "email": "tech2@example.com",
            "password_hash": get_password_hash("tech123"),
            "full_name": "Tran Thi B",
            "phone": generate_phone(),
            "role": UserRole.TECHNICIAN.value,
            "status": UserStatus.ACTIVE.value,
            "department": "Maintenance",
            "permissions": ["maintenance:read", "maintenance:write"],
            "created_at": datetime.utcnow() - timedelta(days=150),
        },
    ]

    # Add more technicians
    for i in range(3, min(count - 2, 8)):
        users_data.append(
            {
                "username": f"technician{i}",
                "email": f"tech{i}@example.com",
                "password_hash": get_password_hash("tech123"),
                "full_name": f"Technician {i}",
                "phone": generate_phone(),
                "role": UserRole.TECHNICIAN.value,
                "status": UserStatus.ACTIVE.value,
                "department": random.choice(
                    ["Maintenance", "Operations", "Field Service"]
                ),
                "permissions": ["maintenance:read", "maintenance:write"],
                "created_at": datetime.utcnow()
                - timedelta(days=random.randint(30, 120)),
            }
        )

    # Add citizens
    for i in range(len(users_data), count):
        users_data.append(
            {
                "username": f"citizen{i}",
                "email": f"citizen{i}@example.com",
                "password_hash": get_password_hash("citizen123"),
                "full_name": f"Citizen {i}",
                "phone": generate_phone(),
                "role": UserRole.CITIZEN.value,
                "status": UserStatus.ACTIVE.value,
                "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 90)),
            }
        )

    # Clear existing users (except keep admin if exists)
    await db.users.delete_many({"username": {"$ne": "admin"}})

    # Insert users
    result = await db.users.insert_many(users_data)
    user_ids = [str(id) for id in result.inserted_ids]

    logger.info(f"Created {len(user_ids)} users")
    return user_ids


async def seed_assets(
    db, count: int = 50, user_ids: Optional[List[str]] = None
) -> List[str]:
    """Seed assets."""
    logger.info(f"Seeding {count} assets...")

    if not user_ids:
        user_ids = [
            str(user["_id"]) for user in await db.users.find({}).to_list(length=100)
        ]

    assets_data = []
    asset_index = 1

    for feature_info in FEATURE_TYPES:
        feature_count = count // len(FEATURE_TYPES)
        for i in range(feature_count):
            location = random.choice(SAMPLE_LOCATIONS)
            geometry = {
                "type": "Point",
                "coordinates": [location["lng"], location["lat"]],
            }

            asset = {
                "asset_code": generate_asset_code(
                    feature_info["feature_code"], asset_index
                ),
                "name": f"{feature_info['feature_type'].replace('_', ' ').title()} {asset_index}",
                "feature_type": feature_info["feature_type"],
                "feature_code": feature_info["feature_code"],
                "category": feature_info["category"],
                "geometry": geometry,
                "location": {
                    "district": random.choice(
                        ["Hai Chau", "Thanh Khe", "Son Tra", "Ngu Hanh Son"]
                    ),
                    "ward": f"Ward {random.randint(1, 20)}",
                    "address": f"{random.randint(1, 200)} Street Name",
                },
                "status": random.choice(list(AssetStatus)).value,
                "condition": random.choice(list(AssetCondition)).value,
                "lifecycle_stage": random.choice(list(LifecycleStage)).value,
                "iot_enabled": random.choice([True, False]),
                "public_info_visible": random.choice([True, False]),
                "created_by": random.choice(user_ids) if user_ids else None,
                "created_at": datetime.utcnow()
                - timedelta(days=random.randint(1, 730)),
                "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            }

            assets_data.append(asset)
            asset_index += 1

    # Clear existing assets
    await db.assets.delete_many({})

    # Insert assets
    result = await db.assets.insert_many(assets_data)
    asset_ids = [str(id) for id in result.inserted_ids]

    logger.info(f"Created {len(asset_ids)} assets")
    return asset_ids


async def seed_incidents(
    db,
    count: int = 30,
    asset_ids: Optional[List[str]] = None,
    user_ids: Optional[List[str]] = None,
) -> List[str]:
    """Seed incidents."""
    logger.info(f"Seeding {count} incidents...")

    if not asset_ids:
        asset_ids = [
            str(asset["_id"]) for asset in await db.assets.find({}).to_list(length=100)
        ]
    if not user_ids:
        user_ids = [
            str(user["_id"]) for user in await db.users.find({}).to_list(length=100)
        ]

    incidents_data = []
    incident_index = 1

    for i in range(count):
        asset_id = random.choice(asset_ids) if asset_ids else None

        location = random.choice(SAMPLE_LOCATIONS)
        geometry = {
            "type": "Point",
            "coordinates": [location["lng"], location["lat"]],
        }

        status = random.choice(list(IncidentStatus))
        reported_at = datetime.utcnow() - timedelta(days=random.randint(0, 60))

        incident = {
            "incident_number": generate_incident_number(incident_index),
            "asset_id": asset_id,
            "title": f"Incident {incident_index}: {random.choice(['Damage', 'Malfunction', 'Safety Hazard', 'Vandalism'])}",
            "description": f"Detailed description of incident {incident_index}. This is a sample incident for testing purposes.",
            "category": random.choice(list(IncidentCategory)).value,
            "severity": random.choice(list(IncidentSeverity)).value,
            "status": status.value,
            "location": {
                "geometry": geometry,
                "address": f"{random.randint(1, 200)} Street Name",
                "description": "Near the intersection",
            },
            "reported_by": random.choice(user_ids) if user_ids else None,
            "reporter_type": random.choice(list(ReporterType)).value,
            "reported_via": random.choice(["web", "mobile", "qr_code", "phone"]),
            "reported_at": reported_at,
            "public_visible": random.choice([True, False]),
            "upvotes": random.randint(0, 50),
            "created_at": reported_at,
            "updated_at": reported_at + timedelta(days=random.randint(0, 5)),
        }

        # Add assignment and resolution for some incidents
        if status in [
            IncidentStatus.ACKNOWLEDGED,
            IncidentStatus.INVESTIGATING,
            IncidentStatus.RESOLVED,
            IncidentStatus.CLOSED,
        ]:
            incident["assigned_to"] = random.choice(user_ids) if user_ids else None
            incident["acknowledged_at"] = reported_at + timedelta(
                hours=random.randint(1, 24)
            )
            incident["acknowledged_by"] = incident["assigned_to"]

        if status in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
            incident["resolved_at"] = reported_at + timedelta(days=random.randint(1, 7))
            incident["resolved_by"] = incident["assigned_to"]
            incident["resolution_notes"] = "Issue has been resolved successfully."
            incident["resolution_type"] = "fixed"

        if status == IncidentStatus.CLOSED:
            incident["closed_at"] = incident["resolved_at"] + timedelta(
                days=random.randint(1, 3)
            )

        incidents_data.append(incident)
        incident_index += 1

    # Clear existing incidents
    await db.incidents.delete_many({})

    # Insert incidents
    result = await db.incidents.insert_many(incidents_data)
    incident_ids = [str(id) for id in result.inserted_ids]

    logger.info(f"Created {len(incident_ids)} incidents")
    return incident_ids


async def seed_maintenance_records(
    db,
    count: int = 25,
    asset_ids: Optional[List[str]] = None,
    user_ids: Optional[List[str]] = None,
) -> List[str]:
    """Seed maintenance records."""
    logger.info(f"Seeding {count} maintenance records...")

    if not asset_ids:
        asset_ids = [
            str(asset["_id"]) for asset in await db.assets.find({}).to_list(length=100)
        ]
    if not user_ids:
        user_ids = [
            str(user["_id"]) for user in await db.users.find({}).to_list(length=100)
        ]

    maintenance_data = []
    wo_index = 1

    for i in range(count):
        asset_id = random.choice(asset_ids) if asset_ids else None
        status = random.choice(list(MaintenanceStatus))
        scheduled_date = datetime.utcnow() + timedelta(days=random.randint(-30, 30))

        maintenance = {
            "work_order_number": generate_work_order_number(wo_index),
            "asset_id": asset_id,
            "type": random.choice(list(MaintenanceType)).value,
            "priority": random.choice(list(MaintenancePriority)).value,
            "title": f"Maintenance Work Order {wo_index}",
            "description": f"Maintenance task description for work order {wo_index}",
            "status": status.value,
            "scheduled_date": scheduled_date,
            "estimated_duration": random.randint(30, 480),  # 30 minutes to 8 hours
            "assigned_to": random.choice(user_ids) if user_ids else None,
            "created_at": scheduled_date - timedelta(days=random.randint(1, 14)),
            "updated_at": scheduled_date - timedelta(days=random.randint(0, 7)),
        }

        # Add execution details for completed maintenance
        if status == MaintenanceStatus.COMPLETED:
            maintenance["actual_start_time"] = scheduled_date + timedelta(
                minutes=random.randint(0, 60)
            )
            maintenance["actual_end_time"] = maintenance[
                "actual_start_time"
            ] + timedelta(
                minutes=maintenance["estimated_duration"] + random.randint(-30, 60)
            )
            maintenance["actual_duration"] = (
                maintenance["actual_end_time"] - maintenance["actual_start_time"]
            ).total_seconds() / 60
            maintenance["work_performed"] = "Maintenance work completed successfully."
            maintenance["total_cost"] = random.uniform(100000, 5000000)  # VND
            maintenance["labor_cost"] = maintenance["total_cost"] * 0.6
            maintenance["parts_cost"] = maintenance["total_cost"] * 0.4
            maintenance["completed_by"] = maintenance["assigned_to"]

        # Add in-progress details
        if status == MaintenanceStatus.IN_PROGRESS:
            maintenance["actual_start_time"] = scheduled_date + timedelta(
                minutes=random.randint(0, 60)
            )

        maintenance_data.append(maintenance)
        wo_index += 1

    # Clear existing maintenance records
    await db.maintenance_records.delete_many({})

    # Insert maintenance records
    result = await db.maintenance_records.insert_many(maintenance_data)
    maintenance_ids = [str(id) for id in result.inserted_ids]

    logger.info(f"Created {len(maintenance_ids)} maintenance records")
    return maintenance_ids


async def seed_budgets(
    db, count: int = 5, user_ids: Optional[List[str]] = None
) -> List[str]:
    """Seed budgets."""
    logger.info(f"Seeding {count} budgets...")

    if not user_ids:
        user_ids = [
            str(user["_id"]) for user in await db.users.find({}).to_list(length=100)
        ]

    budgets_data = []
    budget_index = 1
    current_year = datetime.now().year

    for i in range(count):
        fiscal_year = current_year - (count - i - 1)
        start_date = datetime(fiscal_year, 1, 1)
        end_date = datetime(fiscal_year, 12, 31)

        total_allocated = random.uniform(100000000, 1000000000)  # 100M to 1B VND

        budget = {
            "budget_code": generate_budget_code(
                fiscal_year, random.choice(list(BudgetCategory)).value, budget_index
            ),
            "fiscal_year": fiscal_year,
            "period_type": BudgetPeriodType.ANNUAL.value,
            "start_date": start_date,
            "end_date": end_date,
            "name": f"Budget {fiscal_year} - {random.choice(list(BudgetCategory)).value.title()}",
            "description": f"Annual budget for {fiscal_year}",
            "category": random.choice(list(BudgetCategory)).value,
            "total_allocated": total_allocated,
            "currency": "VND",
            "status": random.choice(list(BudgetStatus)).value,
            "created_by": random.choice(user_ids) if user_ids else None,
            "created_at": start_date - timedelta(days=30),
            "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
        }

        # Add department allocations
        budget["departments"] = [
            {
                "department": "Maintenance",
                "allocated_amount": total_allocated * 0.4,
                "spent_amount": 0,
                "remaining_amount": total_allocated * 0.4,
            },
            {
                "department": "Operations",
                "allocated_amount": total_allocated * 0.3,
                "spent_amount": 0,
                "remaining_amount": total_allocated * 0.3,
            },
            {
                "department": "Capital",
                "allocated_amount": total_allocated * 0.3,
                "spent_amount": 0,
                "remaining_amount": total_allocated * 0.3,
            },
        ]

        # Add breakdown
        budget["breakdown"] = [
            {
                "category": "labor",
                "allocated": total_allocated * 0.5,
                "spent": 0,
                "remaining": total_allocated * 0.5,
            },
            {
                "category": "materials",
                "allocated": total_allocated * 0.3,
                "spent": 0,
                "remaining": total_allocated * 0.3,
            },
            {
                "category": "equipment",
                "allocated": total_allocated * 0.2,
                "spent": 0,
                "remaining": total_allocated * 0.2,
            },
        ]

        if budget["status"] == BudgetStatus.APPROVED:
            budget["approved_by"] = random.choice(user_ids) if user_ids else None
            budget["approved_at"] = budget["created_at"] + timedelta(
                days=random.randint(1, 7)
            )

        budgets_data.append(budget)
        budget_index += 1

    # Clear existing budgets
    await db.budgets.delete_many({})

    # Insert budgets
    result = await db.budgets.insert_many(budgets_data)
    budget_ids = [str(id) for id in result.inserted_ids]

    logger.info(f"Created {len(budget_ids)} budgets")
    return budget_ids


async def seed_budget_transactions(
    db,
    count: int = 20,
    budget_ids: Optional[List[str]] = None,
    maintenance_ids: Optional[List[str]] = None,
    asset_ids: Optional[List[str]] = None,
) -> List[str]:
    """Seed budget transactions."""
    logger.info(f"Seeding {count} budget transactions...")

    if not budget_ids:
        budget_ids = [
            str(budget["_id"])
            for budget in await db.budgets.find({}).to_list(length=100)
        ]
    if not maintenance_ids:
        maintenance_ids = [
            str(maint["_id"])
            for maint in await db.maintenance_records.find({}).to_list(length=100)
        ]
    if not asset_ids:
        asset_ids = [
            str(asset["_id"]) for asset in await db.assets.find({}).to_list(length=100)
        ]

    transactions_data = []
    txn_index = 1

    for i in range(count):
        budget_id = random.choice(budget_ids) if budget_ids else None
        amount = random.uniform(50000, 2000000)  # 50K to 2M VND

        transaction = {
            "transaction_number": generate_transaction_number(txn_index),
            "budget_id": budget_id,
            "amount": amount,
            "currency": "VND",
            "transaction_date": datetime.utcnow()
            - timedelta(days=random.randint(0, 90)),
            "description": f"Transaction {txn_index}: {random.choice(['Labor', 'Materials', 'Equipment', 'Contractor'])}",
            "category": random.choice(
                ["labor", "materials", "equipment", "contractors", "other"]
            ),
            "maintenance_record_id": (
                random.choice(maintenance_ids)
                if maintenance_ids and random.random() > 0.5
                else None
            ),
            "asset_id": (
                random.choice(asset_ids)
                if asset_ids and random.random() > 0.3
                else None
            ),
            "status": random.choice(["pending", "approved", "paid"]),
            "created_at": datetime.utcnow() - timedelta(days=random.randint(0, 90)),
            "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
        }

        if transaction["status"] == "approved":
            transaction["approved_at"] = transaction["created_at"] + timedelta(
                days=random.randint(1, 7)
            )

        if transaction["status"] == "paid":
            transaction["approved_at"] = transaction["created_at"] + timedelta(
                days=random.randint(1, 7)
            )
            transaction["payment_date"] = transaction["approved_at"] + timedelta(
                days=random.randint(1, 14)
            )
            transaction["payment_method"] = random.choice(["cash", "transfer", "check"])

        transactions_data.append(transaction)
        txn_index += 1

    # Clear existing transactions
    await db.budget_transactions.delete_many({})

    # Insert transactions
    result = await db.budget_transactions.insert_many(transactions_data)
    transaction_ids = [str(id) for id in result.inserted_ids]

    logger.info(f"Created {len(transaction_ids)} budget transactions")
    return transaction_ids


async def seed_database(
    users: int = 20,
    assets: int = 50,
    incidents: int = 30,
    maintenance: int = 25,
    budgets: int = 5,
    transactions: int = 20,
    clear_existing: bool = False,
):
    """Main seeding function."""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    try:
        logger.info("=" * 60)
        logger.info("DATABASE SEEDING STARTED")
        logger.info("=" * 60)
        logger.info(f"Database: {settings.DATABASE_NAME}")
        logger.info(f"MongoDB URL: {settings.MONGODB_URL}")
        logger.info("=" * 60)

        if clear_existing:
            logger.info("Clearing existing seed data...")
            await db.users.delete_many({})
            await db.assets.delete_many({})
            await db.incidents.delete_many({})
            await db.maintenance_records.delete_many({})
            await db.budgets.delete_many({})
            await db.budget_transactions.delete_many({})

        # Seed in order (respecting dependencies)
        user_ids = await seed_users(db, count=users)
        asset_ids = await seed_assets(db, count=assets, user_ids=user_ids)
        await seed_incidents(
            db, count=incidents, asset_ids=asset_ids, user_ids=user_ids
        )
        maintenance_ids = await seed_maintenance_records(
            db, count=maintenance, asset_ids=asset_ids, user_ids=user_ids
        )
        budget_ids = await seed_budgets(db, count=budgets, user_ids=user_ids)
        await seed_budget_transactions(
            db,
            count=transactions,
            budget_ids=budget_ids,
            maintenance_ids=maintenance_ids,
            asset_ids=asset_ids,
        )

        logger.info("=" * 60)
        logger.info("DATABASE SEEDING COMPLETED")
        logger.info("=" * 60)
        logger.info("Summary:")
        logger.info(f"  - Users: {await db.users.count_documents({})}")
        logger.info(f"  - Assets: {await db.assets.count_documents({})}")
        logger.info(f"  - Incidents: {await db.incidents.count_documents({})}")
        logger.info(
            f"  - Maintenance Records: {await db.maintenance_records.count_documents({})}"
        )
        logger.info(f"  - Budgets: {await db.budgets.count_documents({})}")
        logger.info(
            f"  - Budget Transactions: {await db.budget_transactions.count_documents({})}"
        )
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        raise
    finally:
        client.close()
        logger.info("Database connection closed")


async def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed the database with sample data")
    parser.add_argument(
        "--users", type=int, default=20, help="Number of users to create"
    )
    parser.add_argument(
        "--assets", type=int, default=50, help="Number of assets to create"
    )
    parser.add_argument(
        "--incidents", type=int, default=30, help="Number of incidents to create"
    )
    parser.add_argument(
        "--maintenance",
        type=int,
        default=25,
        help="Number of maintenance records to create",
    )
    parser.add_argument(
        "--budgets", type=int, default=5, help="Number of budgets to create"
    )
    parser.add_argument(
        "--transactions",
        type=int,
        default=20,
        help="Number of budget transactions to create",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all existing seed data before seeding (users, assets, incidents, etc.)",
    )

    args = parser.parse_args()

    await seed_database(
        users=args.users,
        assets=args.assets,
        incidents=args.incidents,
        maintenance=args.maintenance,
        budgets=args.budgets,
        transactions=args.transactions,
        clear_existing=args.clear,
    )


if __name__ == "__main__":
    asyncio.run(main())
