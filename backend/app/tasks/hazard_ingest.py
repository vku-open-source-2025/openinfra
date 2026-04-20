"""Celery tasks for hazard feed ingestion."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from celery.exceptions import MaxRetriesExceededError

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


def _utcnow_iso() -> str:
    """Return UTC timestamp in ISO-8601 format with trailing Z."""
    return datetime.utcnow().isoformat() + "Z"


def _normalize_source_mode(source_mode: str) -> str:
    """Normalize source selector used by scheduler/manual task triggers."""
    mode = str(source_mode or "all").strip().lower()
    if mode in {"all", "mixed", "*", ""}:
        return "all"
    if mode in {"nchmf", "vndms"}:
        return mode
    raise ValueError("source must be one of: all, nchmf, vndms")


def _record_identity(
    record: dict,
    source_override: Optional[str],
) -> Optional[Tuple[str, str]]:
    """Build deterministic identity key for one normalized ingest record."""
    source = str(source_override or record.get("source") or "other").strip().lower() or "other"
    source_id = str(record.get("source_id") or record.get("hazard_id") or "").strip()
    if not source_id:
        return None
    return source, source_id


def _record_rank(record: dict) -> Tuple[str, str]:
    """Rank duplicate records to deterministically keep the most relevant one."""
    detected_at_raw = record.get("detected_at")
    if isinstance(detected_at_raw, datetime):
        detected_at_key = detected_at_raw.isoformat()
    else:
        detected_at_key = str(detected_at_raw or "")

    try:
        payload_fingerprint = json.dumps(record, sort_keys=True, default=str, ensure_ascii=True)
    except TypeError:
        payload_fingerprint = str(record)

    return detected_at_key, payload_fingerprint


def _prepare_deterministic_records(
    records: List[dict],
    source_override: Optional[str],
) -> Tuple[List[dict], Dict[str, int]]:
    """Deterministically de-duplicate records before repository upsert."""
    deduped: Dict[Tuple[str, str], dict] = {}
    valid_keyed_records = 0
    skipped_records = 0

    for record in records:
        if not isinstance(record, dict):
            skipped_records += 1
            continue

        identity = _record_identity(record, source_override)
        if identity is None:
            skipped_records += 1
            continue

        valid_keyed_records += 1
        previous = deduped.get(identity)
        if previous is None or _record_rank(record) >= _record_rank(previous):
            deduped[identity] = record

    ordered_records = [deduped[key] for key in sorted(deduped)]
    deduplicated_records = max(valid_keyed_records - len(ordered_records), 0)

    return ordered_records, {
        "received_records": len(records),
        "valid_keyed_records": valid_keyed_records,
        "deduplicated_records": deduplicated_records,
        "skipped_records": skipped_records,
        "persisted_candidates": len(ordered_records),
    }


def _collect_records(
    service: HazardIngestService,
    source_mode: str,
) -> Tuple[List[dict], Optional[str], str]:
    """Collect hazard records from one or all providers."""
    mode = _normalize_source_mode(source_mode)
    if mode == "nchmf":
        return _run(service.ingest_nchmf()), "nchmf", "nchmf"
    if mode == "vndms":
        return _run(service.ingest_vndms()), "vndms", "vndms"
    return _run(service.ingest_all()), None, "mixed"


def _build_failure_payload(
    *,
    context: Dict[str, Any],
    source_label: str,
    source_mode: str,
    triggered_by: str,
    error: Exception,
    started_at: str,
    finished_at: str,
    status: str,
    retry_exhausted: bool,
) -> Dict[str, Any]:
    """Build a stable failure payload for scheduler observability."""
    return {
        "status": status,
        "source": source_label,
        "source_mode": source_mode,
        "triggered_by": triggered_by,
        "task_name": context.get("task_name"),
        "task_id": context.get("task_id"),
        "count": 0,
        "inserted": 0,
        "updated": 0,
        "expired_deactivated": 0,
        "geofence_checked": 0,
        "geofence_triggered": 0,
        "error": str(error),
        "retry_exhausted": retry_exhausted,
        "pipeline": {
            "before_disaster": {
                "crawl_started_at": started_at,
                "source_mode": source_mode,
            },
            "during_disaster": {
                "received_records": 0,
                "valid_keyed_records": 0,
                "deduplicated_records": 0,
                "skipped_records": 0,
            },
            "after_disaster": {
                "crawl_finished_at": finished_at,
                "db_upsert_strategy": "source+hazard_id",
            },
        },
    }


def _run_crawl_update_task(
    task_self,
    *,
    source_mode: str,
    triggered_by: str,
) -> Dict[str, Any]:
    """Shared runner for scheduler-driven hazard crawl and DB update flow."""
    started_at = _utcnow_iso()
    normalized_mode = str(source_mode or "all").strip().lower() or "all"
    context = {
        "task_name": getattr(task_self, "name", "app.tasks.hazard_ingest.crawl_and_update_hazard_layers"),
        "task_id": getattr(getattr(task_self, "request", None), "id", None),
        "triggered_by": triggered_by,
        "source_mode": normalized_mode,
    }
    logger.info("Hazard crawl/update started | context=%s", context)

    try:
        normalized_mode = _normalize_source_mode(source_mode)
        context["source_mode"] = normalized_mode

        service = HazardIngestService()
        records, source_override, source_label = _collect_records(service, normalized_mode)
        deterministic_records, quality_stats = _prepare_deterministic_records(records, source_override)

        if not deterministic_records:
            logger.warning(
                "Hazard crawl produced no valid records | context=%s quality=%s",
                context,
                quality_stats,
            )

        persist_result = _run(_persist_records(deterministic_records, source_override=source_override))
        finished_at = _utcnow_iso()
        result = {
            "status": "success",
            "source": persist_result.get("source", source_label),
            "source_mode": normalized_mode,
            "triggered_by": triggered_by,
            "task_name": context["task_name"],
            "task_id": context["task_id"],
            "count": persist_result.get("count", 0),
            "inserted": persist_result.get("inserted", 0),
            "updated": persist_result.get("updated", 0),
            "expired_deactivated": persist_result.get("expired_deactivated", 0),
            "geofence_checked": persist_result.get("geofence_checked", 0),
            "geofence_triggered": persist_result.get("geofence_triggered", 0),
            "pipeline": {
                "before_disaster": {
                    "crawl_started_at": started_at,
                    "source_mode": normalized_mode,
                    "feed_timeout_seconds": service.feed_timeout_seconds,
                },
                "during_disaster": quality_stats,
                "after_disaster": {
                    "crawl_finished_at": finished_at,
                    "db_upsert_strategy": "source+hazard_id",
                    "inserted": persist_result.get("inserted", 0),
                    "updated": persist_result.get("updated", 0),
                    "expired_deactivated": persist_result.get("expired_deactivated", 0),
                },
            },
        }
        logger.info("Hazard crawl/update completed | result=%s", result)
        return result
    except ValueError as exc:
        finished_at = _utcnow_iso()
        result = _build_failure_payload(
            context=context,
            source_label="mixed",
            source_mode=normalized_mode,
            triggered_by=triggered_by,
            error=exc,
            started_at=started_at,
            finished_at=finished_at,
            status="invalid_arguments",
            retry_exhausted=False,
        )
        logger.error("Hazard crawl/update aborted | result=%s", result)
        return result
    except Exception as exc:
        finished_at = _utcnow_iso()
        logger.exception("Hazard crawl/update failed | context=%s", context)
        try:
            raise task_self.retry(exc=exc)
        except MaxRetriesExceededError:
            result = _build_failure_payload(
                context=context,
                source_label="mixed" if normalized_mode == "all" else normalized_mode,
                source_mode=normalized_mode,
                triggered_by=triggered_by,
                error=exc,
                started_at=started_at,
                finished_at=finished_at,
                status="failed",
                retry_exhausted=True,
            )
            logger.error("Hazard crawl/update exhausted retries | result=%s", result)
            return result


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
    name="app.tasks.hazard_ingest.crawl_and_update_hazard_layers",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def crawl_and_update_hazard_layers(
    self,
    source: str = "all",
    triggered_by: str = "scheduler",
) -> Dict[str, Any]:
    """Dedicated scheduler entrypoint for hazard crawl/update pipeline."""
    return _run_crawl_update_task(
        self,
        source_mode=source,
        triggered_by=triggered_by,
    )


@celery_app.task(
    name="app.tasks.hazard_ingest.ingest_nchmf_data",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def ingest_nchmf_data(self) -> Dict[str, Any]:
    """Backward-compatible NCHMF-only ingest task symbol."""
    return _run_crawl_update_task(
        self,
        source_mode="nchmf",
        triggered_by="legacy_nchmf_task",
    )


@celery_app.task(
    name="app.tasks.hazard_ingest.ingest_vndms_data",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def ingest_vndms_data(self) -> Dict[str, Any]:
    """Backward-compatible VNDMS-only ingest task symbol."""
    return _run_crawl_update_task(
        self,
        source_mode="vndms",
        triggered_by="legacy_vndms_task",
    )


@celery_app.task(
    name="app.tasks.hazard_ingest.ingest_hazard_feeds",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def ingest_hazard_feeds(self) -> Dict[str, Any]:
    """Backward-compatible combined ingest task symbol."""
    return _run_crawl_update_task(
        self,
        source_mode="all",
        triggered_by="legacy_combined_task",
    )
