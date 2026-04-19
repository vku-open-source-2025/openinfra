"""Background monitoring tasks for emergency events."""

import asyncio
from datetime import datetime
import logging

from app.celery_app import app as celery_app
from app.domain.models.emergency import EmergencySeverity, EmergencyStatus
from app.infrastructure.database.mongodb import db as database_manager
from app.infrastructure.database.mongodb import get_database
from app.infrastructure.database.repositories.mongo_emergency_repository import (
    MongoEmergencyRepository,
)

logger = logging.getLogger(__name__)

_SLA_THRESHOLD_MINUTES = {
    EmergencySeverity.CRITICAL: 30,
    EmergencySeverity.HIGH: 60,
    EmergencySeverity.MEDIUM: 120,
    EmergencySeverity.LOW: 180,
}


def _next_severity(current: EmergencySeverity) -> EmergencySeverity:
    """Compute one-step severity escalation."""
    severity_order = [
        EmergencySeverity.LOW,
        EmergencySeverity.MEDIUM,
        EmergencySeverity.HIGH,
        EmergencySeverity.CRITICAL,
    ]
    current_idx = severity_order.index(current)
    next_idx = min(current_idx + 1, len(severity_order) - 1)
    return severity_order[next_idx]


def _can_escalate_again(event_metadata: dict, now: datetime) -> bool:
    """Allow escalation at most once per 2 hours for the same event."""
    monitor_meta = (event_metadata or {}).get("auto_monitoring", {})
    last_escalated_at = monitor_meta.get("last_escalated_at")
    if not last_escalated_at:
        return True
    try:
        last = datetime.fromisoformat(last_escalated_at)
    except ValueError:
        return True
    return (now - last).total_seconds() >= 120 * 60


async def _monitor_active_emergency_events_async() -> dict:
    """Evaluate active/monitoring emergency events and auto-adjust lifecycle."""
    if database_manager.client is None:
        database_manager.connect()

    db = await get_database()
    repository = MongoEmergencyRepository(db)
    now = datetime.utcnow()

    checked = 0
    escalated = 0
    auto_activated = 0
    sla_breached = 0

    sla_collection = db["emergency_sla_breaches"]
    await sla_collection.create_index([("event_id", 1), ("breached_at", -1)], name="idx_sla_event_time")

    active_events = await repository.list(
        skip=0,
        limit=500,
        status=EmergencyStatus.ACTIVE.value,
    )

    for event in active_events:
        checked += 1
        if not event.id:
            continue

        reference_time = event.started_at or event.created_at
        active_minutes = int((now - reference_time).total_seconds() / 60)
        should_escalate = (
            active_minutes >= 180
            and event.severity != EmergencySeverity.CRITICAL
            and _can_escalate_again(event.metadata, now)
        )

        metadata = dict(event.metadata or {})
        monitor_meta = dict(metadata.get("auto_monitoring", {}))
        update_payload = {}

        if should_escalate:
            next_severity = _next_severity(event.severity)
            monitor_meta["last_escalated_at"] = now.isoformat()
            monitor_meta["active_minutes"] = active_minutes
            monitor_meta["escalation_count"] = int(monitor_meta.get("escalation_count", 0)) + 1
            metadata["auto_monitoring"] = monitor_meta

            update_payload["severity"] = next_severity.value
            escalated += 1

        sla_threshold = _SLA_THRESHOLD_MINUTES.get(event.severity, 120)
        is_sla_breach = active_minutes >= sla_threshold

        if is_sla_breach:
            last_sla_breach = monitor_meta.get("last_sla_breach_at")
            should_record_breach = True
            if last_sla_breach:
                try:
                    last_breach_dt = datetime.fromisoformat(last_sla_breach)
                    should_record_breach = (now - last_breach_dt).total_seconds() >= 30 * 60
                except ValueError:
                    should_record_breach = True

            monitor_meta["sla"] = {
                "threshold_minutes": sla_threshold,
                "active_minutes": active_minutes,
                "status": "breached",
            }

            if should_record_breach:
                monitor_meta["last_sla_breach_at"] = now.isoformat()
                await sla_collection.insert_one(
                    {
                        "event_id": str(event.id),
                        "event_code": event.event_code,
                        "severity": event.severity.value,
                        "threshold_minutes": sla_threshold,
                        "active_minutes": active_minutes,
                        "status": event.status.value,
                        "breached_at": now,
                        "metadata": {
                            "title": event.title,
                            "event_type": event.event_type.value,
                        },
                    }
                )
                sla_breached += 1

        metadata["auto_monitoring"] = monitor_meta
        update_payload["metadata"] = metadata

        if update_payload:
            await repository.update(str(event.id), update_payload)

    monitoring_events = await repository.list(
        skip=0,
        limit=500,
        status=EmergencyStatus.MONITORING.value,
    )

    for event in monitoring_events:
        checked += 1
        if not event.id:
            continue

        monitoring_minutes = int((now - event.created_at).total_seconds() / 60)
        should_activate = (
            monitoring_minutes >= 60
            and event.severity in {EmergencySeverity.HIGH, EmergencySeverity.CRITICAL}
        )
        if not should_activate:
            continue

        metadata = dict(event.metadata or {})
        monitor_meta = dict(metadata.get("auto_monitoring", {}))
        monitor_meta["auto_activated_at"] = now.isoformat()
        monitor_meta["monitoring_minutes"] = monitoring_minutes
        metadata["auto_monitoring"] = monitor_meta

        await repository.update(
            str(event.id),
            {
                "status": EmergencyStatus.ACTIVE.value,
                "started_at": now,
                "metadata": metadata,
            },
        )
        auto_activated += 1

    return {
        "checked": checked,
        "escalated": escalated,
        "auto_activated": auto_activated,
        "sla_breached": sla_breached,
        "checked_at": now.isoformat(),
    }


@celery_app.task(name="app.tasks.event_monitoring.monitor_active_emergency_events")
def monitor_active_emergency_events() -> dict:
    """Periodic lifecycle and severity monitoring for emergency events."""
    result = asyncio.run(_monitor_active_emergency_events_async())
    logger.info("Emergency event monitoring completed: %s", result)
    return result
