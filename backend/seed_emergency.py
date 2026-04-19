"""Seed script for Emergency Command Center dummy data."""
import asyncio
from datetime import datetime, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://mongo:27017"
DB_NAME = "openinfra"

now = datetime.utcnow()

# Fixed IDs for cross-referencing
EVENT_IDS = [ObjectId() for _ in range(4)]
RESOURCE_IDS = [ObjectId() for _ in range(8)]
EOP_IDS = [ObjectId() for _ in range(3)]
DISPATCH_IDS = [ObjectId() for _ in range(6)]
HAZARD_IDS = [ObjectId() for _ in range(5)]
SITREP_IDS = [ObjectId() for _ in range(3)]
AAR_IDS = [ObjectId() for _ in range(2)]


async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # ── Emergency Events ──────────────────────────────────────
    events = [
        {
            "_id": EVENT_IDS[0],
            "event_code": "EV-2026-001",
            "title": "Ngập lụt nghiêm trọng quận 8",
            "description": "Mưa lớn kéo dài gây ngập úng tại nhiều tuyến đường, ảnh hưởng 2.000 hộ dân.",
            "event_type": "flood",
            "severity": "critical",
            "status": "active",
            "source": "iot",
            "location": {"address": "Quận 8, TP.HCM", "district": "Quận 8", "city": "TP.HCM"},
            "affected_area_km2": 3.5,
            "instructions": ["Sơ tán dân cư vùng trũng", "Bơm thoát nước khẩn cấp"],
            "tags": ["flood", "urgent"],
            "started_at": now - timedelta(hours=3),
            "created_at": now - timedelta(hours=3),
            "updated_at": now - timedelta(minutes=30),
        },
        {
            "_id": EVENT_IDS[1],
            "event_code": "EV-2026-002",
            "title": "Cháy kho hàng khu công nghiệp Bình Dương",
            "description": "Đám cháy bùng phát tại kho hàng, nguy cơ lan sang khu dân cư.",
            "event_type": "fire",
            "severity": "high",
            "status": "contained",
            "source": "manual",
            "location": {"address": "KCN Sóng Thần, Bình Dương", "district": "Dĩ An", "city": "Bình Dương"},
            "affected_area_km2": 0.5,
            "instructions": ["Cách ly khu vực 200m", "Hỗ trợ PCCC"],
            "tags": ["fire", "industrial"],
            "started_at": now - timedelta(hours=6),
            "created_at": now - timedelta(hours=6),
            "updated_at": now - timedelta(hours=1),
        },
        {
            "_id": EVENT_IDS[2],
            "event_code": "EV-2026-003",
            "title": "Bão số 3 đổ bộ vào bờ biển miền Trung",
            "description": "Bão mạnh cấp 10 dự kiến đổ bộ, cần sơ tán khẩn.",
            "event_type": "storm",
            "severity": "critical",
            "status": "monitoring",
            "source": "forecast",
            "location": {"address": "Bờ biển Đà Nẵng", "district": "Sơn Trà", "city": "Đà Nẵng"},
            "affected_area_km2": 120.0,
            "instructions": ["Sơ tán dân ven biển", "Gia cố nhà cửa", "Chuẩn bị lương thực 7 ngày"],
            "tags": ["storm", "evacuation"],
            "started_at": now + timedelta(hours=12),
            "created_at": now - timedelta(hours=12),
            "updated_at": now - timedelta(hours=1),
        },
        {
            "_id": EVENT_IDS[3],
            "event_code": "EV-2026-004",
            "title": "Sự cố mất điện diện rộng Hà Nội",
            "description": "Trạm biến áp 110kV sự cố, 50.000 hộ dân mất điện.",
            "event_type": "outage",
            "severity": "high",
            "status": "resolved",
            "source": "iot",
            "location": {"address": "Quận Hai Bà Trưng, Hà Nội", "district": "Hai Bà Trưng", "city": "Hà Nội"},
            "instructions": ["Ưu tiên bệnh viện và trường học"],
            "tags": ["outage", "electrical"],
            "started_at": now - timedelta(hours=24),
            "ended_at": now - timedelta(hours=2),
            "created_at": now - timedelta(hours=24),
            "updated_at": now - timedelta(hours=2),
        },
    ]

    # ── Hazard Layers ─────────────────────────────────────────
    hazards = [
        {
            "_id": HAZARD_IDS[0],
            "hazard_id": "HAZ-2026-001",
            "title": "Vùng ngập lụt Q8 – mức độ nguy hiểm cao",
            "description": "Nước ngập 0.5–1.2m tại các tuyến đường chính.",
            "event_type": "flood",
            "severity": "critical",
            "source": "iot",
            "geometry": {"type": "Point", "coordinates": [106.6297, 10.7344]},
            "affected_polygon": {
                "type": "Polygon",
                "coordinates": [[[106.62, 10.73], [106.64, 10.73], [106.64, 10.75], [106.62, 10.75], [106.62, 10.73]]]
            },
            "intensity_level": 8.5,
            "forecast_confidence": 0.92,
            "affected_population": 8500,
            "district": "Quận 8",
            "ward": "Phường 1",
            "detected_at": now - timedelta(hours=3),
            "expires_at": now + timedelta(hours=24),
            "is_active": True,
            "status": "active",
            "created_at": now - timedelta(hours=3),
            "updated_at": now - timedelta(minutes=30),
        },
        {
            "_id": HAZARD_IDS[1],
            "hazard_id": "HAZ-2026-002",
            "title": "Điểm cháy KCN Bình Dương",
            "description": "Nhiệt độ cao, khói lan rộng 500m.",
            "event_type": "fire",
            "severity": "high",
            "source": "manual",
            "geometry": {"type": "Point", "coordinates": [106.7747, 10.9031]},
            "intensity_level": 7.0,
            "forecast_confidence": 0.85,
            "affected_population": 1200,
            "district": "Dĩ An",
            "detected_at": now - timedelta(hours=6),
            "expires_at": now + timedelta(hours=6),
            "is_active": True,
            "status": "active",
            "created_at": now - timedelta(hours=6),
            "updated_at": now - timedelta(hours=1),
        },
        {
            "_id": HAZARD_IDS[2],
            "hazard_id": "HAZ-2026-003",
            "title": "Vùng ảnh hưởng bão số 3 – ven biển Đà Nẵng",
            "event_type": "storm",
            "severity": "critical",
            "source": "nchmf",
            "geometry": {"type": "Point", "coordinates": [108.2022, 16.0544]},
            "intensity_level": 10.0,
            "forecast_confidence": 0.78,
            "affected_population": 45000,
            "district": "Sơn Trà",
            "detected_at": now - timedelta(hours=8),
            "expires_at": now + timedelta(hours=36),
            "is_active": True,
            "status": "active",
            "created_at": now - timedelta(hours=8),
            "updated_at": now - timedelta(hours=2),
        },
        {
            "_id": HAZARD_IDS[3],
            "hazard_id": "HAZ-2026-004",
            "title": "Ô nhiễm không khí khu vực nhà máy thép",
            "event_type": "pollution",
            "severity": "medium",
            "source": "iot",
            "geometry": {"type": "Point", "coordinates": [107.0, 11.0]},
            "intensity_level": 4.5,
            "forecast_confidence": 0.7,
            "affected_population": 3000,
            "district": "Tân Uyên",
            "detected_at": now - timedelta(hours=10),
            "expires_at": now + timedelta(hours=12),
            "is_active": True,
            "status": "active",
            "created_at": now - timedelta(hours=10),
            "updated_at": now - timedelta(hours=3),
        },
        {
            "_id": HAZARD_IDS[4],
            "hazard_id": "HAZ-2026-005",
            "title": "Sạt lở đất đèo Hải Vân",
            "event_type": "landslide",
            "severity": "high",
            "source": "manual",
            "geometry": {"type": "Point", "coordinates": [108.1175, 16.1731]},
            "intensity_level": 6.0,
            "forecast_confidence": 0.88,
            "affected_population": 500,
            "district": "Liên Chiểu",
            "detected_at": now - timedelta(hours=2),
            "expires_at": now + timedelta(hours=48),
            "is_active": True,
            "status": "active",
            "created_at": now - timedelta(hours=2),
            "updated_at": now - timedelta(minutes=45),
        },
    ]

    # ── Resource Units ────────────────────────────────────────
    resources = [
        {"_id": RESOURCE_IDS[0], "resource_code": "RES-001", "name": "Xe bơm nước PCCC Q8", "resource_type": "vehicle", "status": "deployed", "capacity": 5000, "capacity_unit": "liter", "district": "Quận 8", "skills": ["firefighting", "flood"], "contact_phone": "0901234001", "created_at": now - timedelta(days=30), "updated_at": now - timedelta(hours=2)},
        {"_id": RESOURCE_IDS[1], "resource_code": "RES-002", "name": "Đội cứu nạn 15 người – Q8", "resource_type": "personnel", "status": "deployed", "capacity": 15, "capacity_unit": "người", "district": "Quận 8", "skills": ["rescue", "first_aid", "flood"], "contact_phone": "0901234002", "created_at": now - timedelta(days=30), "updated_at": now - timedelta(hours=1)},
        {"_id": RESOURCE_IDS[2], "resource_code": "RES-003", "name": "Máy bơm di động 3000L/h", "resource_type": "rescue_equipment", "status": "available", "capacity": 3000, "capacity_unit": "L/h", "district": "Quận 7", "skills": ["flood"], "created_at": now - timedelta(days=30), "updated_at": now},
        {"_id": RESOURCE_IDS[3], "resource_code": "RES-004", "name": "Xe cứu thương Bình Dương", "resource_type": "vehicle", "status": "deployed", "capacity": 4, "capacity_unit": "người", "district": "Dĩ An", "skills": ["medical", "emergency_transport"], "contact_phone": "0901234004", "created_at": now - timedelta(days=30), "updated_at": now - timedelta(hours=3)},
        {"_id": RESOURCE_IDS[4], "resource_code": "RES-005", "name": "Kho thuốc y tế dự phòng", "resource_type": "medical_supply", "status": "available", "capacity": 500, "capacity_unit": "kg", "district": "Quận 1", "skills": [], "created_at": now - timedelta(days=30), "updated_at": now},
        {"_id": RESOURCE_IDS[5], "resource_code": "RES-006", "name": "Nhà tạm lánh Đà Nẵng 200 chỗ", "resource_type": "shelter", "status": "standby", "capacity": 200, "capacity_unit": "người", "district": "Sơn Trà", "skills": [], "contact_phone": "0901234006", "created_at": now - timedelta(days=30), "updated_at": now - timedelta(hours=5)},
        {"_id": RESOURCE_IDS[6], "resource_code": "RES-007", "name": "Máy phát điện 100kVA", "resource_type": "rescue_equipment", "status": "available", "capacity": 100, "capacity_unit": "kVA", "district": "Hai Bà Trưng", "skills": ["electrical"], "created_at": now - timedelta(days=30), "updated_at": now},
        {"_id": RESOURCE_IDS[7], "resource_code": "RES-008", "name": "Đội PCCC 20 người – Bình Dương", "resource_type": "personnel", "status": "deployed", "capacity": 20, "capacity_unit": "người", "district": "Dĩ An", "skills": ["firefighting"], "contact_phone": "0901234008", "created_at": now - timedelta(days=30), "updated_at": now - timedelta(hours=4)},
    ]

    # ── EOP Plans ─────────────────────────────────────────────
    eops = [
        {
            "_id": EOP_IDS[0],
            "emergency_event_id": str(EVENT_IDS[0]),
            "version": 1,
            "title": "EOP: Ứng phó ngập lụt Quận 8 – v1",
            "summary": "Kế hoạch sơ tán và bơm thoát nước khẩn cấp cho khu vực Q8.",
            "objectives": ["Sơ tán 2.000 hộ dân", "Giảm mực nước trong 12h"],
            "operational_phases": ["Ứng phó tức thời", "Hỗ trợ kéo dài", "Phục hồi"],
            "actions": [
                {"action_id": "A1", "title": "Huy động xe bơm nước", "phase": "response", "priority": "critical", "owner_role": "PCCC", "estimated_minutes": 30},
                {"action_id": "A2", "title": "Sơ tán dân khu vực ngập", "phase": "response", "priority": "critical", "owner_role": "Dân phòng", "estimated_minutes": 60},
                {"action_id": "A3", "title": "Cấp phát lương thực khẩn cấp", "phase": "support", "priority": "high", "owner_role": "Hội chữ thập đỏ", "estimated_minutes": 120},
            ],
            "evacuation_plan": ["Tuyến sơ tán: Đường Phạm Thế Hiển → Trường tiểu học P3"],
            "fallback_plan": ["Nếu bơm hỏng: huy động máy bơm Q7"],
            "communications_plan": ["Loa phát thanh phường", "SMS khẩn cấp"],
            "status": "approved",
            "approved_by": "admin",
            "approved_at": now - timedelta(hours=2),
            "created_at": now - timedelta(hours=3),
            "updated_at": now - timedelta(hours=2),
        },
        {
            "_id": EOP_IDS[1],
            "emergency_event_id": str(EVENT_IDS[0]),
            "version": 2,
            "title": "EOP: Ứng phó ngập lụt Quận 8 – v2 (AI draft)",
            "summary": "Phiên bản cập nhật với dự báo mưa 6h tới.",
            "objectives": ["Dự phòng mực nước tăng thêm 20cm"],
            "operational_phases": ["Giám sát mở rộng", "Sơ tán bổ sung"],
            "actions": [
                {"action_id": "B1", "title": "Tăng cường giám sát IoT 15 phút/lần", "phase": "monitoring", "priority": "medium", "owner_role": "Kỹ thuật", "estimated_minutes": 15},
            ],
            "status": "draft",
            "created_at": now - timedelta(hours=1),
            "updated_at": now - timedelta(hours=1),
        },
        {
            "_id": EOP_IDS[2],
            "emergency_event_id": str(EVENT_IDS[2]),
            "version": 1,
            "title": "EOP: Ứng phó bão số 3 – Đà Nẵng",
            "summary": "Kế hoạch sơ tán và gia cố trước khi bão đổ bộ.",
            "objectives": ["Sơ tán 45.000 người ven biển trong 10h"],
            "operational_phases": ["Chuẩn bị", "Sơ tán", "Trú ẩn"],
            "actions": [
                {"action_id": "C1", "title": "Triển khai nhà tạm lánh", "phase": "preparation", "priority": "critical", "owner_role": "Ban chỉ huy bão", "estimated_minutes": 180},
                {"action_id": "C2", "title": "Sơ tán dân bằng xe buýt", "phase": "evacuation", "priority": "critical", "owner_role": "Giao thông", "estimated_minutes": 360},
            ],
            "status": "published",
            "approved_by": "director",
            "published_by": "director",
            "published_at": now - timedelta(hours=4),
            "created_at": now - timedelta(hours=8),
            "updated_at": now - timedelta(hours=4),
        },
    ]

    # ── Dispatch Orders ───────────────────────────────────────
    dispatches = [
        {"_id": DISPATCH_IDS[0], "emergency_event_id": str(EVENT_IDS[0]), "eop_plan_id": str(EOP_IDS[0]), "task_title": "Triển khai xe bơm Q8", "task_description": "Bơm thoát nước tuyến đường Phạm Thế Hiển", "priority": "critical", "status": "on_scene", "eta_minutes": 10, "assignments": [{"resource_unit_id": str(RESOURCE_IDS[0]), "role": "Xe bơm chính", "quantity": 1}], "started_at": now - timedelta(hours=2), "created_at": now - timedelta(hours=2), "updated_at": now - timedelta(minutes=20)},
        {"_id": DISPATCH_IDS[1], "emergency_event_id": str(EVENT_IDS[0]), "eop_plan_id": str(EOP_IDS[0]), "task_title": "Sơ tán hộ dân vùng ngập", "task_description": "Sơ tán 200 hộ dân ưu tiên người già trẻ em", "priority": "critical", "status": "in_transit", "eta_minutes": 45, "assignments": [{"resource_unit_id": str(RESOURCE_IDS[1]), "role": "Đội cứu nạn", "quantity": 15}], "started_at": now - timedelta(hours=1), "created_at": now - timedelta(hours=1, minutes=30), "updated_at": now - timedelta(minutes=15)},
        {"_id": DISPATCH_IDS[2], "emergency_event_id": str(EVENT_IDS[1]), "task_title": "Dập lửa kho hàng Bình Dương", "priority": "high", "status": "on_scene", "eta_minutes": 0, "assignments": [{"resource_unit_id": str(RESOURCE_IDS[7]), "role": "PCCC chính", "quantity": 20}], "started_at": now - timedelta(hours=5), "created_at": now - timedelta(hours=5), "updated_at": now - timedelta(hours=1)},
        {"_id": DISPATCH_IDS[3], "emergency_event_id": str(EVENT_IDS[1]), "task_title": "Cấp cứu nạn nhân bỏng", "priority": "critical", "status": "completed", "eta_minutes": 0, "assignments": [{"resource_unit_id": str(RESOURCE_IDS[3]), "role": "Xe cấp cứu", "quantity": 1}], "started_at": now - timedelta(hours=5, minutes=30), "completed_at": now - timedelta(hours=3), "created_at": now - timedelta(hours=5), "updated_at": now - timedelta(hours=3)},
        {"_id": DISPATCH_IDS[4], "emergency_event_id": str(EVENT_IDS[2]), "eop_plan_id": str(EOP_IDS[2]), "task_title": "Triển khai nhà tạm lánh Sơn Trà", "priority": "critical", "status": "assigned", "eta_minutes": 120, "assignments": [{"resource_unit_id": str(RESOURCE_IDS[5]), "role": "Quản lý nhà lánh", "quantity": 1}], "created_at": now - timedelta(hours=4), "updated_at": now - timedelta(hours=2)},
        {"_id": DISPATCH_IDS[5], "emergency_event_id": str(EVENT_IDS[0]), "task_title": "Phân phối lương thực khẩn cấp", "priority": "high", "status": "pending", "eta_minutes": 90, "assignments": [], "created_at": now - timedelta(minutes=30), "updated_at": now - timedelta(minutes=30)},
    ]

    # ── Sitreps ───────────────────────────────────────────────
    sitreps = [
        {
            "_id": SITREP_IDS[0],
            "emergency_event_id": str(EVENT_IDS[0]),
            "title": "SITREP #1 – Ngập lụt Q8 – 09:00",
            "snapshot": {"water_level_cm": 80, "affected_households": 350, "evacuated": 120, "resources_deployed": 3},
            "deltas": [{"actor_id": "operator1", "action_type": "update", "changes": {"evacuated": "+120"}, "created_at": now - timedelta(hours=2)}],
            "status": "published",
            "published_by": "operator1",
            "published_at": now - timedelta(hours=2),
            "created_at": now - timedelta(hours=2, minutes=30),
            "updated_at": now - timedelta(hours=2),
        },
        {
            "_id": SITREP_IDS[1],
            "emergency_event_id": str(EVENT_IDS[0]),
            "title": "SITREP #2 – Ngập lụt Q8 – 11:00",
            "snapshot": {"water_level_cm": 65, "affected_households": 350, "evacuated": 280, "resources_deployed": 4},
            "deltas": [],
            "status": "published",
            "published_by": "operator1",
            "published_at": now - timedelta(minutes=30),
            "created_at": now - timedelta(hours=1),
            "updated_at": now - timedelta(minutes=30),
        },
        {
            "_id": SITREP_IDS[2],
            "emergency_event_id": str(EVENT_IDS[2]),
            "title": "SITREP #1 – Bão số 3 – Cảnh báo sớm",
            "snapshot": {"forecast_landfall_hours": 12, "evacuation_progress_pct": 35, "shelters_ready": 8},
            "deltas": [],
            "status": "draft",
            "created_at": now - timedelta(hours=3),
            "updated_at": now - timedelta(hours=3),
        },
    ]

    # ── After-Action Reports ──────────────────────────────────
    aars = [
        {
            "_id": AAR_IDS[0],
            "report_code": "AAR-2026-001",
            "emergency_event_id": str(EVENT_IDS[3]),
            "title": "Báo cáo sau sự cố mất điện Hà Nội – 2026-04-18",
            "summary": "Sự cố trạm biến áp 110kV gây mất điện 6 giờ, ảnh hưởng 50.000 hộ. Khôi phục hoàn toàn trong 22 tiếng.",
            "status": "published",
            "kpi": {
                "response_time_minutes": 18.0,
                "response_speed_score": 0.82,
                "dispatch_completion_rate": 0.95,
                "sitrep_coverage_rate": 0.88,
                "resource_efficiency_score": 0.79,
                "overall_score": 0.85,
            },
            "timeline": [
                {"timestamp": now - timedelta(hours=24), "source": "iot", "action": "Phát hiện sự cố trạm biến áp", "details": {}},
                {"timestamp": now - timedelta(hours=23, minutes=42), "source": "manual", "action": "Điều phối đội kỹ thuật", "details": {}},
                {"timestamp": now - timedelta(hours=2), "source": "manual", "action": "Khôi phục điện hoàn toàn", "details": {}},
            ],
            "lessons_learned": ["Cần bảo trì trạm biến áp định kỳ 6 tháng/lần", "Tăng cường máy phát dự phòng cho bệnh viện"],
            "recommendations": ["Đầu tư thêm 2 trạm biến áp dự phòng Q.HBT", "Huấn luyện đội ứng phó khẩn cấp điện mỗi quý"],
            "generated_by": "ai_system",
            "published_by": "director",
            "generated_at": now - timedelta(hours=4),
            "published_at": now - timedelta(hours=2),
            "created_at": now - timedelta(hours=4),
            "updated_at": now - timedelta(hours=2),
        },
        {
            "_id": AAR_IDS[1],
            "report_code": "AAR-2026-002",
            "emergency_event_id": str(EVENT_IDS[1]),
            "title": "Báo cáo sau sự cố cháy KCN Bình Dương – 2026-04-19",
            "summary": "Đám cháy được khống chế trong 5 tiếng. 3 nạn nhân bỏng nhẹ đã xuất viện.",
            "status": "draft",
            "kpi": {
                "response_time_minutes": 12.0,
                "response_speed_score": 0.91,
                "dispatch_completion_rate": 0.88,
                "sitrep_coverage_rate": 0.72,
                "resource_efficiency_score": 0.85,
                "overall_score": 0.84,
            },
            "timeline": [
                {"timestamp": now - timedelta(hours=6), "source": "manual", "action": "Báo cháy nhận được", "details": {}},
                {"timestamp": now - timedelta(hours=5, minutes=48), "source": "manual", "action": "Xe PCCC có mặt hiện trường", "details": {}},
                {"timestamp": now - timedelta(hours=1), "source": "manual", "action": "Lửa được khống chế hoàn toàn", "details": {}},
            ],
            "lessons_learned": ["Cần hệ thống báo cháy tự động trong kho hàng", "Tăng khoảng cách an toàn giữa các kho"],
            "recommendations": ["Yêu cầu lắp đặt sprinkler tại tất cả kho KCN"],
            "generated_by": "ai_system",
            "generated_at": now - timedelta(hours=1),
            "created_at": now - timedelta(hours=1),
            "updated_at": now - timedelta(hours=1),
        },
    ]

    # ── Insert all ────────────────────────────────────────────
    collections = {
        "emergency_events": events,
        "hazard_layers": hazards,
        "resource_units": resources,
        "eop_plans": eops,
        "dispatch_orders": dispatches,
        "sitreps": sitreps,
        "after_action_reports": aars,
    }

    for coll_name, docs in collections.items():
        coll = db[coll_name]
        # Clear existing dummy data
        await coll.delete_many({})
        result = await coll.insert_many(docs)
        print(f"✅ {coll_name}: inserted {len(result.inserted_ids)} docs")

    client.close()
    print("\n🎉 Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
