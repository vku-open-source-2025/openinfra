"""Contract-first stream payload models for SOSConn integrations."""

from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Union

from pydantic import BaseModel, Field


class HazardStreamEvent(BaseModel):
    """Payload for hazard stream messages."""

    stream_type: str = "hazard"
    action: str = "upsert"
    hazard_id: Optional[str] = None
    id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    severity: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    geometry: Optional[Dict[str, Any]] = None
    district: Optional[str] = None
    ward: Optional[str] = None
    detected_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None

    class Config:
        extra = "allow"
        populate_by_name = True


class EmergencyStreamEvent(BaseModel):
    """Payload for emergency stream messages."""

    stream_type: str = "emergency"
    action: str = "upsert"
    event_id: Optional[str] = None
    emergency_event_id: Optional[str] = None
    id: Optional[str] = None
    event_code: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    affected_asset_ids: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None

    class Config:
        extra = "allow"
        populate_by_name = True


StreamEvent = Union[HazardStreamEvent, EmergencyStreamEvent]
StreamEventInput = Union[StreamEvent, Mapping[str, Any]]


def _to_iso8601(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None:
        return datetime.utcnow().isoformat()
    return str(value)


def as_stream_envelope(
    event: StreamEventInput,
    *,
    event_name: Optional[str] = None,
    schema_version: str = "1.0",
) -> Dict[str, Any]:
    """Normalize a stream payload into a simple compatibility envelope."""

    payload: Dict[str, Any]
    default_event: str

    if isinstance(event, HazardStreamEvent):
        payload = event.model_dump(mode="json", exclude_none=True)
        if "hazard_id" not in payload and payload.get("id"):
            payload["hazard_id"] = str(payload["id"])
        default_event = f"hazard.{payload.get('action', 'upsert')}"
    elif isinstance(event, EmergencyStreamEvent):
        payload = event.model_dump(mode="json", exclude_none=True)
        if "event_id" not in payload:
            legacy_event_id = payload.get("emergency_event_id") or payload.get("id")
            if legacy_event_id is not None:
                payload["event_id"] = str(legacy_event_id)
        default_event = f"emergency.{payload.get('action', 'upsert')}"
    elif isinstance(event, BaseModel):
        payload = event.model_dump(mode="json", exclude_none=True)
        default_event = str(
            payload.get("event")
            or payload.get("event_type")
            or payload.get("stream_type")
            or "event"
        )
    else:
        payload = {k: v for k, v in dict(event).items() if v is not None}
        default_event = str(
            payload.get("event")
            or payload.get("event_type")
            or payload.get("stream_type")
            or "event"
        )

    resolved_event = (
        event_name
        or payload.get("event")
        or payload.get("event_type")
        or default_event
    )
    resolved_event = str(resolved_event)

    emitted_value = payload.get("emitted_at") or payload.get("occurred_at")
    emitted_at = _to_iso8601(emitted_value)

    envelope: Dict[str, Any] = {
        "event": resolved_event,
        "event_type": resolved_event,
        "schema_version": str(schema_version),
        "emitted_at": emitted_at,
        "payload": payload,
        "data": payload,
    }

    request_id = payload.get("request_id")
    if request_id is not None:
        envelope["request_id"] = str(request_id)

    entity_id = payload.get("event_id") or payload.get("hazard_id") or payload.get("id")
    if entity_id is not None:
        envelope["entity_id"] = str(entity_id)

    return envelope


__all__ = [
    "HazardStreamEvent",
    "EmergencyStreamEvent",
    "as_stream_envelope",
]
