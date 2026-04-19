"""Request ID helpers for request/event traceability."""

import uuid
from typing import Any, Dict, Optional

from fastapi import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"


def get_request_id(request: Request) -> Optional[str]:
    """Get request id from state/header if available."""
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        return str(request_id)

    raw_header_value = request.headers.get(REQUEST_ID_HEADER)
    if not raw_header_value:
        return None

    normalized = raw_header_value.strip()
    return normalized or None


def get_or_create_request_id(request: Request) -> str:
    """Get existing request id or generate and persist a new one."""
    request_id = get_request_id(request)
    if request_id:
        request.state.request_id = request_id
        return request_id

    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    return request_id


def set_request_id_header(response: Response, request_id: str):
    """Attach request id header to outgoing response."""
    response.headers[REQUEST_ID_HEADER] = request_id


def merge_request_id_metadata(
    metadata: Optional[Dict[str, Any]],
    request_id: str,
) -> Dict[str, Any]:
    """Merge request id into metadata payload without mutating input."""
    merged = dict(metadata or {})
    merged["request_id"] = request_id
    return merged
