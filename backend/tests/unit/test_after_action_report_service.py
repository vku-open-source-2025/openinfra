"""Unit tests for after-action report service."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import pytest

from app.core.exceptions import ValidationError
from app.domain.models.after_action_report import (
    AfterActionGenerateRequest,
    AfterActionReport,
    AfterActionReportUpdate,
)
from app.domain.models.dispatch_order import (
    DispatchOrder,
    DispatchOrderCreate,
    DispatchStatus,
)
from app.domain.models.emergency import (
    EmergencyEvent,
    EmergencyEventCreate,
    EmergencyEventType,
    EmergencySeverity,
    EmergencySource,
    EmergencyStatus,
)
from app.domain.models.sitrep import Sitrep, SitrepCreate, SitrepStatus
from app.domain.services.after_action_report_service import AfterActionReportService


class FakeAfterActionRepository:
    def __init__(self):
        self._items: dict[str, AfterActionReport] = {}

    async def create(self, payload: dict) -> AfterActionReport:
        report_id = str(len(self._items) + 1)
        report = AfterActionReport(**{**payload, "_id": report_id})
        self._items[report_id] = report
        return report

    async def find_by_id(self, report_id: str) -> Optional[AfterActionReport]:
        return self._items.get(report_id)

    async def find_latest_by_event(self, emergency_event_id: str) -> Optional[AfterActionReport]:
        candidates = [
            item for item in self._items.values() if item.emergency_event_id == emergency_event_id
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda item: item.created_at, reverse=True)
        return candidates[0]

    async def update(self, report_id: str, updates: dict) -> Optional[AfterActionReport]:
        current = self._items.get(report_id)
        if not current:
            return None

        payload = current.model_dump(by_alias=True)
        payload.update(updates)
        payload["_id"] = report_id
        updated = AfterActionReport(**payload)
        self._items[report_id] = updated
        return updated

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
    ):
        items = list(self._items.values())
        if emergency_event_id:
            items = [item for item in items if item.emergency_event_id == emergency_event_id]
        if status:
            items = [item for item in items if item.status.value == status]
        return items[skip : skip + limit]


class FakeEmergencyRepository:
    def __init__(self):
        now = datetime.utcnow()
        create_payload = EmergencyEventCreate(
            title="Flood Event",
            event_type=EmergencyEventType.FLOOD,
            severity=EmergencySeverity.HIGH,
            source=EmergencySource.MANUAL,
            started_at=now - timedelta(hours=2),
        )
        self.event = EmergencyEvent(
            **create_payload.model_dump(),
            _id="event-1",
            event_code="EMG-TEST-001",
            status=EmergencyStatus.RESOLVED,
            created_at=now - timedelta(hours=3),
            ended_at=now,
        )

    async def find_by_id(self, event_id: str) -> Optional[EmergencyEvent]:
        if event_id == "event-1":
            return self.event
        return None


class FakeDispatchRepository:
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ):
        if emergency_event_id != "event-1":
            return []

        now = datetime.utcnow()
        order_a = DispatchOrder(
            **DispatchOrderCreate(
                emergency_event_id="event-1",
                task_title="Pump deployment",
            ).model_dump(),
            _id="dispatch-1",
            status=DispatchStatus.COMPLETED,
            created_at=now - timedelta(hours=2),
            started_at=now - timedelta(hours=1, minutes=50),
            completed_at=now - timedelta(hours=1),
        )
        order_b = DispatchOrder(
            **DispatchOrderCreate(
                emergency_event_id="event-1",
                task_title="Traffic reroute",
            ).model_dump(),
            _id="dispatch-2",
            status=DispatchStatus.ASSIGNED,
            created_at=now - timedelta(hours=1, minutes=40),
            started_at=now - timedelta(hours=1, minutes=20),
        )
        return [order_a, order_b]


class FakeSitrepRepository:
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
    ):
        if emergency_event_id != "event-1":
            return []

        now = datetime.utcnow()
        draft = Sitrep(
            **SitrepCreate(
                emergency_event_id="event-1",
                title="SITREP #1",
            ).model_dump(),
            _id="sitrep-1",
            status=SitrepStatus.DRAFT,
            created_at=now - timedelta(hours=2),
        )
        published = Sitrep(
            **SitrepCreate(
                emergency_event_id="event-1",
                title="SITREP #2",
            ).model_dump(),
            _id="sitrep-2",
            status=SitrepStatus.PUBLISHED,
            created_at=now - timedelta(hours=1),
            published_at=now - timedelta(minutes=50),
        )
        return [draft, published]


@pytest.mark.asyncio
async def test_generate_after_action_report_creates_kpi():
    service = AfterActionReportService(
        after_action_repository=FakeAfterActionRepository(),
        emergency_repository=FakeEmergencyRepository(),
        dispatch_repository=FakeDispatchRepository(),
        sitrep_repository=FakeSitrepRepository(),
    )

    report = await service.generate_for_event(
        AfterActionGenerateRequest(emergency_event_id="event-1"),
        generated_by="operator-1",
    )

    assert report.emergency_event_id == "event-1"
    assert report.kpi.overall_score > 0
    assert len(report.timeline) >= 3


@pytest.mark.asyncio
async def test_generate_after_action_report_reuses_existing_without_force():
    repository = FakeAfterActionRepository()
    service = AfterActionReportService(
        after_action_repository=repository,
        emergency_repository=FakeEmergencyRepository(),
        dispatch_repository=FakeDispatchRepository(),
        sitrep_repository=FakeSitrepRepository(),
    )

    first = await service.generate_for_event(
        AfterActionGenerateRequest(emergency_event_id="event-1"),
        generated_by="operator-1",
    )
    second = await service.generate_for_event(
        AfterActionGenerateRequest(emergency_event_id="event-1"),
        generated_by="operator-2",
    )

    assert first.id == second.id


@pytest.mark.asyncio
async def test_published_report_cannot_be_updated():
    repository = FakeAfterActionRepository()
    service = AfterActionReportService(
        after_action_repository=repository,
        emergency_repository=FakeEmergencyRepository(),
        dispatch_repository=FakeDispatchRepository(),
        sitrep_repository=FakeSitrepRepository(),
    )

    report = await service.generate_for_event(
        AfterActionGenerateRequest(emergency_event_id="event-1"),
        generated_by="operator-1",
    )
    await service.publish_report(str(report.id), published_by="operator-1")

    with pytest.raises(ValidationError):
        await service.update_report(
            str(report.id),
            AfterActionReportUpdate(summary="attempt update after publish"),
            updated_by="operator-2",
        )
