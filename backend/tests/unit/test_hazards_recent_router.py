"""Unit tests for the hazards recent endpoint payload and validation."""

from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_hazard_layer_service
from app.api.v1.routers import hazards
from app.domain.models.hazard_layer import HazardLayer


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Override global DB fixture for pure unit tests."""
    yield


class FakeHazardLayerService:
    """Small fake service for recent hazards endpoint tests."""

    def __init__(self, hazards_list):
        self._hazards_list = list(hazards_list)
        self.calls = []

    async def list_recent_hazards(self, window_hours: int, limit: int, active_only: bool = True):
        self.calls.append(
            {
                "window_hours": window_hours,
                "limit": limit,
                "active_only": active_only,
            }
        )
        return self._hazards_list[:limit]


def _build_hazard(**overrides) -> HazardLayer:
    now = datetime(2026, 4, 20, 10, 0, 0)
    payload = {
        "_id": "haz-db-1",
        "hazard_id": "HZ-001",
        "title": "Ngap lut tai Hai Chau",
        "event_type": "flood",
        "severity": "high",
        "source": "vndms",
        "is_active": True,
        "geometry": {"type": "Point", "coordinates": [108.221, 16.067]},
        "district": "Hai Chau",
        "ward": "Hai Chau 1",
        "detected_at": now,
        "ingest_timestamp": now,
        "metadata": {
            "published_at": "2026-04-20T09:45:00Z",
            "warning_level": 3,
        },
        "created_at": now,
        "updated_at": now,
    }
    payload.update(overrides)
    return HazardLayer(**payload)


def _build_test_client(service: FakeHazardLayerService) -> TestClient:
    app = FastAPI()
    app.include_router(hazards.router, prefix="/hazards")
    app.dependency_overrides[get_hazard_layer_service] = lambda: service
    return TestClient(app)


def test_recent_hazards_endpoint_returns_compact_payload_with_defaults():
    service = FakeHazardLayerService(
        [
            _build_hazard(),
            _build_hazard(
                _id="haz-db-2",
                hazard_id="HZ-002",
                title="Sat lo bo song",
                source="nchmf",
                severity="critical",
                district=None,
                ward=None,
                geometry=None,
                metadata={"location_name": "Hoa Vang", "level": "4"},
            ),
        ]
    )
    client = _build_test_client(service)

    response = client.get("/hazards/recent")

    assert response.status_code == 200
    assert service.calls == [{"window_hours": 24, "limit": 50, "active_only": True}]

    payload = response.json()
    assert len(payload) == 2

    first = payload[0]
    assert first["id"] == "haz-db-1"
    assert first["title"] == "Ngap lut tai Hai Chau"
    assert first["name"] == "Ngap lut tai Hai Chau"
    assert first["severity"] == "high"
    assert first["level"] == 3.0
    assert first["source"] == "vndms"
    assert first["location_summary"] == "Hai Chau 1, Hai Chau"
    assert first["coordinates"] == [108.221, 16.067]
    assert first["occurred_at"].startswith("2026-04-20T10:00:00")
    assert first["published_at"].startswith("2026-04-20T09:45:00")

    second = payload[1]
    assert second["id"] == "haz-db-2"
    assert second["source"] == "nchmf"
    assert second["severity"] == "critical"
    assert second["level"] == 4.0
    assert second["location_summary"] == "Hoa Vang"
    assert second["coordinates"] is None


def test_recent_hazards_endpoint_accepts_custom_window_limit_and_filter():
    service = FakeHazardLayerService([_build_hazard()])
    client = _build_test_client(service)

    response = client.get("/hazards/recent", params={"hours": 6, "limit": 5, "active_only": False})

    assert response.status_code == 200
    assert service.calls == [{"window_hours": 6, "limit": 5, "active_only": False}]


def test_recent_hazards_endpoint_validates_hours_and_limit():
    service = FakeHazardLayerService([_build_hazard()])
    client = _build_test_client(service)

    invalid_hours = client.get("/hazards/recent", params={"hours": 0})
    invalid_limit = client.get("/hazards/recent", params={"limit": 201})

    assert invalid_hours.status_code == 422
    assert invalid_limit.status_code == 422
    assert service.calls == []
