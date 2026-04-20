"""Unit tests for MongoHazardLayerRepository recent hazard query."""

from datetime import datetime, timedelta

import pytest
from pymongo import DESCENDING

from app.infrastructure.database.repositories.mongo_hazard_layer_repository import (
    MongoHazardLayerRepository,
)


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Override global DB fixture for pure unit tests."""
    yield


class FakeCursor:
    """Minimal async cursor for repository unit tests."""

    def __init__(self, docs):
        self._docs = list(docs)
        self._iter = iter(())
        self.sort_args = None
        self.limit_value = None

    def sort(self, *args, **kwargs):
        self.sort_args = (args, kwargs)
        if args and isinstance(args[0], list):
            sort_spec = args[0]
            for field, direction in reversed(sort_spec):
                reverse = direction == DESCENDING
                self._docs.sort(key=lambda item: item.get(field), reverse=reverse)
        return self

    def limit(self, value):
        self.limit_value = value
        if value is not None:
            self._docs = self._docs[:value]
        return self

    def __aiter__(self):
        self._iter = iter(self._docs)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class FakeCollection:
    """Configurable fake Motor collection for recent query tests."""

    def __init__(self, docs):
        self._docs = list(docs)
        self.last_query = None
        self.last_cursor = None

    def find(self, query):
        self.last_query = query
        self.last_cursor = FakeCursor(self._docs)
        return self.last_cursor


class FakeDatabase:
    """Fake AsyncIOMotorDatabase-like object for repository constructor."""

    def __init__(self, collection: FakeCollection):
        self._collection = collection

    def __getitem__(self, name):
        assert name == "hazard_layers"
        return self._collection


def _build_doc(identifier: str, detected_at: datetime, is_active: bool = True):
    return {
        "_id": identifier,
        "hazard_id": f"HZ-{identifier}",
        "title": f"Hazard {identifier}",
        "event_type": "flood",
        "severity": "high",
        "source": "vndms",
        "is_active": is_active,
        "geometry": {"type": "Point", "coordinates": [108.2, 16.0]},
        "district": "Hai Chau",
        "ward": "Hai Chau 1",
        "detected_at": detected_at,
        "ingest_timestamp": detected_at,
        "metadata": {},
        "created_at": detected_at,
        "updated_at": detected_at,
    }


@pytest.mark.asyncio
async def test_list_recent_applies_detected_at_filter_sort_and_limit():
    now = datetime(2026, 4, 20, 12, 0, 0)
    cutoff = now - timedelta(hours=24)

    collection = FakeCollection(
        [
            _build_doc("old", now - timedelta(hours=5)),
            _build_doc("new", now - timedelta(hours=1)),
            _build_doc("mid", now - timedelta(hours=3)),
        ]
    )
    repository = MongoHazardLayerRepository(FakeDatabase(collection))

    hazards = await repository.list_recent(window_start=cutoff, limit=2, active_only=True)

    assert collection.last_query == {
        "detected_at": {"$gte": cutoff},
        "is_active": True,
    }
    assert collection.last_cursor is not None
    assert collection.last_cursor.sort_args is not None
    assert collection.last_cursor.sort_args[0][0] == [
        ("detected_at", DESCENDING),
        ("updated_at", DESCENDING),
    ]
    assert collection.last_cursor.limit_value == 2

    assert [hazard.id for hazard in hazards] == ["new", "mid"]


@pytest.mark.asyncio
async def test_list_recent_can_skip_active_only_filter():
    now = datetime(2026, 4, 20, 12, 0, 0)
    cutoff = now - timedelta(hours=24)

    collection = FakeCollection([_build_doc("inactive", now - timedelta(hours=2), is_active=False)])
    repository = MongoHazardLayerRepository(FakeDatabase(collection))

    hazards = await repository.list_recent(window_start=cutoff, limit=10, active_only=False)

    assert collection.last_query == {"detected_at": {"$gte": cutoff}}
    assert len(hazards) == 1
    assert hazards[0].id == "inactive"
