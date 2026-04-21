"""HTTP client for the standalone `llm-service` FastAPI.

Provides two high-level helpers that the backend uses to enrich EOP plans:

- ``generate_eop_markdown``: produce a free-form markdown EOP draft.
- ``generate_tasks``: derive a list of volunteer tasks from a markdown EOP.

Both helpers are resilient: if ``llm-service`` is unreachable or returns an
error payload, they raise :class:`LLMServiceError` so callers can fall back.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


class LLMServiceError(RuntimeError):
    """Raised when the LLM service cannot fulfil a request."""


def _base_url() -> str:
    base = settings.SOSCONN_LLM_BASE_URL.rstrip("/")
    # llm-service mounts routes under /v1
    if base.endswith("/v1"):
        return base
    return f"{base}/v1"


async def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{_base_url()}{path}"
    timeout = max(settings.SOSCONN_LLM_TIMEOUT_SECONDS, 1.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
    except httpx.HTTPError as exc:
        logger.warning("llm-service request to %s failed: %s", url, exc)
        raise LLMServiceError(f"llm-service unreachable: {exc}") from exc

    if response.status_code >= 400:
        logger.warning(
            "llm-service returned %s for %s: %s",
            response.status_code,
            url,
            response.text[:500],
        )
        raise LLMServiceError(
            f"llm-service responded {response.status_code}: {response.text[:200]}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise LLMServiceError("llm-service returned non-JSON body") from exc

    if isinstance(data, dict) and data.get("status") == "error":
        raise LLMServiceError(data.get("message") or "llm-service error")
    return data


async def generate_eop_markdown(
    *,
    flood_data: str,
    resource_data: str,
    location: str,
) -> str:
    """Call ``POST /v1/ai/generate-eop`` and return the markdown body."""
    payload = {
        "flood_data": flood_data or "N/A",
        "resource_data": resource_data or "N/A",
        "location": location or "N/A",
    }
    data = await _post("/ai/generate-eop", payload)
    report = data.get("eop_report") or data.get("report") or ""
    if not isinstance(report, str) or not report.strip():
        raise LLMServiceError("llm-service returned empty EOP markdown")
    return report.strip()


async def generate_tasks(
    *,
    emergency_operations_plan: str,
    flood_data: str,
    resource_data: str,
) -> List[Dict[str, str]]:
    """Call ``POST /v1/ai/generate-tasks`` and return the task list.

    Each task has keys ``priority``, ``description``, ``location``,
    ``resource_needed``.
    """
    payload = {
        "emergency_operations_plan": emergency_operations_plan,
        "flood_data": flood_data or "N/A",
        "resource_data": resource_data or "N/A",
    }
    data = await _post("/ai/generate-tasks", payload)
    tasks = data.get("tasks") or data.get("task_list") or []
    if not isinstance(tasks, list) or not tasks:
        raise LLMServiceError("llm-service returned empty task list")
    return tasks


def deterministic_eop_markdown(
    *,
    event_title: str,
    hazard_type: str,
    severity: str,
    location: str,
    objectives: Optional[List[str]] = None,
    actions: Optional[List[str]] = None,
) -> str:
    """Local markdown fallback when llm-service is unavailable."""
    obj_lines = "\n".join(f"- {line}" for line in (objectives or [])) or "- Bảo vệ tính mạng người dân\n- Giảm thiểu thiệt hại tài sản"
    act_lines = "\n".join(f"{idx + 1}. {line}" for idx, line in enumerate(actions or [])) or (
        "1. Kích hoạt đội ứng phó tại khu vực ảnh hưởng\n"
        "2. Thiết lập vùng an toàn & hướng dẫn sơ tán\n"
        "3. Điều phối lực lượng tình nguyện, vật tư y tế\n"
        "4. Duy trì liên lạc 2 chiều với hiện trường mỗi 30 phút\n"
        "5. Báo cáo tình hình về sở chỉ huy"
    )
    return (
        f"# Kế hoạch ứng phó — {event_title}\n\n"
        f"- **Loại sự cố:** {hazard_type}\n"
        f"- **Mức độ:** {severity}\n"
        f"- **Địa điểm:** {location or 'Chưa xác định'}\n\n"
        f"## Mục tiêu\n{obj_lines}\n\n"
        f"## Hành động ưu tiên\n{act_lines}\n\n"
        f"## Truyền thông\n- Cập nhật bản tin mỗi giờ\n- Kênh hotline: 114\n\n"
        f"## Phương án dự phòng\n- Duy trì đội backup tại điểm tập kết\n- Sẵn sàng điều xe cứu thương bổ sung\n"
    )


def deterministic_tasks(event_title: str, severity: str) -> List[Dict[str, str]]:
    """Local task fallback — keeps the flow usable without llm-service."""
    prio_map = {"critical": "High", "high": "High", "medium": "Medium", "low": "Low"}
    base = prio_map.get(severity, "Medium")
    return [
        {
            "priority": "High",
            "description": f"Sơ tán dân cư khu vực ảnh hưởng — {event_title}",
            "location": "Khu vực nguy hiểm trọng điểm",
            "resource_needed": "Xe tải nhẹ, áo phao, loa cầm tay",
        },
        {
            "priority": base,
            "description": "Thiết lập điểm tiếp nhận vật tư và y tế lưu động",
            "location": "Gần hiện trường, cao ráo",
            "resource_needed": "Lều bạt, bộ sơ cứu, nước uống",
        },
        {
            "priority": base,
            "description": "Phát loa hướng dẫn & đi kiểm tra các hộ đơn thân, người già",
            "location": "Tổ dân phố ảnh hưởng",
            "resource_needed": "Loa tay, pin dự phòng",
        },
        {
            "priority": "Medium",
            "description": "Ghi nhận tình trạng hạ tầng (điện, nước, cầu đường) và báo về",
            "location": "Khu vực lân cận",
            "resource_needed": "Bộ đàm, sổ tay, smartphone",
        },
        {
            "priority": "Low",
            "description": "Dọn dẹp, hỗ trợ người dân sau khi nước rút / sự cố dừng",
            "location": "Trong phạm vi triển khai",
            "resource_needed": "Găng tay, xẻng, bao tải",
        },
    ]
