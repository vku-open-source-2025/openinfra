#!/usr/bin/env python3
"""Script to seed technicians in the database."""
import asyncio
import sys
import os
import random
from datetime import datetime, timedelta
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.security import get_password_hash
from app.core.logging import setup_logging
from app.domain.models.user import UserRole, UserStatus
from app.domain.models.incident import (
    IncidentCategory,
    IncidentSeverity,
    IncidentStatus,
    ReporterType,
    ResolutionType,
)
from app.db.mongodb import db
from bson import ObjectId

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

# Sample locations for incidents
SAMPLE_LOCATIONS = [
    # Hai Chau District
    {"lat": 16.0544, "lng": 108.2022, "district": "Hai Chau", "ward": "Thach Thang"},
    {"lat": 16.0678, "lng": 108.2208, "district": "Hai Chau", "ward": "Hoa Cuong Bac"},
    {"lat": 16.0712, "lng": 108.2145, "district": "Hai Chau", "ward": "Binh Hien"},
    # Thanh Khe District
    {"lat": 16.0479, "lng": 108.2068, "district": "Thanh Khe", "ward": "Tam Thuan"},
    {"lat": 16.0634, "lng": 108.2015, "district": "Thanh Khe", "ward": "Thanh Khe Tay"},
    {"lat": 16.0723, "lng": 108.1956, "district": "Thanh Khe", "ward": "An Khe"},
    # Son Tra District
    {"lat": 16.0600, "lng": 108.2300, "district": "Son Tra", "ward": "Tho Quang"},
    {"lat": 16.0890, "lng": 108.2490, "district": "Son Tra", "ward": "Man Thai"},
    {"lat": 16.1050, "lng": 108.2656, "district": "Son Tra", "ward": "Bac My An"},
    # Ngu Hanh Son District
    {"lat": 16.0400, "lng": 108.1900, "district": "Ngu Hanh Son", "ward": "My An"},
    {"lat": 15.9956, "lng": 108.2634, "district": "Ngu Hanh Son", "ward": "Hoa Hai"},
    {"lat": 16.0234, "lng": 108.2456, "district": "Ngu Hanh Son", "ward": "Hoa Quy"},
    # Cam Le District
    {"lat": 16.0267, "lng": 108.1823, "district": "Cam Le", "ward": "Hoa Phat"},
    {"lat": 16.0156, "lng": 108.1678, "district": "Cam Le", "ward": "Hoa An"},
    # Lien Chieu District
    {"lat": 16.0812, "lng": 108.1456, "district": "Lien Chieu", "ward": "Hoa Minh"},
    {"lat": 16.0645, "lng": 108.1534, "district": "Lien Chieu", "ward": "Hoa Khanh Bac"},
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


def generate_incident_number(index: int) -> str:
    """Generate incident number."""
    year = datetime.now().year
    return f"INC-{year}-{index:05d}"


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


async def seed_vietnamese_duplicate_incidents(
    db,
    asset_ids: Optional[List[str]] = None,
    user_ids: Optional[List[str]] = None,
) -> List[str]:
    """
    Seed Vietnamese duplicate incidents for testing duplicate display in incident reports.
    
    LOGIC FOR DUPLICATE INCIDENTS:
    ===============================
    According to merge service logic (incident_merge_service.py), the PRIMARY ticket
    is always the OLDEST ticket (earliest reported_at). Therefore:
    
    1. PRIMARY TICKET (Main ticket):
       - Reported FIRST: 7-10 days ago
       - Status: INVESTIGATING (still active, shown in "useful" tab)
       - This is the ticket that appears in "useful" tab
    
    2. DUPLICATE TICKETS (Child tickets):
       - Reported AFTER primary: 1-5 days after primary ticket
       - Status: RESOLVED with resolution_type = DUPLICATE
       - Resolved 1-3 days after being reported
       - These appear in "duplicates" tab grouped under primary ticket
    
    Example timeline:
    - Day 0: Primary ticket reported (7 days ago)
    - Day 2: Duplicate ticket #1 reported (5 days ago)
    - Day 3: Duplicate ticket #1 resolved as duplicate
    - Day 4: Duplicate ticket #2 reported (3 days ago)
    - Day 6: Duplicate ticket #2 resolved as duplicate
    
    This ensures primary ticket is always the oldest, matching merge service behavior.
    
    Args:
        db: MongoDB database instance
        asset_ids: Optional list of asset IDs to use
        user_ids: Optional list of user IDs to use as reporters/resolvers
        
    Returns:
        List of created incident IDs
    """
    logger.info("Seeding Vietnamese duplicate incidents...")
    
    if not asset_ids:
        asset_ids = [
            str(asset["_id"]) for asset in await db.assets.find({}).to_list(length=100)
        ]
    if not user_ids:
        user_ids = [
            str(user["_id"]) for user in await db.users.find({}).to_list(length=100)
        ]
    
    # Vietnamese duplicate incident scenarios
    duplicate_groups = [
        {
            "primary": {
                "title": "Đèn đường không hoạt động tại ngã tư",
                "description": "Đèn đường tại ngã tư đường Bạch Đằng và Trần Phú không sáng vào ban đêm, gây nguy hiểm cho người đi đường.",
                "category": IncidentCategory.MALFUNCTION,
                "severity": IncidentSeverity.HIGH,
            },
            "duplicates": [
                {
                    "title": "Đèn đường bị hỏng ở ngã tư Bạch Đằng",
                    "description": "Đèn đường không hoạt động tại ngã tư đường Bạch Đằng, khu vực tối vào ban đêm.",
                    "category": IncidentCategory.MALFUNCTION,
                    "severity": IncidentSeverity.MEDIUM,
                },
                {
                    "title": "Đèn chiếu sáng không sáng",
                    "description": "Đèn chiếu sáng tại khu vực ngã tư không hoạt động, cần kiểm tra và sửa chữa.",
                    "category": IncidentCategory.MALFUNCTION,
                    "severity": IncidentSeverity.MEDIUM,
                },
            ],
        },
        {
            "primary": {
                "title": "Ống cống bị tắc nghẽn gây ngập lụt",
                "description": "Hệ thống thoát nước bị tắc nghẽn do rác thải và bùn đất, gây ngập lụt trên đường sau khi mưa lớn.",
                "category": IncidentCategory.DAMAGE,
                "severity": IncidentSeverity.HIGH,
            },
            "duplicates": [
                {
                    "title": "Cống thoát nước bị nghẹt",
                    "description": "Cống thoát nước bị tắc do rác thải, nước không thể thoát được.",
                    "category": IncidentCategory.DAMAGE,
                    "severity": IncidentSeverity.MEDIUM,
                },
                {
                    "title": "Đường bị ngập do cống tắc",
                    "description": "Sau cơn mưa, đường bị ngập nước do hệ thống thoát nước không hoạt động.",
                    "category": IncidentCategory.SAFETY_HAZARD,
                    "severity": IncidentSeverity.HIGH,
                },
            ],
        },
        {
            "primary": {
                "title": "Biển báo giao thông bị hư hỏng",
                "description": "Biển báo giao thông bị cong vênh và không còn rõ ràng, ảnh hưởng đến an toàn giao thông.",
                "category": IncidentCategory.DAMAGE,
                "severity": IncidentSeverity.MEDIUM,
            },
            "duplicates": [
                {
                    "title": "Biển hiệu bị hỏng",
                    "description": "Biển báo giao thông bị hư hỏng, cần thay thế.",
                    "category": IncidentCategory.DAMAGE,
                    "severity": IncidentSeverity.LOW,
                },
            ],
        },
        {
            "primary": {
                "title": "Vỉa hè bị nứt vỡ gây nguy hiểm",
                "description": "Vỉa hè có nhiều chỗ nứt vỡ và lồi lõm, tạo nguy cơ vấp ngã cho người đi bộ, đặc biệt là người già và trẻ em.",
                "category": IncidentCategory.DAMAGE,
                "severity": IncidentSeverity.MEDIUM,
            },
            "duplicates": [
                {
                    "title": "Lề đường bị hỏng",
                    "description": "Vỉa hè bị nứt và không bằng phẳng, cần sửa chữa.",
                    "category": IncidentCategory.DAMAGE,
                    "severity": IncidentSeverity.MEDIUM,
                },
                {
                    "title": "Đường đi bộ bị hư hỏng",
                    "description": "Vỉa hè có nhiều chỗ nứt, gây khó khăn cho người đi bộ.",
                    "category": IncidentCategory.SAFETY_HAZARD,
                    "severity": IncidentSeverity.MEDIUM,
                },
            ],
        },
        {
            "primary": {
                "title": "Đèn giao thông không hoạt động",
                "description": "Đèn tín hiệu giao thông tại ngã tư không hoạt động, đèn đỏ sáng liên tục không chuyển sang xanh.",
                "category": IncidentCategory.MALFUNCTION,
                "severity": IncidentSeverity.CRITICAL,
            },
            "duplicates": [
                {
                    "title": "Đèn xanh đỏ không chạy",
                    "description": "Đèn giao thông bị hỏng, không chuyển đổi tín hiệu.",
                    "category": IncidentCategory.MALFUNCTION,
                    "severity": IncidentSeverity.HIGH,
                },
            ],
        },
        {
            "primary": {
                "title": "Cây xanh bị đổ sau cơn bão",
                "description": "Cây xanh lớn bị đổ do gió mạnh, chặn một phần đường và có nguy cơ gây tai nạn.",
                "category": IncidentCategory.DAMAGE,
                "severity": IncidentSeverity.HIGH,
            },
            "duplicates": [
                {
                    "title": "Cây đổ chặn đường",
                    "description": "Cây lớn bị đổ xuống đường, cần dọn dẹp ngay.",
                    "category": IncidentCategory.SAFETY_HAZARD,
                    "severity": IncidentSeverity.HIGH,
                },
                {
                    "title": "Cây xanh bị gãy đổ",
                    "description": "Cây xanh bị đổ sau cơn bão, ảnh hưởng giao thông.",
                    "category": IncidentCategory.DAMAGE,
                    "severity": IncidentSeverity.MEDIUM,
                },
            ],
        },
        {
            "primary": {
                "title": "Hố ga bị mất nắp",
                "description": "Nắp hố ga bị mất hoặc bị hỏng, tạo nguy cơ tai nạn cho người đi đường và phương tiện.",
                "category": IncidentCategory.SAFETY_HAZARD,
                "severity": IncidentSeverity.HIGH,
            },
            "duplicates": [
                {
                    "title": "Nắp cống bị mất",
                    "description": "Nắp hố ga bị mất, rất nguy hiểm cho người đi đường.",
                    "category": IncidentCategory.SAFETY_HAZARD,
                    "severity": IncidentSeverity.HIGH,
                },
            ],
        },
    ]
    
    location = random.choice(SAMPLE_LOCATIONS)
    incident_ids = []
    incident_index = len(await db.incidents.find({}).to_list(length=1000)) + 1
    
    for group in duplicate_groups:
        # LOGIC: Primary ticket must be the OLDEST (reported first)
        # Duplicate tickets are reported AFTER primary ticket
        # This matches the merge service logic which selects oldest as primary
        
        # Primary ticket: reported 7-10 days ago (oldest)
        primary_days_ago = random.randint(7, 10)
        primary_reported_at = datetime.utcnow() - timedelta(days=primary_days_ago)
        
        primary_asset_id = random.choice(asset_ids) if asset_ids and len(asset_ids) > 0 else None
        geometry = {
            "type": "Point",
            "coordinates": [
                location["lng"] + random.uniform(-0.001, 0.001),
                location["lat"] + random.uniform(-0.001, 0.001),
            ],
        }
        
        primary_incident = {
            "incident_number": generate_incident_number(incident_index),
            "asset_id": primary_asset_id,
            "title": group["primary"]["title"],
            "description": group["primary"]["description"],
            "category": group["primary"]["category"].value,
            "severity": group["primary"]["severity"].value,
            "status": IncidentStatus.INVESTIGATING.value,
            "location": {
                "geometry": geometry,
                "address": f"{random.randint(1, 500)} {random.choice(['Bạch Đằng', 'Trần Phú', 'Nguyễn Văn Linh'])}",
                "description": f"Gần ngã tư {random.choice(['Bạch Đằng', 'Trần Phú'])}",
                "district": location["district"],
                "ward": location["ward"],
            },
            "reported_by": random.choice(user_ids) if user_ids and len(user_ids) > 0 else None,
            "reporter_type": ReporterType.CITIZEN.value,
            "reported_via": "web",
            "reported_at": primary_reported_at,  # Primary reported FIRST (oldest)
            "assigned_to": random.choice(user_ids) if user_ids and len(user_ids) > 0 else None,
            "acknowledged_at": primary_reported_at + timedelta(hours=random.randint(1, 12)),
            "acknowledged_by": random.choice(user_ids) if user_ids and len(user_ids) > 0 else None,
            "public_visible": True,
            "created_at": primary_reported_at,
            "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 2)),
            "related_incidents": [],  # Will be populated after creating duplicates
        }
        incident_index += 1
        
        # Create duplicate incidents - reported AFTER primary ticket
        duplicate_incident_ids = []
        for dup_scenario in group["duplicates"]:
            # Duplicate tickets: reported 1-5 days AFTER primary ticket
            # So if primary was 7 days ago, duplicates are 2-6 days ago (after primary)
            duplicate_days_ago = random.randint(1, 5)  # Days after primary
            duplicate_reported_at = primary_reported_at + timedelta(days=duplicate_days_ago)
            
            # Resolved as duplicate: resolved 1-3 days after being reported
            duplicate_resolved_at = duplicate_reported_at + timedelta(days=random.randint(1, 3))
            
            dup_geometry = {
                "type": "Point",
                "coordinates": [
                    geometry["coordinates"][0] + random.uniform(-0.0005, 0.0005),
                    geometry["coordinates"][1] + random.uniform(-0.0005, 0.0005),
                ],
            }
            
            dup_incident = {
                "incident_number": generate_incident_number(incident_index),
                "asset_id": primary_asset_id,  # Same asset
                "title": dup_scenario["title"],
                "description": dup_scenario["description"],
                "category": dup_scenario["category"].value,
                "severity": dup_scenario["severity"].value,
                "status": IncidentStatus.RESOLVED.value,
                "resolution_type": ResolutionType.DUPLICATE.value,
                "resolution_notes": f"Trùng lặp với sự cố {primary_incident['incident_number']}",
                "resolved_at": duplicate_resolved_at,  # Resolved after being reported
                "resolved_by": random.choice(user_ids) if user_ids and len(user_ids) > 0 else None,
                "location": {
                    "geometry": dup_geometry,
                    "address": primary_incident["location"]["address"],
                    "description": primary_incident["location"]["description"],
                    "district": location["district"],
                    "ward": location["ward"],
                },
                "reported_by": random.choice(user_ids) if user_ids and len(user_ids) > 0 else None,
                "reporter_type": ReporterType.CITIZEN.value,
                "reported_via": random.choice(["web", "mobile"]),
                "reported_at": duplicate_reported_at,  # Reported AFTER primary ticket
                "public_visible": True,
                "created_at": duplicate_reported_at,
                "updated_at": duplicate_resolved_at,
                "related_incidents": [],  # Will link to primary
            }
            duplicate_incident_ids.append(dup_incident)
            incident_index += 1
        
        # Insert all incidents
        all_incidents = [primary_incident] + duplicate_incident_ids
        result = await db.incidents.insert_many(all_incidents)
        inserted_ids = [str(id) for id in result.inserted_ids]
        incident_ids.extend(inserted_ids)
        
        # Update relationships
        primary_id = inserted_ids[0]
        duplicate_ids = inserted_ids[1:]
        
        # Link duplicates to primary
        await db.incidents.update_one(
            {"_id": ObjectId(primary_id)},
            {"$set": {"related_incidents": duplicate_ids}}
        )
        
        # Link primary to duplicates
        for dup_id in duplicate_ids:
            await db.incidents.update_one(
                {"_id": ObjectId(dup_id)},
                {"$set": {"related_incidents": [primary_id]}}
            )
    
    logger.info(f"Created {len(incident_ids)} Vietnamese duplicate incidents")
    return incident_ids


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
    parser.add_argument(
        "--seed-duplicates",
        action="store_true",
        help="Also seed Vietnamese duplicate incidents",
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

        # Seed duplicate incidents if requested
        duplicate_incident_ids = []
        if args.seed_duplicates:
            logger.info("=" * 60)
            logger.info("SEEDING VIETNAMESE DUPLICATE INCIDENTS")
            logger.info("=" * 60)
            # Get user IDs (including newly created technicians)
            user_ids = [
                str(user["_id"]) for user in await database.users.find({}).to_list(length=1000)
            ]
            # Get asset IDs
            asset_ids = [
                str(asset["_id"]) for asset in await database.assets.find({}).to_list(length=100)
            ]
            duplicate_incident_ids = await seed_vietnamese_duplicate_incidents(
                database,
                asset_ids=asset_ids if asset_ids else None,
                user_ids=user_ids if user_ids else None,
            )
            logger.info(f"Created {len(duplicate_incident_ids)} duplicate incidents")
            logger.info("=" * 60)

        # Final summary
        total_count = await database.users.count_documents(
            {"role": UserRole.TECHNICIAN.value}
        )
        logger.info("=" * 60)
        logger.info("TECHNICIAN SEEDING COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Total technicians in database: {total_count}")
        logger.info(f"Created in this run: {len(technician_ids)}")
        if args.seed_duplicates:
            logger.info(f"Duplicate incidents created: {len(duplicate_incident_ids)}")
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
