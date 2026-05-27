"""
Seed script for rescue demo data.

Creates:
  - 3 volunteer users (vol01, vol02, vol03)
  - 3 hazards (flood Q8 critical, landslide Hải Vân high, storm Sơn Trà critical)
  - For Flood Q8: EmergencyEvent + EOPPlan (with markdown) + 4 DispatchOrders

Usage:
  docker compose exec backend python -m app.scripts.seed_rescue_demo
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://mongo:27017")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "gis_db")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

NOW = datetime.utcnow()


# ── helpers ──────────────────────────────────────────────────────────────────


def oid() -> ObjectId:
    return ObjectId()


def new_doc(extra: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "_id": oid(),
        "created_at": NOW,
        "updated_at": NOW,
        **extra,
    }


# ── seed data ─────────────────────────────────────────────────────────────────

VOLUNTEER_USERS = [
    {"username": "vol01", "full_name": "Nguyễn Tình Nguyện 01"},
    {"username": "vol02", "full_name": "Trần Tình Nguyện 02"},
    {"username": "vol03", "full_name": "Lê Tình Nguyện 03"},
]

HAZARDS_SEED = [
    {
        "hazard_id": "SEED-FLOOD-Q8-001",
        "title": "Lũ lụt nghiêm trọng tại Quận 8",
        "event_type": "flood",
        "severity": "critical",
        "source": "manual",
        "district": "Quận 8",
        "ward": "Phường 5",
        "geometry": {"type": "Point", "coordinates": [106.6862, 10.7231]},
        "is_active": True,
        "detected_at": NOW - timedelta(hours=2),
        "expires_at": NOW + timedelta(hours=22),
    },
    {
        "hazard_id": "SEED-LAND-HAIVAN-001",
        "title": "Sạt lở đất khu vực đèo Hải Vân",
        "event_type": "landslide",
        "severity": "high",
        "source": "manual",
        "district": "Huyện Phú Lộc",
        "ward": "Đèo Hải Vân",
        "geometry": {"type": "Point", "coordinates": [107.9128, 16.1720]},
        "is_active": True,
        "detected_at": NOW - timedelta(hours=4),
        "expires_at": NOW + timedelta(hours=20),
    },
    {
        "hazard_id": "SEED-STORM-SONTRA-001",
        "title": "Bão cấp 8 đổ bộ bán đảo Sơn Trà",
        "event_type": "storm",
        "severity": "critical",
        "source": "manual",
        "district": "Quận Sơn Trà",
        "ward": "Phường Thọ Quang",
        "geometry": {"type": "Point", "coordinates": [108.2766, 16.1002]},
        "is_active": True,
        "detected_at": NOW - timedelta(hours=1),
        "expires_at": NOW + timedelta(hours=23),
    },
]

SAMPLE_MARKDOWN = """# Kế hoạch ứng phó khẩn cấp — Lũ lụt Quận 8

- **Loại sự cố:** Lũ lụt
- **Mức độ:** Nghiêm trọng (Critical)
- **Địa điểm:** Quận 8, Phường 5, TP.HCM

## Mục tiêu
- Bảo vệ tính mạng và tài sản người dân vùng ngập
- Sơ tán toàn bộ hộ gia đình trong vùng nguy hiểm trong 4 giờ
- Thiết lập 2 điểm tiếp nhận cứu trợ

## Hành động ưu tiên
1. Kích hoạt đội ứng phó tại Quận 8 và huy động 20 tình nguyện viên
2. Triển khai 4 xe tải nhẹ + 10 áo phao cho nhóm sơ tán
3. Thiết lập điểm tiếp nhận tại Trường THPT Nhà Bè và UBND Phường 5
4. Duy trì liên lạc 2 chiều với hiện trường mỗi 30 phút
5. Báo cáo tình hình về sở chỉ huy mỗi giờ

## Truyền thông
- Phát loa di động hướng dẫn sơ tán
- Cập nhật bản tin trên cổng thông tin mỗi giờ
- Hotline khẩn cấp: 114

