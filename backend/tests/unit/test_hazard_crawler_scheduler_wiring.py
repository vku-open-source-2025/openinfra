"""Regression guards for hazard crawler Celery schedule wiring."""

from app.celery_app import app as celery_app


def test_hazard_crawler_beat_entry_exists_and_points_to_dedicated_task():
    beat_schedule = celery_app.conf.beat_schedule

    assert "crawl-and-update-hazard-feeds" in beat_schedule
    assert beat_schedule["crawl-and-update-hazard-feeds"]["task"] == (
        "app.tasks.hazard_ingest.crawl_and_update_hazard_layers"
    )


def test_hazard_crawler_runs_every_15_minutes():
    schedule = celery_app.conf.beat_schedule["crawl-and-update-hazard-feeds"]["schedule"]

    assert getattr(schedule, "_orig_minute", None) == "*/15"
    assert getattr(schedule, "_orig_hour", None) == "*"


def test_hazard_ingest_module_is_included_in_celery_imports():
    includes = tuple(celery_app.conf.include or ())

    assert "app.tasks.hazard_ingest" in includes
