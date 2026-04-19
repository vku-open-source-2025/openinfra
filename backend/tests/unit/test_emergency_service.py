"""Unit tests for emergency service workflow rules."""

from __future__ import annotations

from typing import Optional

import pytest

from app.core.exceptions import ValidationError
from app.domain.models.emergency import (
    EmergencyEvent,
    EmergencyEventCreate,
    EmergencyEventUpdate,
    EmergencyStatus,
)
from app.domain.services.emergency_service import EmergencyService


class FakeEmergencyRepository:
    """In-memory repository for emergency service tests."""

    def __init__(self):
        self._items: dict[str, EmergencyEvent] = {}

    async def create(self, event_data: dict) -> EmergencyEvent:
        event_id = str(len(self._items) + 1)
        payload = {**event_data, "_id": event_id}
        event = EmergencyEvent(**payload)
        self._items[event_id] = event
        return event

    async def find_by_id(self, event_id: str) -> Optional[EmergencyEvent]:
        return self._items.get(event_id)

    async def update(self, event_id: str, updates: dict) -> Optional[EmergencyEvent]:
        current = self._items.get(event_id)
        if not current:
            return None

        payload = current.model_dump(by_alias=True)
        payload.update(updates)
        payload["_id"] = event_id
        updated = EmergencyEvent(**payload)
        self._items[event_id] = updated
        return updated

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        query_text: Optional[str] = None,
    ):
        events = list(self._items.values())

        if status:
            events = [event for event in events if event.status.value == status]
        if severity:
            events = [event for event in events if event.severity.value == severity]
        if event_type:
            events = [event for event in events if event.event_type.value == event_type]
        if query_text:
            q = query_text.lower()
            events = [
                event
                for event in events
                if q in event.title.lower() or q in (event.event_code or "").lower()
            ]

        return events[skip : skip + limit]


@pytest.mark.asyncio
async def test_invalid_emergency_status_transition_is_rejected():
    repository = FakeEmergencyRepository()
    service = EmergencyService(repository)

    created = await service.create_event(
        EmergencyEventCreate(
            title="Flood Warning",
            event_type="flood",
            severity="high",
        ),
        created_by="operator-1",
    )

    with pytest.raises(ValidationError):
        await service.update_event(
            str(created.id),
            EmergencyEventUpdate(status=EmergencyStatus.RESOLVED),
            updated_by="operator-2",
        )


@pytest.mark.asyncio
async def test_resolve_emergency_sets_ended_at_and_resolution_note():
    repository = FakeEmergencyRepository()
    service = EmergencyService(repository)

    created = await service.create_event(
        EmergencyEventCreate(
            title="Power Outage",
            event_type="outage",
            severity="medium",
        ),
        created_by="operator-1",
    )

    event_id = str(created.id)

    await service.update_event(
        event_id,
        EmergencyEventUpdate(status=EmergencyStatus.ACTIVE),
        updated_by="operator-2",
    )

    resolved = await service.resolve_event(
        event_id,
        resolution_note="Power restored after grid reset",
        updated_by="operator-3",
    )

    assert resolved.status == EmergencyStatus.RESOLVED
    assert resolved.ended_at is not None
    assert resolved.metadata.get("resolution_note") == "Power restored after grid reset"
