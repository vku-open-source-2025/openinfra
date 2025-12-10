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
from bson import ObjectId
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
    ResolutionType,
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
from app.domain.models.iot_sensor import (
    SensorType,
    SensorStatus,
    ConnectionType,
)
from app.domain.models.alert import (
    AlertSeverity,
    AlertStatus,
    AlertSourceType,
)
from app.domain.models.report import (
    ReportType,
    ReportFormat,
    ReportStatus,
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


def generate_sensor_code(index: int) -> str:
    """Generate sensor code."""
    return f"SENS-{index:05d}"


def generate_alert_code(index: int) -> str:
    """Generate alert code."""
    year = datetime.now().year
    return f"ALT-{year}-{index:05d}"


def generate_report_code(index: int) -> str:
    """Generate report code."""
    year = datetime.now().year
    return f"RPT-{year}-{index:05d}"


# Sample locations (Da Nang, Vietnam coordinates) - covering major districts and areas
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
    {
        "lat": 16.0645,
        "lng": 108.1534,
        "district": "Lien Chieu",
        "ward": "Hoa Khanh Bac",
    },
]

# Sample feature types and codes for city asset management
FEATURE_TYPES = [
    # Traffic & Transportation
    {
        "feature_type": "traffic_light",
        "feature_code": "DGT",
        "category": "traffic",
        "description": "Traffic signal control system",
        "specifications": {
            "voltage": "220V",
            "led_type": "LED",
            "poles": "galvanized_steel",
        },
    },
    {
        "feature_type": "street_lamp",
        "feature_code": "DCS",
        "category": "lighting",
        "description": "Street lighting fixture",
        "specifications": {"wattage": "150W", "type": "LED", "height": "8m"},
    },
    {
        "feature_type": "traffic_sign",
        "feature_code": "BBG",
        "category": "traffic",
        "description": "Traffic regulatory and warning signs",
        "specifications": {"material": "aluminum", "reflective": "diamond_grade"},
    },
    {
        "feature_type": "street_sign",
        "feature_code": "BTD",
        "category": "traffic",
        "description": "Street name signs",
        "specifications": {"material": "aluminum", "size": "standard"},
    },
    {
        "feature_type": "bus_stop",
        "feature_code": "TXB",
        "category": "transportation",
        "description": "Public bus stop shelter",
        "specifications": {"capacity": "15_people", "shelter": "yes"},
    },
    # Infrastructure
    {
        "feature_type": "drain",
        "feature_code": "CTN",
        "category": "infrastructure",
        "description": "Storm water drainage system",
        "specifications": {"diameter": "600mm", "material": "concrete"},
    },
    {
        "feature_type": "manhole",
        "feature_code": "GTN",
        "category": "infrastructure",
        "description": "Sewer and drainage access point",
        "specifications": {"diameter": "600mm", "cover": "cast_iron"},
    },
    {
        "feature_type": "bridge",
        "feature_code": "CAU",
        "category": "infrastructure",
        "description": "Road bridge structure",
        "specifications": {"material": "reinforced_concrete", "lanes": "2"},
    },
    {
        "feature_type": "sidewalk",
        "feature_code": "VHS",
        "category": "infrastructure",
        "description": "Pedestrian walkway",
        "specifications": {"width": "2m", "material": "concrete_tiles"},
    },
    # Safety & Emergency
    {
        "feature_type": "fire_hydrant",
        "feature_code": "VCC",
        "category": "safety",
        "description": "Fire suppression water source",
        "specifications": {"type": "pillar", "outlet": "2.5_inch"},
    },
    {
        "feature_type": "guardrail",
        "feature_code": "LCA",
        "category": "safety",
        "description": "Road safety barrier",
        "specifications": {"material": "steel", "length": "20m"},
    },
    {
        "feature_type": "cctv_camera",
        "feature_code": "CAM",
        "category": "safety",
        "description": "Surveillance camera",
        "specifications": {"resolution": "4K", "type": "PTZ", "night_vision": "yes"},
    },
    # Public Facilities
    {
        "feature_type": "park_bench",
        "feature_code": "GDA",
        "category": "furniture",
        "description": "Public seating bench",
        "specifications": {"material": "wood_steel", "capacity": "3_people"},
    },
    {
        "feature_type": "waste_bin",
        "feature_code": "TRA",
        "category": "sanitation",
        "description": "Public waste container",
        "specifications": {"capacity": "120L", "type": "recycling"},
    },
    {
        "feature_type": "water_fountain",
        "feature_code": "NUO",
        "category": "facility",
        "description": "Public drinking water fountain",
        "specifications": {"type": "pedestal", "filter": "yes"},
    },
    {
        "feature_type": "public_toilet",
        "feature_code": "NVS",
        "category": "facility",
        "description": "Public restroom facility",
        "specifications": {"type": "standalone", "accessible": "yes"},
    },
    # Green Infrastructure
    {
        "feature_type": "tree",
        "feature_code": "CXA",
        "category": "greenery",
        "description": "Street or park tree",
        "specifications": {"species": "varies", "planting_date": "varies"},
    },
    {
        "feature_type": "flower_bed",
        "feature_code": "THO",
        "category": "greenery",
        "description": "Decorative flower planting area",
        "specifications": {"area": "10m2", "irrigation": "drip"},
    },
    # Utilities
    {
        "feature_type": "utility_pole",
        "feature_code": "COT",
        "category": "utility",
        "description": "Electrical or telecom pole",
        "specifications": {"height": "10m", "material": "concrete"},
    },
    {
        "feature_type": "transformer",
        "feature_code": "TBA",
        "category": "utility",
        "description": "Electrical transformer box",
        "specifications": {"capacity": "250kVA", "voltage": "22kV"},
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
    
    # Verify technicians were created
    technician_count = await db.users.count_documents({"role": "technician", "status": "active"})
    logger.info(f"Verified: {technician_count} active technicians in database")
    if technician_count == 0:
        logger.warning("WARNING: No active technicians found after seeding!")
        # List all technicians regardless of status
        all_techs = await db.users.find({"role": "technician"}).to_list(length=10)
        logger.warning(f"Found {len(all_techs)} technicians total (any status):")
        for tech in all_techs:
            logger.warning(f"  - {tech.get('username')}: status={tech.get('status')}, role={tech.get('role')}")
    
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

    # Street names in Da Nang
    street_names = [
        "Bach Dang",
        "Tran Phu",
        "Nguyen Van Linh",
        "Le Duan",
        "Ngo Quyen",
        "Phan Chau Trinh",
        "Hung Vuong",
        "Ly Thuong Kiet",
        "Hoang Dieu",
        "Dien Bien Phu",
        "Hai Phong",
        "Ong Ich Khiem",
        "Nguyen Tri Phuong",
        "Le Loi",
        "Quang Trung",
        "Nguyen Huu Tho",
        "Vo Nguyen Giap",
    ]

    for feature_info in FEATURE_TYPES:
        feature_count = count // len(FEATURE_TYPES)
        for i in range(feature_count):
            location = random.choice(SAMPLE_LOCATIONS)
            geometry = {
                "type": "Point",
                "coordinates": [location["lng"], location["lat"]],
            }

            # Add some variation to coordinates
            geometry["coordinates"][0] += random.uniform(-0.001, 0.001)
            geometry["coordinates"][1] += random.uniform(-0.001, 0.001)

            # Generate realistic asset name
            feature_name = feature_info["feature_type"].replace("_", " ").title()
            street = random.choice(street_names)
            asset_name = f"{feature_name} - {street} St."

            # Determine IoT capability based on asset type
            iot_capable_types = [
                "traffic_light",
                "street_lamp",
                "cctv_camera",
                "fire_hydrant",
                "transformer",
                "waste_bin",
            ]
            iot_enabled = feature_info["feature_type"] in iot_capable_types

            asset = {
                "asset_code": generate_asset_code(
                    feature_info["feature_code"], asset_index
                ),
                "name": asset_name,
                "feature_type": feature_info["feature_type"],
                "feature_code": feature_info["feature_code"],
                "category": feature_info["category"],
                "description": feature_info.get("description", ""),
                "geometry": geometry,
                "location": {
                    "district": location["district"],
                    "ward": location["ward"],
                    "address": f"{random.randint(1, 500)} {street}",
                },
                "specifications": feature_info.get("specifications", {}),
                "status": random.choice(list(AssetStatus)).value,
                "condition": random.choice(list(AssetCondition)).value,
                "lifecycle_stage": random.choice(list(LifecycleStage)).value,
                "installation_date": datetime.utcnow()
                - timedelta(days=random.randint(365, 3650)),
                "iot_enabled": iot_enabled and random.random() > 0.3,
                "public_info_visible": True,
                "created_by": random.choice(user_ids) if user_ids else None,
                "created_at": datetime.utcnow()
                - timedelta(days=random.randint(1, 730)),
                "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            }

            # Add maintenance schedule for critical assets
            if feature_info["category"] in ["traffic", "safety", "lighting"]:
                asset["maintenance_schedule"] = {
                    "frequency": random.choice(["monthly", "quarterly", "semi_annual"]),
                    "last_maintenance": datetime.utcnow()
                    - timedelta(days=random.randint(30, 180)),
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

    # Realistic incident scenarios for city infrastructure
    incident_scenarios = [
        # Traffic & Lighting
        {
            "title": "Traffic light not working",
            "category": IncidentCategory.MALFUNCTION,
            "description": "Traffic signal at intersection is not functioning properly. Red light stays on continuously.",
            "severity": IncidentSeverity.HIGH,
        },
        {
            "title": "Street lamp out",
            "category": IncidentCategory.MALFUNCTION,
            "description": "Street lighting is not working. Area is dark at night creating safety concern.",
            "severity": IncidentSeverity.MEDIUM,
        },
        {
            "title": "Traffic sign damaged",
            "category": IncidentCategory.DAMAGE,
            "description": "Traffic sign has been damaged and is not visible to drivers.",
            "severity": IncidentSeverity.MEDIUM,
        },
        {
            "title": "Traffic light showing wrong signal",
            "category": IncidentCategory.MALFUNCTION,
            "description": "Traffic light displaying green in multiple directions simultaneously.",
            "severity": IncidentSeverity.CRITICAL,
        },
        # Infrastructure
        {
            "title": "Blocked drainage system",
            "category": IncidentCategory.DAMAGE,
            "description": "Storm drain is clogged with debris causing water accumulation on road.",
            "severity": IncidentSeverity.MEDIUM,
        },
        {
            "title": "Manhole cover missing",
            "category": IncidentCategory.SAFETY_HAZARD,
            "description": "Manhole cover is missing creating dangerous hole in road.",
            "severity": IncidentSeverity.CRITICAL,
        },
        {
            "title": "Broken manhole cover",
            "category": IncidentCategory.DAMAGE,
            "description": "Manhole cover is cracked and broken, poses risk to vehicles and pedestrians.",
            "severity": IncidentSeverity.HIGH,
        },
        {
            "title": "Damaged sidewalk",
            "category": IncidentCategory.DAMAGE,
            "description": "Sidewalk tiles are broken and uneven, creating trip hazard.",
            "severity": IncidentSeverity.MEDIUM,
        },
        {
            "title": "Flooded street",
            "category": IncidentCategory.SAFETY_HAZARD,
            "description": "Street flooding due to drainage backup after heavy rain.",
            "severity": IncidentSeverity.HIGH,
        },
        # Safety
        {
            "title": "Damaged guardrail",
            "category": IncidentCategory.DAMAGE,
            "description": "Guardrail has been damaged, possibly from vehicle collision.",
            "severity": IncidentSeverity.HIGH,
        },
        {
            "title": "Fire hydrant leaking",
            "category": IncidentCategory.MALFUNCTION,
            "description": "Fire hydrant valve is leaking water continuously.",
            "severity": IncidentSeverity.MEDIUM,
        },
        {
            "title": "CCTV camera not working",
            "category": IncidentCategory.MALFUNCTION,
            "description": "Surveillance camera appears to be offline or damaged.",
            "severity": IncidentSeverity.LOW,
        },
        # Public Facilities
        {
            "title": "Broken park bench",
            "category": IncidentCategory.DAMAGE,
            "description": "Park bench is damaged and unsafe for use.",
            "severity": IncidentSeverity.LOW,
        },
        {
            "title": "Overflowing waste bin",
            "category": IncidentCategory.OTHER,
            "description": "Public waste bin is overflowing and needs immediate collection.",
            "severity": IncidentSeverity.MEDIUM,
        },
        {
            "title": "Vandalized public property",
            "category": IncidentCategory.VANDALISM,
            "description": "Public facility has been vandalized with graffiti and intentional damage.",
            "severity": IncidentSeverity.MEDIUM,
        },
        {
            "title": "Water fountain not working",
            "category": IncidentCategory.MALFUNCTION,
            "description": "Public drinking fountain has no water flow.",
            "severity": IncidentSeverity.LOW,
        },
        # Trees & Green spaces
        {
            "title": "Fallen tree blocking road",
            "category": IncidentCategory.SAFETY_HAZARD,
            "description": "Large tree has fallen and is blocking traffic.",
            "severity": IncidentSeverity.CRITICAL,
        },
        {
            "title": "Overgrown vegetation",
            "category": IncidentCategory.OTHER,
            "description": "Vegetation has overgrown and is obstructing traffic signs and visibility.",
            "severity": IncidentSeverity.MEDIUM,
        },
        {
            "title": "Damaged tree requiring removal",
            "category": IncidentCategory.SAFETY_HAZARD,
            "description": "Tree shows signs of disease or damage and poses falling risk.",
            "severity": IncidentSeverity.HIGH,
        },
    ]

    street_names = [
        "Bach Dang",
        "Tran Phu",
        "Nguyen Van Linh",
        "Le Duan",
        "Ngo Quyen",
        "Phan Chau Trinh",
        "Hung Vuong",
        "Ly Thuong Kiet",
        "Hoang Dieu",
        "Dien Bien Phu",
        "Hai Phong",
        "Ong Ich Khiem",
        "Nguyen Tri Phuong",
    ]

    for i in range(count):
        asset_id = (
            random.choice(asset_ids) if asset_ids and random.random() > 0.3 else None
        )

        location = random.choice(SAMPLE_LOCATIONS)
        geometry = {
            "type": "Point",
            "coordinates": [
                location["lng"] + random.uniform(-0.002, 0.002),
                location["lat"] + random.uniform(-0.002, 0.002),
            ],
        }

        status = random.choice(list(IncidentStatus))
        reported_at = datetime.utcnow() - timedelta(days=random.randint(0, 60))

        # Select random incident scenario
        scenario = random.choice(incident_scenarios)
        street = random.choice(street_names)

        incident = {
            "incident_number": generate_incident_number(incident_index),
            "asset_id": asset_id,
            "title": scenario["title"],
            "description": scenario["description"],
            "category": scenario["category"].value,
            "severity": scenario["severity"].value,
            "status": status.value,
            "location": {
                "geometry": geometry,
                "address": f"{random.randint(1, 500)} {street}",
                "description": f"Near {street} intersection with {random.choice(street_names)}",
                "district": location["district"],
                "ward": location["ward"],
            },
            "reported_by": random.choice(user_ids) if user_ids else None,
            "reporter_type": random.choice(list(ReporterType)).value,
            "reported_via": random.choice(
                ["web", "mobile", "qr_code", "phone", "hotline"]
            ),
            "reported_at": reported_at,
            "public_visible": True,
            "upvotes": random.randint(0, 50) if random.random() > 0.5 else 0,
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


async def seed_vietnamese_duplicate_incidents(
    db,
    asset_ids: Optional[List[str]] = None,
    user_ids: Optional[List[str]] = None,
) -> List[str]:
    """Seed Vietnamese duplicate incidents for testing duplicate display."""
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
    ]

    location = random.choice(SAMPLE_LOCATIONS)
    incident_ids = []
    incident_index = len(await db.incidents.find({}).to_list(length=1000)) + 1

    for group in duplicate_groups:
        # Create primary incident
        primary_asset_id = random.choice(asset_ids) if asset_ids else None
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
            "reported_by": random.choice(user_ids) if user_ids else None,
            "reporter_type": ReporterType.CITIZEN.value,
            "reported_via": "web",
            "reported_at": datetime.utcnow() - timedelta(days=random.randint(1, 7)),
            "assigned_to": random.choice(user_ids) if user_ids else None,
            "acknowledged_at": datetime.utcnow() - timedelta(days=random.randint(1, 6)),
            "acknowledged_by": random.choice(user_ids) if user_ids else None,
            "public_visible": True,
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 7)),
            "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 6)),
            "related_incidents": [],  # Will be populated after creating duplicates
        }
        incident_index += 1

        # Create duplicate incidents
        duplicate_incident_ids = []
        for dup_scenario in group["duplicates"]:
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
                "resolved_at": datetime.utcnow() - timedelta(days=random.randint(1, 5)),
                "resolved_by": random.choice(user_ids) if user_ids else None,
                "location": {
                    "geometry": dup_geometry,
                    "address": primary_incident["location"]["address"],
                    "description": primary_incident["location"]["description"],
                    "district": location["district"],
                    "ward": location["ward"],
                },
                "reported_by": random.choice(user_ids) if user_ids else None,
                "reporter_type": ReporterType.CITIZEN.value,
                "reported_via": random.choice(["web", "mobile"]),
                "reported_at": datetime.utcnow() - timedelta(days=random.randint(1, 6)),
                "public_visible": True,
                "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 6)),
                "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 5)),
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

    # Realistic maintenance tasks for city infrastructure
    maintenance_tasks = [
        # Preventive
        {
            "type": MaintenanceType.PREVENTIVE,
            "title": "Traffic light routine inspection",
            "description": "Quarterly inspection of traffic signal system, check bulbs, wiring, and timing controls.",
            "duration": 120,
            "priority": MaintenancePriority.MEDIUM,
        },
        {
            "type": MaintenanceType.PREVENTIVE,
            "title": "Street lamp maintenance",
            "description": "Replace LED bulbs and clean fixtures. Check electrical connections.",
            "duration": 60,
            "priority": MaintenancePriority.LOW,
        },
        {
            "type": MaintenanceType.PREVENTIVE,
            "title": "Drainage system cleaning",
            "description": "Clear debris and sediment from storm drains to prevent flooding.",
            "duration": 180,
            "priority": MaintenancePriority.MEDIUM,
        },
        {
            "type": MaintenanceType.PREVENTIVE,
            "title": "Fire hydrant testing",
            "description": "Test water pressure and flow. Lubricate valves and check for leaks.",
            "duration": 45,
            "priority": MaintenancePriority.HIGH,
        },
        {
            "type": MaintenanceType.PREVENTIVE,
            "title": "CCTV system check",
            "description": "Verify camera functionality, clean lenses, check recording systems.",
            "duration": 90,
            "priority": MaintenancePriority.MEDIUM,
        },
        # Corrective
        {
            "type": MaintenanceType.CORRECTIVE,
            "title": "Repair damaged traffic sign",
            "description": "Replace damaged or faded traffic sign with new sign.",
            "duration": 120,
            "priority": MaintenancePriority.HIGH,
        },
        {
            "type": MaintenanceType.CORRECTIVE,
            "title": "Fix broken street lamp",
            "description": "Replace malfunctioning street lamp fixture and repair electrical wiring.",
            "duration": 180,
            "priority": MaintenancePriority.MEDIUM,
        },
        {
            "type": MaintenanceType.CORRECTIVE,
            "title": "Replace manhole cover",
            "description": "Install new manhole cover to replace missing or damaged cover.",
            "duration": 90,
            "priority": MaintenancePriority.CRITICAL,
        },
        {
            "type": MaintenanceType.CORRECTIVE,
            "title": "Repair sidewalk damage",
            "description": "Fix broken or uneven sidewalk tiles. Replace damaged sections.",
            "duration": 240,
            "priority": MaintenancePriority.MEDIUM,
        },
        {
            "type": MaintenanceType.CORRECTIVE,
            "title": "Repair guardrail",
            "description": "Replace damaged sections of guardrail and reinforce mounting.",
            "duration": 300,
            "priority": MaintenancePriority.HIGH,
        },
        # Inspection (preventive maintenance)
        {
            "type": MaintenanceType.PREVENTIVE,
            "title": "Bridge structural inspection",
            "description": "Annual structural inspection of bridge components and safety features.",
            "duration": 480,
            "priority": MaintenancePriority.HIGH,
        },
        {
            "type": MaintenanceType.PREVENTIVE,
            "title": "Traffic infrastructure audit",
            "description": "Comprehensive inspection of traffic lights, signs, and road markings.",
            "duration": 360,
            "priority": MaintenancePriority.MEDIUM,
        },
        {
            "type": MaintenanceType.PREVENTIVE,
            "title": "Safety equipment check",
            "description": "Inspect fire hydrants, emergency call boxes, and safety barriers.",
            "duration": 240,
            "priority": MaintenancePriority.HIGH,
        },
        # Emergency
        {
            "type": MaintenanceType.EMERGENCY,
            "title": "Emergency pothole repair",
            "description": "Urgent repair of dangerous pothole causing safety hazard.",
            "duration": 120,
            "priority": MaintenancePriority.CRITICAL,
        },
        {
            "type": MaintenanceType.EMERGENCY,
            "title": "Emergency drainage clearing",
            "description": "Clear blocked drainage causing street flooding during rain.",
            "duration": 180,
            "priority": MaintenancePriority.CRITICAL,
        },
        {
            "type": MaintenanceType.EMERGENCY,
            "title": "Fallen tree removal",
            "description": "Emergency removal of fallen tree blocking roadway.",
            "duration": 240,
            "priority": MaintenancePriority.CRITICAL,
        },
    ]

    for i in range(count):
        asset_id = random.choice(asset_ids) if asset_ids else None
        status = random.choice(list(MaintenanceStatus))
        scheduled_date = datetime.utcnow() + timedelta(days=random.randint(-30, 30))

        # Select random maintenance task
        task = random.choice(maintenance_tasks)

        maintenance = {
            "work_order_number": generate_work_order_number(wo_index),
            "asset_id": asset_id,
            "type": task["type"].value,
            "priority": task["priority"].value,
            "title": task["title"],
            "description": task["description"],
            "status": status.value,
            "scheduled_date": scheduled_date,
            "estimated_duration": task["duration"],
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

    # Define budget categories with realistic allocations
    budget_categories = [
        {
            "category": BudgetCategory.OPERATIONS,
            "name": "Infrastructure Operations & Maintenance",
            "description": "Daily operations and routine maintenance of city infrastructure",
            "allocation_range": (500000000, 2000000000),  # 500M-2B VND
        },
        {
            "category": BudgetCategory.CAPITAL,
            "name": "Capital Infrastructure Projects",
            "description": "Major infrastructure construction and upgrade projects",
            "allocation_range": (2000000000, 5000000000),  # 2B-5B VND
        },
        {
            "category": BudgetCategory.MAINTENANCE,
            "name": "Preventive Maintenance Program",
            "description": "Scheduled preventive maintenance and asset care",
            "allocation_range": (300000000, 1000000000),  # 300M-1B VND
        },
        {
            "category": BudgetCategory.EMERGENCY,
            "name": "Emergency Response Fund",
            "description": "Emergency repairs and disaster response",
            "allocation_range": (200000000, 500000000),  # 200M-500M VND
        },
    ]

    for i in range(count):
        fiscal_year = current_year - (count - i - 1)
        start_date = datetime(fiscal_year, 1, 1)
        end_date = datetime(fiscal_year, 12, 31)

        # Select budget category
        budget_cat = budget_categories[i % len(budget_categories)]
        total_allocated = random.uniform(*budget_cat["allocation_range"])

        # Calculate spent amount based on time elapsed
        days_elapsed = (datetime.utcnow() - start_date).days
        days_total = (end_date - start_date).days
        progress = min(days_elapsed / days_total, 1.0) if days_total > 0 else 0
        spent_amount = total_allocated * progress * random.uniform(0.6, 0.9)

        budget = {
            "budget_code": generate_budget_code(
                fiscal_year, budget_cat["category"].value, budget_index
            ),
            "fiscal_year": fiscal_year,
            "period_type": BudgetPeriodType.ANNUAL.value,
            "start_date": start_date,
            "end_date": end_date,
            "name": f"{fiscal_year} - {budget_cat['name']}",
            "description": budget_cat["description"],
            "category": budget_cat["category"].value,
            "total_allocated": total_allocated,
            "spent_amount": spent_amount if fiscal_year <= current_year else 0,
            "remaining_amount": (
                total_allocated - spent_amount
                if fiscal_year <= current_year
                else total_allocated
            ),
            "currency": "VND",
            "status": (
                BudgetStatus.APPROVED.value
                if fiscal_year <= current_year
                else BudgetStatus.DRAFT.value
            ),
            "created_by": random.choice(user_ids) if user_ids else None,
            "created_at": start_date - timedelta(days=60),
            "updated_at": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
        }

        # Add department allocations
        budget["departments"] = [
            {
                "department": "Traffic & Transportation",
                "allocated_amount": total_allocated * 0.35,
                "spent_amount": spent_amount * 0.35 if spent_amount > 0 else 0,
                "remaining_amount": (total_allocated - spent_amount) * 0.35,
            },
            {
                "department": "Public Works",
                "allocated_amount": total_allocated * 0.30,
                "spent_amount": spent_amount * 0.30 if spent_amount > 0 else 0,
                "remaining_amount": (total_allocated - spent_amount) * 0.30,
            },
            {
                "department": "Parks & Recreation",
                "allocated_amount": total_allocated * 0.15,
                "spent_amount": spent_amount * 0.15 if spent_amount > 0 else 0,
                "remaining_amount": (total_allocated - spent_amount) * 0.15,
            },
            {
                "department": "Public Safety",
                "allocated_amount": total_allocated * 0.20,
                "spent_amount": spent_amount * 0.20 if spent_amount > 0 else 0,
                "remaining_amount": (total_allocated - spent_amount) * 0.20,
            },
        ]

        # Add breakdown
        budget["breakdown"] = [
            {
                "category": "labor",
                "allocated": total_allocated * 0.45,
                "spent": spent_amount * 0.45 if spent_amount > 0 else 0,
                "remaining": (total_allocated - spent_amount) * 0.45,
            },
            {
                "category": "materials",
                "allocated": total_allocated * 0.30,
                "spent": spent_amount * 0.30 if spent_amount > 0 else 0,
                "remaining": (total_allocated - spent_amount) * 0.30,
            },
            {
                "category": "equipment",
                "allocated": total_allocated * 0.15,
                "spent": spent_amount * 0.15 if spent_amount > 0 else 0,
                "remaining": (total_allocated - spent_amount) * 0.15,
            },
            {
                "category": "contractors",
                "allocated": total_allocated * 0.10,
                "spent": spent_amount * 0.10 if spent_amount > 0 else 0,
                "remaining": (total_allocated - spent_amount) * 0.10,
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

    # Realistic transaction descriptions
    transaction_types = [
        {
            "category": "labor",
            "descriptions": [
                "Field technician labor for routine maintenance",
                "Emergency repair crew overtime pay",
                "Contractor labor for infrastructure repairs",
                "Inspection team field work compensation",
            ],
            "amount_range": (500000, 5000000),
        },
        {
            "category": "materials",
            "descriptions": [
                "LED bulbs and lighting fixtures",
                "Traffic sign reflective materials",
                "Concrete and asphalt for road repairs",
                "Replacement parts for traffic signals",
                "Paint and marking materials for road lines",
                "Drainage pipes and covers",
            ],
            "amount_range": (1000000, 10000000),
        },
        {
            "category": "equipment",
            "descriptions": [
                "Power tools and maintenance equipment",
                "Safety gear and protective equipment",
                "Specialized inspection equipment",
                "Vehicle and machinery rental",
            ],
            "amount_range": (2000000, 15000000),
        },
        {
            "category": "contractors",
            "descriptions": [
                "Third-party contractor for major repairs",
                "Specialized electrical contractor services",
                "Tree removal and landscaping services",
                "Road resurfacing contractor payment",
            ],
            "amount_range": (5000000, 50000000),
        },
    ]

    for i in range(count):
        budget_id = random.choice(budget_ids) if budget_ids else None
        txn_type = random.choice(transaction_types)
        amount = random.uniform(*txn_type["amount_range"])

        transaction_date = datetime.utcnow() - timedelta(days=random.randint(0, 90))
        status = random.choice(["pending", "approved", "paid"])

        transaction = {
            "transaction_number": generate_transaction_number(txn_index),
            "budget_id": budget_id,
            "amount": amount,
            "currency": "VND",
            "transaction_date": transaction_date,
            "description": random.choice(txn_type["descriptions"]),
            "category": txn_type["category"],
            "maintenance_record_id": (
                random.choice(maintenance_ids)
                if maintenance_ids and random.random() > 0.4
                else None
            ),
            "asset_id": (
                random.choice(asset_ids)
                if asset_ids and random.random() > 0.2
                else None
            ),
            "vendor": f"Vendor {random.randint(1, 20)}",
            "status": status,
            "created_at": transaction_date - timedelta(days=random.randint(1, 7)),
            "updated_at": transaction_date,
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


async def seed_iot_sensors(
    db,
    count: int = 30,
    asset_ids: Optional[List[str]] = None,
    user_ids: Optional[List[str]] = None,
) -> List[str]:
    """Seed IoT sensors."""
    logger.info(f"Seeding {count} IoT sensors...")

    if not asset_ids:
        asset_ids = [
            str(asset["_id"]) for asset in await db.assets.find({}).to_list(length=100)
        ]
    if not user_ids:
        user_ids = [
            str(user["_id"]) for user in await db.users.find({}).to_list(length=100)
        ]

    # Filter assets that have iot_enabled=True
    iot_assets = await db.assets.find({"iot_enabled": True}).to_list(length=100)
    iot_asset_ids = [str(asset["_id"]) for asset in iot_assets]

    if not iot_asset_ids:
        logger.warning(
            "No IoT-enabled assets found. Creating sensors for random assets."
        )
        iot_asset_ids = asset_ids[: min(count, len(asset_ids))]

    sensors_data = []
    sensor_index = 1

    # Sensor configurations by type
    sensor_configs = {
        SensorType.TEMPERATURE: {
            "unit": "°C",
            "sample_rate": 300,  # 5 minutes
            "manufacturers": ["Sensirion", "Bosch", "Texas Instruments"],
            "models": ["SHT30", "BME280", "TMP102"],
            "thresholds": {
                "min_value": -10.0,
                "max_value": 60.0,
                "critical_min": -5.0,
                "critical_max": 55.0,
            },
        },
        SensorType.HUMIDITY: {
            "unit": "%",
            "sample_rate": 300,
            "manufacturers": ["Sensirion", "Honeywell", "Bosch"],
            "models": ["SHT30", "HIH6130", "BME280"],
            "thresholds": {
                "min_value": 0.0,
                "max_value": 100.0,
                "critical_min": 10.0,
                "critical_max": 90.0,
            },
        },
        SensorType.PRESSURE: {
            "unit": "kPa",
            "sample_rate": 600,  # 10 minutes
            "manufacturers": ["Bosch", "Honeywell", "TE Connectivity"],
            "models": ["BMP280", "MPX5700", "MS5611"],
            "thresholds": {
                "min_value": 80.0,
                "max_value": 120.0,
                "critical_min": 85.0,
                "critical_max": 115.0,
            },
        },
        SensorType.VIBRATION: {
            "unit": "Hz",
            "sample_rate": 60,  # 1 minute
            "manufacturers": ["Analog Devices", "STMicroelectronics", "Bosch"],
            "models": ["ADXL345", "LSM6DS3", "BMA250"],
            "thresholds": {
                "min_value": 0.0,
                "max_value": 100.0,
                "critical_min": 0.0,
                "critical_max": 80.0,
            },
        },
        SensorType.POWER: {
            "unit": "kW",
            "sample_rate": 60,
            "manufacturers": ["Schneider Electric", "ABB", "Siemens"],
            "models": ["PM8000", "CM4000", "SENTRON"],
            "thresholds": {
                "min_value": 0.0,
                "max_value": 50.0,
                "critical_min": 0.0,
                "critical_max": 45.0,
            },
        },
    }

    # Connection types with realistic IP/MAC patterns
    connection_configs = {
        ConnectionType.WIFI: {
            "ip_prefix": "192.168.1.",
            "mac_prefix": "00:1B:44:",
        },
        ConnectionType.LORA: {
            "ip_prefix": None,
            "mac_prefix": "AA:BB:CC:",
        },
        ConnectionType.CELLULAR: {
            "ip_prefix": None,
            "mac_prefix": "00:0A:95:",
        },
        ConnectionType.ZIGBEE: {
            "ip_prefix": None,
            "mac_prefix": "00:12:4B:",
        },
        ConnectionType.BLUETOOTH: {
            "ip_prefix": None,
            "mac_prefix": "00:1A:7D:",
        },
    }

    for i in range(count):
        asset_id = random.choice(iot_asset_ids) if iot_asset_ids else None
        sensor_type = random.choice(list(SensorType))

        config = sensor_configs.get(
            sensor_type,
            {
                "unit": "units",
                "sample_rate": 300,
                "manufacturers": ["Generic"],
                "models": ["Model-1"],
                "thresholds": {},
            },
        )

        connection_type = random.choice(list(ConnectionType))
        conn_config = connection_configs[connection_type]

        # Generate IP and MAC addresses
        ip_address = None
        mac_address = None
        if conn_config["ip_prefix"]:
            ip_address = f"{conn_config['ip_prefix']}{random.randint(100, 254)}"
        mac_address = f"{conn_config['mac_prefix']}{random.randint(10, 99):02X}:{random.randint(10, 99):02X}:{random.randint(10, 99):02X}"

        # Determine status based on installation date
        installed_days_ago = random.randint(1, 730)
        installed_at = datetime.utcnow() - timedelta(days=installed_days_ago)

        # Status: mostly online, some offline/maintenance
        status_weights = (
            [SensorStatus.ONLINE] * 7
            + [SensorStatus.OFFLINE] * 2
            + [SensorStatus.MAINTENANCE] * 1
        )
        status = random.choice(status_weights)

        # Last seen: recent for online, older for offline
        if status == SensorStatus.ONLINE:
            last_seen = datetime.utcnow() - timedelta(minutes=random.randint(1, 60))
        elif status == SensorStatus.MAINTENANCE:
            last_seen = datetime.utcnow() - timedelta(days=random.randint(1, 7))
        else:
            last_seen = datetime.utcnow() - timedelta(days=random.randint(1, 30))

        # Generate last reading
        base_value = {
            SensorType.TEMPERATURE: random.uniform(20.0, 35.0),
            SensorType.HUMIDITY: random.uniform(40.0, 80.0),
            SensorType.PRESSURE: random.uniform(95.0, 105.0),
            SensorType.VIBRATION: random.uniform(0.0, 50.0),
            SensorType.POWER: random.uniform(5.0, 30.0),
        }.get(sensor_type, random.uniform(0.0, 100.0))

        last_reading = {
            "value": base_value,
            "timestamp": last_seen,
            "status": "normal" if status == SensorStatus.ONLINE else "warning",
        }

        # Calibration dates
        calibration_date = installed_at + timedelta(days=random.randint(1, 30))
        calibration_due = calibration_date + timedelta(days=365)

        sensor = {
            "sensor_code": generate_sensor_code(sensor_index),
            "asset_id": asset_id,
            "sensor_type": sensor_type.value,
            "manufacturer": random.choice(config["manufacturers"]),
            "model": random.choice(config["models"]),
            "firmware_version": f"v{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "measurement_unit": config["unit"],
            "sample_rate": config["sample_rate"],
            "thresholds": config.get("thresholds", {}),
            "connection_type": connection_type.value,
            "ip_address": ip_address,
            "mac_address": mac_address,
            "gateway_id": f"GW-{random.randint(1, 10):03d}",
            "status": status.value,
            "last_seen": last_seen,
            "last_reading": last_reading,
            "calibration_date": calibration_date,
            "calibration_due": calibration_due,
            "calibration_factor": random.uniform(0.95, 1.05),
            "installed_at": installed_at,
            "installed_by": random.choice(user_ids) if user_ids else None,
            "location_description": f"Installed on asset {asset_id[:8]}...",
            "maintenance_schedule": random.choice(["monthly", "quarterly", "yearly"]),
            "last_maintenance": installed_at + timedelta(days=random.randint(30, 180)),
            "next_maintenance": datetime.utcnow()
            + timedelta(days=random.randint(1, 90)),
            "created_at": installed_at,
            "updated_at": last_seen,
            "created_by": random.choice(user_ids) if user_ids else None,
            "notes": f"Installed for monitoring {sensor_type.value}",
            "tags": [sensor_type.value, connection_type.value],
        }

        sensors_data.append(sensor)
        sensor_index += 1

    # Clear existing sensors
    await db.iot_sensors.delete_many({})

    # Insert sensors
    result = await db.iot_sensors.insert_many(sensors_data)
    sensor_ids = [str(id) for id in result.inserted_ids]

    logger.info(f"Created {len(sensor_ids)} IoT sensors")
    return sensor_ids


async def seed_alerts(
    db,
    count: int = 20,
    sensor_ids: Optional[List[str]] = None,
    asset_ids: Optional[List[str]] = None,
    incident_ids: Optional[List[str]] = None,
    maintenance_ids: Optional[List[str]] = None,
    user_ids: Optional[List[str]] = None,
) -> List[str]:
    """Seed alerts."""
    logger.info(f"Seeding {count} alerts...")

    if not sensor_ids:
        sensor_ids = [
            str(sensor["_id"])
            for sensor in await db.iot_sensors.find({}).to_list(length=100)
        ]
    if not asset_ids:
        asset_ids = [
            str(asset["_id"]) for asset in await db.assets.find({}).to_list(length=100)
        ]
    if not user_ids:
        user_ids = [
            str(user["_id"]) for user in await db.users.find({}).to_list(length=100)
        ]

    alerts_data = []
    alert_index = 1

    # Alert scenarios
    alert_scenarios = [
        {
            "source_type": AlertSourceType.SENSOR,
            "type": "threshold_exceeded",
            "severity": AlertSeverity.WARNING,
            "title": "Temperature threshold exceeded",
            "message": "Sensor reading exceeds configured maximum threshold",
            "condition": "greater_than",
        },
        {
            "source_type": AlertSourceType.SENSOR,
            "type": "threshold_exceeded",
            "severity": AlertSeverity.CRITICAL,
            "title": "Critical temperature reading",
            "message": "Temperature reading is critically high",
            "condition": "greater_than",
        },
        {
            "source_type": AlertSourceType.SENSOR,
            "type": "sensor_offline",
            "severity": AlertSeverity.WARNING,
            "title": "Sensor offline",
            "message": "Sensor has not reported data for extended period",
            "condition": None,
        },
        {
            "source_type": AlertSourceType.SYSTEM,
            "type": "maintenance_due",
            "severity": AlertSeverity.INFO,
            "title": "Maintenance due",
            "message": "Scheduled maintenance is due for this asset",
            "condition": None,
        },
        {
            "source_type": AlertSourceType.SENSOR,
            "type": "threshold_exceeded",
            "severity": AlertSeverity.WARNING,
            "title": "Power consumption high",
            "message": "Power consumption exceeds normal operating range",
            "condition": "greater_than",
        },
        {
            "source_type": AlertSourceType.SENSOR,
            "type": "vibration_anomaly",
            "severity": AlertSeverity.CRITICAL,
            "title": "Unusual vibration detected",
            "message": "Vibration sensor detected abnormal patterns",
            "condition": "greater_than",
        },
        {
            "source_type": AlertSourceType.SYSTEM,
            "type": "asset_condition_deteriorated",
            "severity": AlertSeverity.WARNING,
            "title": "Asset condition deteriorated",
            "message": "Asset condition has changed to poor status",
            "condition": None,
        },
        {
            "source_type": AlertSourceType.MANUAL,
            "type": "custom",
            "severity": AlertSeverity.INFO,
            "title": "Manual alert created",
            "message": "Alert created manually by administrator",
            "condition": None,
        },
    ]

    for i in range(count):
        scenario = random.choice(alert_scenarios)

        # Determine asset and sensor based on source type
        sensor_id = None
        asset_id = None

        if scenario["source_type"] == AlertSourceType.SENSOR and sensor_ids:
            sensor_id = random.choice(sensor_ids)
            # Get asset_id from sensor
            try:
                sensor_doc = await db.iot_sensors.find_one({"_id": ObjectId(sensor_id)})
                if sensor_doc:
                    asset_id = str(sensor_doc.get("asset_id"))
            except Exception:
                # If ObjectId conversion fails, just use a random asset
                asset_id = random.choice(asset_ids) if asset_ids else None
        elif asset_ids:
            asset_id = random.choice(asset_ids)

        # Status distribution
        status_weights = [
            AlertStatus.ACTIVE,
            AlertStatus.ACTIVE,
            AlertStatus.ACKNOWLEDGED,
            AlertStatus.RESOLVED,
            AlertStatus.DISMISSED,
        ]
        status = random.choice(status_weights)

        triggered_at = datetime.utcnow() - timedelta(days=random.randint(0, 30))

        # Generate trigger and threshold values for threshold alerts
        trigger_value = None
        threshold_value = None
        if scenario["type"] == "threshold_exceeded":
            threshold_value = random.uniform(50.0, 100.0)
            trigger_value = threshold_value + random.uniform(5.0, 20.0)

        alert = {
            "alert_code": generate_alert_code(alert_index),
            "source_type": scenario["source_type"].value,
            "sensor_id": sensor_id,
            "asset_id": asset_id,
            "type": scenario["type"],
            "severity": scenario["severity"].value,
            "title": scenario["title"],
            "message": scenario["message"],
            "trigger_value": trigger_value,
            "threshold_value": threshold_value,
            "condition": scenario["condition"],
            "status": status.value,
            "triggered_at": triggered_at,
            "created_at": triggered_at,
            "updated_at": triggered_at,
            "auto_created": scenario["source_type"] != AlertSourceType.MANUAL,
            "metadata": {
                "source": "seed_data",
                "scenario": scenario["type"],
            },
        }

        # Add acknowledgment/resolution details based on status
        if status in [
            AlertStatus.ACKNOWLEDGED,
            AlertStatus.RESOLVED,
            AlertStatus.DISMISSED,
        ]:
            alert["acknowledged_at"] = triggered_at + timedelta(
                hours=random.randint(1, 24)
            )
            alert["acknowledged_by"] = random.choice(user_ids) if user_ids else None

        if status in [AlertStatus.RESOLVED]:
            alert["resolved_at"] = triggered_at + timedelta(days=random.randint(1, 7))
            alert["resolved_by"] = alert["acknowledged_by"]
            alert["resolution_notes"] = "Alert resolved successfully."

        # Link to incidents/maintenance if resolved
        if status == AlertStatus.RESOLVED and random.random() > 0.5:
            if incident_ids and random.random() > 0.5:
                alert["incident_created"] = True
                alert["incident_id"] = random.choice(incident_ids)
            elif maintenance_ids:
                alert["maintenance_created"] = True
                alert["maintenance_id"] = random.choice(maintenance_ids)

        # Add notifications
        if random.random() > 0.3:
            alert["notifications_sent"] = [
                {
                    "recipient_id": random.choice(user_ids) if user_ids else None,
                    "sent_at": triggered_at + timedelta(minutes=random.randint(1, 60)),
                    "method": random.choice(["email", "push", "sms"]),
                    "status": random.choice(["sent", "delivered"]),
                }
            ]

        alerts_data.append(alert)
        alert_index += 1

    # Clear existing alerts
    await db.alerts.delete_many({})

    # Insert alerts
    result = await db.alerts.insert_many(alerts_data)
    alert_ids = [str(id) for id in result.inserted_ids]

    logger.info(f"Created {len(alert_ids)} alerts")
    return alert_ids


async def seed_reports(
    db,
    count: int = 10,
    user_ids: Optional[List[str]] = None,
) -> List[str]:
    """Seed reports."""
    logger.info(f"Seeding {count} reports...")

    if not user_ids:
        user_ids = [
            str(user["_id"]) for user in await db.users.find({}).to_list(length=100)
        ]

    reports_data = []
    report_index = 1

    # Report templates
    report_templates = [
        {
            "type": ReportType.MAINTENANCE_SUMMARY,
            "name": "Monthly Maintenance Summary",
            "description": "Summary of all maintenance activities for the month",
            "format": ReportFormat.PDF,
            "parameters": {
                "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "status": ["completed", "in_progress"],
            },
        },
        {
            "type": ReportType.ASSET_INVENTORY,
            "name": "Asset Inventory Report",
            "description": "Complete inventory of all city assets",
            "format": ReportFormat.EXCEL,
            "parameters": {
                "include_inactive": False,
                "group_by": "category",
            },
        },
        {
            "type": ReportType.INCIDENT_REPORT,
            "name": "Weekly Incident Report",
            "description": "Summary of incidents reported this week",
            "format": ReportFormat.PDF,
            "parameters": {
                "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "severity": ["high", "critical"],
            },
        },
        {
            "type": ReportType.BUDGET_UTILIZATION,
            "name": "Quarterly Budget Utilization",
            "description": "Budget spending and utilization analysis",
            "format": ReportFormat.EXCEL,
            "parameters": {
                "fiscal_year": datetime.now().year,
                "quarter": (datetime.now().month - 1) // 3 + 1,
            },
        },
        {
            "type": ReportType.IOT_SENSOR_DATA,
            "name": "Sensor Data Analysis",
            "description": "Analysis of IoT sensor readings and trends",
            "format": ReportFormat.PDF,
            "parameters": {
                "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "sensor_types": ["temperature", "humidity"],
            },
        },
    ]

    for i in range(count):
        template = report_templates[i % len(report_templates)]

        # Status distribution
        status_weights = [
            ReportStatus.COMPLETED,
            ReportStatus.COMPLETED,
            ReportStatus.PENDING,
            ReportStatus.GENERATING,
            ReportStatus.FAILED,
        ]
        status = random.choice(status_weights)

        created_at = datetime.utcnow() - timedelta(days=random.randint(0, 60))
        generated_at = None
        file_url = None
        file_size = None
        error_message = None

        if status == ReportStatus.COMPLETED:
            generated_at = created_at + timedelta(hours=random.randint(1, 24))
            file_url = f"/reports/{generate_report_code(report_index)}.{template['format'].value}"
            file_size = random.randint(100000, 5000000)  # 100KB - 5MB
        elif status == ReportStatus.FAILED:
            error_message = "Failed to generate report: Timeout error"

        # Scheduling
        scheduled = random.random() > 0.7
        schedule_pattern = None
        next_run = None
        if scheduled:
            schedule_pattern = random.choice(
                ["0 0 * * *", "0 0 * * 1", "0 0 1 * *"]
            )  # Daily, Weekly, Monthly
            next_run = datetime.utcnow() + timedelta(days=random.randint(1, 30))

        # Expiration
        expires_at = None
        if status == ReportStatus.COMPLETED:
            expires_at = datetime.utcnow() + timedelta(days=random.randint(30, 365))

        report = {
            "report_code": generate_report_code(report_index),
            "type": template["type"].value,
            "name": f"{template['name']} - {report_index}",
            "description": template["description"],
            "parameters": template["parameters"],
            "format": template["format"].value,
            "file_url": file_url,
            "file_size": file_size,
            "status": status.value,
            "generated_at": generated_at,
            "error_message": error_message,
            "scheduled": scheduled,
            "schedule_pattern": schedule_pattern,
            "next_run": next_run,
            "recipients": (
                [random.choice(user_ids) for _ in range(random.randint(1, 3))]
                if user_ids
                else []
            ),
            "expires_at": expires_at,
            "created_at": created_at,
            "created_by": random.choice(user_ids) if user_ids else None,
            "metadata": {
                "template": template["type"].value,
                "generated_by": "seed_script",
            },
        }

        reports_data.append(report)
        report_index += 1

    # Clear existing reports
    await db.reports.delete_many({})

    # Insert reports
    result = await db.reports.insert_many(reports_data)
    report_ids = [str(id) for id in result.inserted_ids]

    logger.info(f"Created {len(report_ids)} reports")
    return report_ids


async def seed_database(
    users: int = 20,
    assets: int = 50,
    incidents: int = 30,
    maintenance: int = 25,
    budgets: int = 5,
    transactions: int = 20,
    iot_sensors: int = 30,
    alerts: int = 20,
    reports: int = 10,
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
            try:
                await db.users.delete_many({})
                await db.assets.delete_many({})
                await db.incidents.delete_many({})
                await db.maintenance_records.delete_many({})
                await db.budgets.delete_many({})
                await db.budget_transactions.delete_many({})
                await db.iot_sensors.delete_many({})
                await db.alerts.delete_many({})
                await db.reports.delete_many({})
            except Exception as e:
                # Handle MongoDB errors gracefully (e.g., time-series collection restrictions)
                logger.warning(f"Some collections could not be cleared: {e}")
                logger.info("Continuing with seeding...")

        # Seed in order (respecting dependencies)
        user_ids = await seed_users(db, count=users)
        asset_ids = await seed_assets(db, count=assets, user_ids=user_ids)
        incident_ids = await seed_incidents(
            db, count=incidents, asset_ids=asset_ids, user_ids=user_ids
        )
        # Add Vietnamese duplicate incidents for testing
        vietnamese_duplicate_ids = await seed_vietnamese_duplicate_incidents(
            db, asset_ids=asset_ids, user_ids=user_ids
        )
        incident_ids.extend(vietnamese_duplicate_ids)
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
        sensor_ids = await seed_iot_sensors(
            db, count=iot_sensors, asset_ids=asset_ids, user_ids=user_ids
        )
        await seed_alerts(
            db,
            count=alerts,
            sensor_ids=sensor_ids,
            asset_ids=asset_ids,
            incident_ids=incident_ids,
            maintenance_ids=maintenance_ids,
            user_ids=user_ids,
        )
        await seed_reports(db, count=reports, user_ids=user_ids)

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
        logger.info(f"  - IoT Sensors: {await db.iot_sensors.count_documents({})}")
        logger.info(f"  - Alerts: {await db.alerts.count_documents({})}")
        logger.info(f"  - Reports: {await db.reports.count_documents({})}")
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
        "--iot-sensors",
        type=int,
        default=30,
        dest="iot_sensors",
        help="Number of IoT sensors to create",
    )
    parser.add_argument(
        "--alerts",
        type=int,
        default=20,
        help="Number of alerts to create",
    )
    parser.add_argument(
        "--reports",
        type=int,
        default=10,
        help="Number of reports to create",
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
        iot_sensors=args.iot_sensors,
        alerts=args.alerts,
        reports=args.reports,
        clear_existing=args.clear,
    )


if __name__ == "__main__":
    asyncio.run(main())
