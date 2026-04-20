"""Regression guards for vector corpus Celery schedule wiring."""

from app.celery_app import app as celery_app


def test_ingest_vector_corpus_beat_entry_exists_and_points_to_expected_task():
    beat_schedule = celery_app.conf.beat_schedule

    assert "ingest-vector-corpus" in beat_schedule
    assert beat_schedule["ingest-vector-corpus"]["task"] == (
        "app.tasks.vector_corpus_ingest.ingest_vector_corpus"
    )


def test_vector_corpus_ingest_module_is_included_in_celery_imports():
    includes = tuple(celery_app.conf.include or ())

    assert "app.tasks.vector_corpus_ingest" in includes