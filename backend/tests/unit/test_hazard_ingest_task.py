"""Unit tests for hazard crawl/update Celery task wrappers."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace


def _load_hazard_ingest_module():
    module_path = Path(__file__).resolve().parents[2] / "app" / "tasks" / "hazard_ingest.py"
    spec = importlib.util.spec_from_file_location("hazard_ingest_under_test", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load hazard_ingest module for tests")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hazard_ingest = _load_hazard_ingest_module()


def test_dedicated_crawl_task_uses_deterministic_deduplicated_upsert_flow(monkeypatch):
    captured = {}

    class FakeIngestService:
        feed_timeout_seconds = 17.0

        async def ingest_all(self):
            return [
                {
                    "source": "vndms",
                    "source_id": "B-2",
                    "title": "older-vndms",
                    "detected_at": "2026-04-20T01:00:00Z",
                },
                {
                    "source": "nchmf",
                    "source_id": "A-1",
                    "title": "nchmf-alert",
                    "detected_at": "2026-04-20T02:00:00Z",
                },
                {
                    "source": "vndms",
                    "source_id": "B-2",
                    "title": "latest-vndms",
                    "detected_at": "2026-04-20T03:00:00Z",
                },
                {
                    "source": "nchmf",
                    "title": "missing-source-id",
                },
            ]

    async def fake_persist_records(records, source_override):
        captured["records"] = records
        captured["source_override"] = source_override
        return {
            "source": "mixed",
            "count": len(records),
            "inserted": 1,
            "updated": 1,
            "expired_deactivated": 2,
            "geofence_checked": 3,
            "geofence_triggered": 1,
        }

    monkeypatch.setattr(hazard_ingest, "HazardIngestService", FakeIngestService)
    monkeypatch.setattr(hazard_ingest, "_persist_records", fake_persist_records)

    result = hazard_ingest.crawl_and_update_hazard_layers.run(
        source="all",
        triggered_by="unit-test",
    )

    assert captured["source_override"] is None
    assert [
        (record.get("source"), record.get("source_id"))
        for record in captured["records"]
    ] == [
        ("nchmf", "A-1"),
        ("vndms", "B-2"),
    ]
    assert captured["records"][1]["title"] == "latest-vndms"

    assert result["status"] == "success"
    assert result["source_mode"] == "all"
    assert result["triggered_by"] == "unit-test"
    assert result["count"] == 2
    assert result["inserted"] == 1
    assert result["updated"] == 1
    assert result["pipeline"]["during_disaster"]["received_records"] == 4
    assert result["pipeline"]["during_disaster"]["valid_keyed_records"] == 3
    assert result["pipeline"]["during_disaster"]["deduplicated_records"] == 1
    assert result["pipeline"]["during_disaster"]["skipped_records"] == 1


def test_runner_returns_failure_payload_when_retries_are_exhausted(monkeypatch):
    class FailingIngestService:
        feed_timeout_seconds = 20.0

        async def ingest_all(self):
            raise RuntimeError("upstream unavailable")

    retry_calls = {}

    def fake_retry(*, exc):
        retry_calls["exc"] = exc
        raise hazard_ingest.MaxRetriesExceededError("retries exhausted")

    fake_task = SimpleNamespace(
        name="app.tasks.hazard_ingest.crawl_and_update_hazard_layers",
        request=SimpleNamespace(id="hazard-task-001"),
        retry=fake_retry,
    )

    monkeypatch.setattr(hazard_ingest, "HazardIngestService", FailingIngestService)

    result = hazard_ingest._run_crawl_update_task(
        fake_task,
        source_mode="all",
        triggered_by="scheduler",
    )

    assert isinstance(retry_calls["exc"], RuntimeError)
    assert result["status"] == "failed"
    assert result["retry_exhausted"] is True
    assert result["task_name"] == "app.tasks.hazard_ingest.crawl_and_update_hazard_layers"
    assert result["task_id"] == "hazard-task-001"
    assert result["error"] == "upstream unavailable"
    assert result["pipeline"]["after_disaster"]["db_upsert_strategy"] == "source+hazard_id"
