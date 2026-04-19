"""Celery tasks for hazard feed ingestion."""

import asyncio
import logging
from typing import Dict, List

from app.celery_app import app as celery_app
from app.domain.services.geofence_service import GeofenceService
from app.domain.services.hazard_layer_service import HazardLayerService
from app.domain.services.notification_service import NotificationService
from app.domain.services.user_service import UserService
from app.infrastructure.database.mongodb import db as database_manager
from app.infrastructure.database.mongodb import get_database
from app.infrastructure.database.repositories.mongo_geofence_repository import (
    MongoGeofenceRepository,
)
from app.infrastructure.database.repositories.mongo_hazard_layer_repository import (
    MongoHazardLayerRepository,
)
from app.infrastructure.database.repositories.mongo_notification_repository import (
    MongoNotificationRepository,
)
from app.infrastructure.database.repositories.mongo_user_repository import (
    MongoUserRepository,
)
from app.infrastructure.notifications.emergency_notifier import EmergencyNotifier

from app.services.hazard_ingest_service import HazardIngestService

logger = logging.getLogger(__name__)


def _run(coro):
    """Run async code safely inside Celery task process."""
    return asyncio.run(coro)


async def _persist_records(
    records: List[dict],
    source_override: str | None,
) -> Dict[str, int]:
    """Persist normalized ingest records into hazard layer collection."""
    if database_manager.client is None:
        database_manager.connect()

    db = await get_database()
    repository = MongoHazardLayerRepository(db)
    await repository.ensure_indexes()
    service = HazardLayerService(repository)

    stats = await service.upsert_ingest_records(records, source_override=source_override)
    expired_deactivated = await service.deactivate_expired()

    geofence_repository = MongoGeofenceRepository(db)
    await geofence_repository.ensure_indexes()
    notification_repository = MongoNotificationRepository(db)
    user_repository = MongoUserRepository(db)
    notification_service = NotificationService(notification_repository, user_repository)
    user_service = UserService(user_repository)
    emergency_notifier = EmergencyNotifier(notification_service, user_service)
    geofence_service = GeofenceService(geofence_repository, emergency_notifier)

    geofence_checked = 0
    geofence_triggered = 0
    for hazard_db_id in stats.get("hazard_db_ids", []):
        hazard = await service.get_hazard_by_id(str(hazard_db_id))
        geofence_result = await geofence_service.check_and_trigger_hazard(hazard)
        geofence_checked += geofence_result.get("matched", 0)
        geofence_triggered += geofence_result.get("triggered", 0)

    return {
        "source": source_override or "mixed",
        "count": stats.get("total", 0),
        "inserted": stats.get("inserted", 0),
        "updated": stats.get("updated", 0),
        "expired_deactivated": expired_deactivated,
        "geofence_checked": geofence_checked,
        "geofence_triggered": geofence_triggered,
    }


@celery_app.task(
    name="app.tasks.hazard_ingest.ingest_nchmf_data",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def ingest_nchmf_data(self) -> Dict[str, int]:
    """Ingest NCHMF feed and persist to hazard layer collection."""
    try:
        service = HazardIngestService()
        records: List[dict] = _run(service.ingest_nchmf())
        if not records:
            logger.warning(
                "NCHMF hazard ingest returned 0 records; check NCHMF_FEED_URL and upstream status"
            )
        result = _run(_persist_records(records, source_override="nchmf"))
        logger.info("NCHMF hazard ingest completed: %s", result)
        return result
    except Exception as exc:
        logger.exception("NCHMF hazard ingest failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.hazard_ingest.ingest_vndms_data",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def ingest_vndms_data(self) -> Dict[str, int]:
    """Ingest VNDMS feed and persist to hazard layer collection."""
    try:
        service = HazardIngestService()
        records: List[dict] = _run(service.ingest_vndms())
        if not records:
            logger.warning(
                "VNDMS hazard ingest returned 0 records; check VNDMS_FEED_URL and upstream status"
            )
        result = _run(_persist_records(records, source_override="vndms"))
        logger.info("VNDMS hazard ingest completed: %s", result)
        return result
    except Exception as exc:
        logger.exception("VNDMS hazard ingest failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.tasks.hazard_ingest.ingest_hazard_feeds",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def ingest_hazard_feeds(self) -> Dict[str, int]:
    """Ingest all configured hazard feeds and persist to hazard layer collection."""
    try:
        service = HazardIngestService()
        records: List[dict] = _run(service.ingest_all())
        if not records:
            logger.warning(
                "Combined hazard ingest returned 0 records; verify feed URL configuration"
            )
        result = _run(_persist_records(records, source_override=None))
        logger.info("Hazard feed ingest completed: %s", result)
        return result
    except Exception as exc:
        logger.exception("Combined hazard ingest failed: %s", exc)
        raise self.retry(exc=exc)
