"""Celery task for vector corpus ingestion."""

import asyncio
import logging
from typing import Any, Dict

from app.celery_app import app as celery_app
from app.infrastructure.database.mongodb import db as database_manager
from app.infrastructure.database.mongodb import get_database
from app.services.rag.vector_corpus_service import VectorCorpusService

logger = logging.getLogger(__name__)


def _run(coro):
    """Run async code safely inside Celery task process."""
    return asyncio.run(coro)


async def _ingest_vector_corpus_async() -> Dict[str, Any]:
    """Build and upsert vector corpus from emergency-related collections."""
    if database_manager.client is None:
        database_manager.connect()

    db = await get_database()
    service = VectorCorpusService(db)
    return await service.upsert_corpus_documents()


@celery_app.task(
    name="app.tasks.vector_corpus_ingest.ingest_vector_corpus",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
)
def ingest_vector_corpus(self) -> Dict[str, Any]:
    """Periodic task to refresh vector corpus for disaster RAG retrieval."""
    try:
        result = _run(_ingest_vector_corpus_async())
        logger.info("Vector corpus ingest completed: %s", result)
        return result
    except Exception as exc:
        logger.exception("Vector corpus ingest failed: %s", exc)
        raise self.retry(exc=exc)