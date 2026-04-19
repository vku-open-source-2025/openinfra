"""Unit tests for SOS timeline shaping in emergency router."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.api.v1.routers import emergency
from app.domain.models.user import UserRole


class _FakeAsyncRows:
    """Async iterator for aggregate rows."""

    def __init__(self, rows: list[dict]):
        self._iterator = iter(rows)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class _FakeFindCursor:
    """Mongo-like cursor chain for find/sort/limit/to_list."""

    def __init__(self, docs: list[dict]):
        self._docs = list(docs)
        self._limit: int | None = None
        self.sort_args = None

    def sort(self, args):
        self.sort_args = args
        return self

    def limit(self, limit: int):
        self._limit = limit
        return self

    async def to_list(self, length: int):
        effective_limit = length if self._limit is None else min(length, self._limit)
        return self._docs[:effective_limit]


class _FakeEmergencyCollection:
    """Collection stub for emergency events."""

    def __init__(self, docs: list[dict]):
        self._docs = docs
        self.last_query = None
        self.last_projection = None

    def find(self, query: dict, projection: dict):
        self.last_query = query
        self.last_projection = projection
        return _FakeFindCursor(self._docs)


class _FakeSlaCollection:
    """Collection stub for SLA breach aggregate."""

    def __init__(self, rows: list[dict]):
        self._rows = rows
        self.last_pipeline = None

    def aggregate(self, pipeline: list[dict]):
        self.last_pipeline = pipeline
        return _FakeAsyncRows(self._rows)


class _FakeDb:
    """Simple database proxy exposing required collections."""

    def __init__(self, event_docs: list[dict], sla_rows: list[dict]):
        self.emergency_collection = _FakeEmergencyCollection(event_docs)
        self.sla_collection = _FakeSlaCollection(sla_rows)

    def __getitem__(self, key: str):
        if key == "emergency_events":
            return self.emergency_collection
        if key == "emergency_sla_breaches":
            return self.sla_collection
        raise KeyError(key)


@pytest.mark.parametrize(
    ("event_doc", "expected"),
    [
        (
            {
                "metadata": {
                    "source_ref": "SRC-001",
                    "sos_report_id": "SOS-001",
                    "request_id": "REQ-001",
                    "external_ref": "EXT-001",
                },
                "_contrib_sos_id": "CONTRIB-001",
            },
            "SRC-001",
        ),
        (
            {
                "metadata": {
                    "source_ref": "",
                    "sos_report_id": "SOS-002",
                    "request_id": "REQ-002",
                    "external_ref": "EXT-002",
                },
                "_contrib_sos_id": "CONTRIB-002",
            },
            "SOS-002",
        ),
        (
            {
                "metadata": {
                    "sos_report_id": None,
                    "request_id": "REQ-003",
                    "external_ref": "EXT-003",
                },
                "_contrib_sos_id": "CONTRIB-003",
            },
            "CONTRIB-003",
        ),
        (
            {
                "metadata": {
                    "request_id": "REQ-004",
                    "external_ref": "EXT-004",
                },
                "_contrib_sos_id": None,
            },
            "REQ-004",
        ),
        (
            {
                "metadata": {
                    "request_id": "",
                    "external_ref": 12345,
                },
            },
            "12345",
        ),
        (
            {
                "metadata": "invalid-metadata",
                "_contrib_sos_id": None,
            },
            None,
        ),
    ],
)
def test_extract_sos_source_ref_uses_defined_precedence(event_doc: dict, expected: str | None):
    assert emergency._extract_sos_source_ref(event_doc) == expected


@pytest.mark.asyncio
async def test_get_sos_timeline_counts_sla_breaches_by_event_id(monkeypatch: pytest.MonkeyPatch):
    now = datetime.utcnow()
    event_docs = [
        {
            "_id": "evt-001",
            "event_code": "E-001",
            "title": "Flood alert at district center",
            "severity": "high",
            "status": "active",
            "created_at": now - timedelta(minutes=10),
            "updated_at": now - timedelta(minutes=2),
            "metadata": {"sos_report_id": "SOS-RPT-001"},
            "_contrib_sos_id": None,
        },
        {
            "_id": "evt-002",
            "event_code": "E-002",
            "title": "Drain blockage report",
            "severity": "medium",
            "status": "investigating",
            "created_at": now - timedelta(minutes=12),
            "updated_at": now - timedelta(minutes=1),
            "metadata": {},
            "_contrib_sos_id": "CONTRIB-SOS-002",
        },
        {
            "_id": "evt-003",
            "event_code": "E-003",
            "title": "Power outage near station",
            "severity": "critical",
            "status": "active",
            "created_at": now - timedelta(minutes=20),
            "updated_at": now - timedelta(minutes=3),
            "metadata": {"request_id": "REQ-003"},
            "_contrib_sos_id": None,
        },
    ]
    sla_rows = [
        {"_id": "evt-001", "count": 2},
        {"_id": "evt-002", "count": 1},
        {"_id": None, "count": 99},
    ]

    fake_db = _FakeDb(event_docs=event_docs, sla_rows=sla_rows)

    async def _fake_get_database():
        return fake_db

    monkeypatch.setattr("app.infrastructure.database.mongodb.get_database", _fake_get_database)

    timeline = await emergency.get_sos_timeline(
        limit=10,
        current_user=SimpleNamespace(role=UserRole.ADMIN),
    )

    assert [item.event_id for item in timeline] == ["evt-001", "evt-002", "evt-003"]
    assert [item.source_ref for item in timeline] == ["SOS-RPT-001", "CONTRIB-SOS-002", "REQ-003"]
    assert [item.sla_breach_count for item in timeline] == [2, 1, 0]

    assert fake_db.sla_collection.last_pipeline == [
        {"$match": {"event_id": {"$in": ["evt-001", "evt-002", "evt-003"]}}},
        {"$group": {"_id": "$event_id", "count": {"$sum": 1}}},
    ]