## Phương án dự phòng
- Nếu đường chính ngập, chuyển hướng qua đường Nguyễn Văn Linh
- Sẵn sàng điều thêm xuồng máy từ đơn vị PCCC nếu cần thiết
"""


async def seed(db: Any) -> None:  # noqa: C901
    users_col = db["users"]
    hazards_col = db["hazard_layers"]
    events_col = db["emergency_events"]
    eop_col = db["eop_plans"]
    dispatch_col = db["dispatch_orders"]

    # ── 1. Volunteers ─────────────────────────────────────────────────────────
    logger.info("Seeding volunteer users...")
    vol_ids: List[ObjectId] = []
    for vdata in VOLUNTEER_USERS:
        existing = await users_col.find_one({"username": vdata["username"]})
        if existing:
            logger.info("  User %s already exists, skipping.", vdata["username"])
            vol_ids.append(existing["_id"])
            continue
        user_doc = new_doc(
            {
                "username": vdata["username"],
                "email": f"{vdata['username']}@demo.sosconn.vn",
                "full_name": vdata["full_name"],
                "hashed_password": pwd_context.hash("Demo@1234"),
                "role": "volunteer",
                "status": "active",
                "permissions": [],
                "metadata": {"seeded": True},
            }
        )
        result = await users_col.insert_one(user_doc)
        vol_ids.append(result.inserted_id)
        logger.info("  Created volunteer %s (id=%s)", vdata["username"], result.inserted_id)

    # ── 2. Hazards ────────────────────────────────────────────────────────────
    logger.info("Seeding hazards (24h)...")
    hazard_db_ids: List[ObjectId] = []
    for hdata in HAZARDS_SEED:
        existing = await hazards_col.find_one({"hazard_id": hdata["hazard_id"]})
        if existing:
            logger.info("  Hazard %s already exists, skipping.", hdata["hazard_id"])
            hazard_db_ids.append(existing["_id"])
            continue
        hazard_doc = new_doc(
            {
                **hdata,
                "metadata": {"seeded": True},
                "ingest_timestamp": NOW,
                "last_seen_at": NOW,
            }
        )
        result = await hazards_col.insert_one(hazard_doc)
        hazard_db_ids.append(result.inserted_id)
        logger.info("  Created hazard %s", hdata["hazard_id"])

    flood_hazard_db_id = hazard_db_ids[0] if hazard_db_ids else None

    # ── 3. EmergencyEvent for Flood Q8 ────────────────────────────────────────
    logger.info("Seeding EmergencyEvent for Flood Q8...")
    event_doc_id: ObjectId | None = None

    existing_event = await events_col.find_one({"metadata.hazard_id": "SEED-FLOOD-Q8-001"})
    if existing_event:
        logger.info("  Event already exists, skipping.")
        event_doc_id = existing_event["_id"]
    else:
        event_doc = new_doc(
            {
                "event_code": "EVT-SEED-FLOOD-Q8",
                "title": "Lũ lụt nghiêm trọng tại Quận 8 (Demo)",
                "description": "Sự kiện demo được tạo bởi seed script",
                "event_type": "flood",
                "severity": "critical",
                "status": "active",
                "source": "sosconn",
                "location": {
                    "geometry": {"type": "Point", "coordinates": [106.6862, 10.7231]},
                    "address": "Khu vực Phường 5",
                    "ward": "Phường 5",
                    "district": "Quận 8",
                    "city": "TP.HCM",
                },
                "started_at": NOW - timedelta(hours=2),
                "affected_asset_ids": [],
                "affected_area_km2": 2.5,
                "estimated_impact": {"families": 120, "population": 480},
                "instructions": [
                    "Gọi 114 nếu cần hỗ trợ khẩn cấp",
                    "Sơ tán ngay khỏi các khu vực trũng thấp",
                ],
                "tags": ["flood", "critical", "q8", "demo"],
                "metadata": {"hazard_id": "SEED-FLOOD-Q8-001", "seeded": True},
            }
        )
        result = await events_col.insert_one(event_doc)
        event_doc_id = result.inserted_id
        logger.info("  Created event id=%s", event_doc_id)

    # Update hazard with linked_event_id
    if flood_hazard_db_id and event_doc_id:
        await hazards_col.update_one(
            {"_id": flood_hazard_db_id},
            {
                "$set": {
                    "metadata.linked_event_id": str(event_doc_id),
                    "updated_at": NOW,
                }
            },
        )

    # ── 4. EOPPlan ────────────────────────────────────────────────────────────
    logger.info("Seeding EOPPlan for Flood Q8...")
    eop_doc_id: ObjectId | None = None

    existing_eop = await eop_col.find_one({"emergency_event_id": str(event_doc_id)})
    if existing_eop:
        logger.info("  EOP already exists, skipping.")
        eop_doc_id = existing_eop["_id"]
    else:
        eop_doc = new_doc(
            {
                "emergency_event_id": str(event_doc_id),
                "version": 1,
                "title": "EOP v1 — Lũ lụt Quận 8 (Demo)",
                "summary": "Kế hoạch ứng phó khẩn cấp demo cho sự kiện lũ lụt Quận 8",
                "objectives": [
                    "Bảo vệ tính mạng người dân",
                    "Sơ tán khu vực nguy hiểm trong 4 giờ",
                    "Thiết lập 2 điểm tiếp nhận cứu trợ",
                ],
                "operational_phases": ["Khởi động", "Sơ tán", "Cứu hộ", "Phục hồi"],
                "actions": [],
                "assignment_matrix": [],
                "evacuation_plan": ["Sơ tán qua đường Nguyễn Văn Linh", "Điểm tập kết tại Trường THPT Nhà Bè"],
                "fallback_plan": ["Điều thêm xuồng từ PCCC nếu đường ngập"],
                "communications_plan": ["Phát loa di động mỗi 30 phút", "Hotline 114"],
                "status": "approved",
                "markdown_body": SAMPLE_MARKDOWN,
                "review_notes": "Seeded for demo",
                "approved_by": "seed_script",
                "approved_at": NOW,
                "metadata": {"seeded": True},
            }
        )
        result = await eop_col.insert_one(eop_doc)
        eop_doc_id = result.inserted_id
        logger.info("  Created EOP id=%s", eop_doc_id)

    # Update hazard with linked_eop_plan_id
    if flood_hazard_db_id and eop_doc_id:
        await hazards_col.update_one(
            {"_id": flood_hazard_db_id},
            {
                "$set": {
                    "metadata.linked_eop_plan_id": str(eop_doc_id),
                    "updated_at": NOW,
                }
            },
        )

    # ── 5. DispatchOrders ────────────────────────────────────────────────────
    logger.info("Seeding DispatchOrders for Flood Q8...")
    existing_orders = await dispatch_col.count_documents(
        {"emergency_event_id": str(event_doc_id), "metadata.seeded": True}
    )
    if existing_orders >= 4:
        logger.info("  Dispatch orders already seeded, skipping.")
    else:
        vol01_id = str(vol_ids[0]) if len(vol_ids) > 0 else None
        vol02_id = str(vol_ids[1]) if len(vol_ids) > 1 else None

        orders_to_create = [
            # Pending, unassigned
            {
                "task_title": "Sơ tán hộ dân khu vực trũng thấp Phường 5",
                "task_description": "Ưu tiên người già, trẻ nhỏ, người tàn tật. Dùng xe tải nhẹ + áo phao.",
                "priority": "critical",
                "status": "pending",
                "assignments": [],
                "assigned_user_id": None,
                "target_location": {
                    "type": "Point",
                    "coordinates": [106.6862, 10.7231],
                    "address": "Phường 5, Quận 8",
                },
            },
            # Pending, unassigned
            {
                "task_title": "Thiết lập điểm tiếp nhận cứu trợ tại Trường THPT Nhà Bè",
                "task_description": "Lều bạt, bộ sơ cứu, nước uống. Sức chứa tối thiểu 200 người.",
                "priority": "high",
                "status": "pending",
                "assignments": [],
                "assigned_user_id": None,
                "target_location": {
                    "type": "Point",
                    "coordinates": [106.6900, 10.7200],
                    "address": "Trường THPT Nhà Bè",
                },
            },
            # Pending, assigned vol01
            {
                "task_title": "Kiểm tra & ghi nhận tình trạng hạ tầng (điện, nước, cầu đường)",
                "task_description": "Dùng bộ đàm, ghi nhận và báo về chỉ huy mỗi giờ.",
                "priority": "medium",
                "status": "pending",
                "assignments": [{"assigned_user_id": vol01_id, "role": "volunteer"}],
                "assigned_user_id": vol01_id,
                "target_location": None,
            },
            # Assigned vol02
            {
                "task_title": "Phát loa hướng dẫn & kiểm tra hộ đơn thân, người già",
                "task_description": "Tổ dân phố ảnh hưởng. Loa tay, pin dự phòng.",
                "priority": "medium",
                "status": "assigned",
                "assignments": [{"assigned_user_id": vol02_id, "role": "volunteer"}],
                "assigned_user_id": vol02_id,
                "target_location": None,
            },
        ]

        for odata in orders_to_create:
            order_doc = new_doc(
                {
                    "emergency_event_id": str(event_doc_id),
                    "eop_plan_id": str(eop_doc_id),
                    "eta_minutes": 45,
                    "assigned_by": "seed_script",
                    "metadata": {"seeded": True},
                    **odata,
                }
            )
            await dispatch_col.insert_one(order_doc)
        logger.info("  Created 4 dispatch orders.")

    # ── Summary ───────────────────────────────────────────────────────────────
    total_vols = await users_col.count_documents({"role": "volunteer"})
    total_hazards = await hazards_col.count_documents({"metadata.seeded": True})
    total_orders = await dispatch_col.count_documents({"emergency_event_id": str(event_doc_id)})
    logger.info(
        "\n✅ Seed complete!\n"
        "   Volunteers: %d total (role=volunteer)\n"
        "   Seeded hazards: %d\n"
        "   Event ID (Flood Q8): %s\n"
        "   EOP Plan ID: %s\n"
        "   Dispatch orders for event: %d",
        total_vols,
        total_hazards,
        event_doc_id,
        eop_doc_id,
        total_orders,
    )


async def main() -> None:
    logger.info("Connecting to MongoDB at %s (db=%s)...", MONGODB_URL, DATABASE_NAME)
    client: AsyncIOMotorClient = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    try:
        await seed(db)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
