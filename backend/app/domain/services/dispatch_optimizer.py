"""Dispatch optimizer v2 service logic shared by API and Celery task."""

from datetime import datetime
from typing import Dict, List, Optional

from app.domain.models.dispatch_order import DispatchStatus
from app.domain.models.resource_unit import ResourceStatus
from app.domain.services.dispatch_optimizer_scoring import (
    default_eta_minutes,
    estimate_eta_minutes,
    score_dispatch_order,
)
from app.infrastructure.database.mongodb import db as database_manager
from app.infrastructure.database.mongodb import get_database
from app.infrastructure.database.repositories.mongo_dispatch_order_repository import (
    MongoDispatchOrderRepository,
)
from app.infrastructure.database.repositories.mongo_emergency_repository import (
    MongoEmergencyRepository,
)
from app.infrastructure.database.repositories.mongo_resource_unit_repository import (
    MongoResourceUnitRepository,
)


def _resource_fit_score(resource, order, emergency_event) -> float:
    """Score one resource candidate for a specific order."""
    score = 0.0
    order_text = f"{order.task_title or ''} {order.task_description or ''}".lower()

    # Prefer resources in same district when location context exists.
    event_district = None
    if emergency_event and emergency_event.location:
        event_district = emergency_event.location.district

    if event_district and resource.district and resource.district == event_district:
        score += 20
    elif resource.district:
        score += 5

    for skill in resource.skills:
        if skill.lower() in order_text:
            score += 8

    if resource.resource_type.value in {"vehicle", "rescue_equipment", "personnel"}:
        score += 6

    if resource.status == ResourceStatus.AVAILABLE:
        score += 4
    elif resource.status == ResourceStatus.STANDBY:
        score += 2

    return score


async def optimize_dispatch_orders(
    *,
    triggered_by: str,
    max_orders: int = 500,
    force_reestimate_eta: bool = False,
) -> Dict[str, object]:
    """Optimize pending dispatch orders with heuristic scoring and resource matching."""
    if database_manager.client is None:
        database_manager.connect()

    db = await get_database()
    dispatch_repo = MongoDispatchOrderRepository(db)
    resource_repo = MongoResourceUnitRepository(db)
    emergency_repo = MongoEmergencyRepository(db)

    now = datetime.utcnow()
    optimized = 0
    auto_assigned = 0
    stale_flagged = 0
    eta_reestimated = 0

    pending_orders = await dispatch_repo.list(
        skip=0,
        limit=max_orders,
        status=DispatchStatus.PENDING.value,
    )

    available_resources = await resource_repo.list(
        skip=0,
        limit=500,
        status=ResourceStatus.AVAILABLE.value,
    )
    standby_resources = await resource_repo.list(
        skip=0,
        limit=200,
        status=ResourceStatus.STANDBY.value,
    )
    available_pool = [
        resource
        for resource in [*available_resources, *standby_resources]
        if resource.id
    ]

    event_cache = {}

    scored_orders: List[dict] = []
    for order in pending_orders:
        order_age_minutes = int((now - order.created_at).total_seconds() / 60)

        emergency_event = None
        if order.emergency_event_id:
            if order.emergency_event_id not in event_cache:
                event_cache[order.emergency_event_id] = await emergency_repo.find_by_id(
                    order.emergency_event_id
                )
            emergency_event = event_cache.get(order.emergency_event_id)

        manual_boost = 0.0
        if order.metadata and isinstance(order.metadata.get("manual_priority_boost"), (int, float)):
            manual_boost = float(order.metadata.get("manual_priority_boost"))

        order_score = score_dispatch_order(
            priority=order.priority,
            age_minutes=order_age_minutes,
            emergency_severity=emergency_event.severity if emergency_event else None,
            manual_boost=manual_boost,
        )
        scored_orders.append(
            {
                "order": order,
                "score": order_score,
                "age_minutes": order_age_minutes,
                "emergency_event": emergency_event,
            }
        )

    scored_orders.sort(key=lambda item: item["score"], reverse=True)

    for item in scored_orders:
        order = item["order"]
        order_age_minutes = item["age_minutes"]
        emergency_event = item["emergency_event"]

        if not order.id:
            continue

        optimized += 1
        update_payload = {}
        metadata = dict(order.metadata or {})
        metadata["optimizer_v2"] = {
            "score": round(item["score"], 2),
            "age_minutes": order_age_minutes,
            "triggered_by": triggered_by,
            "evaluated_at": now.isoformat(),
        }

        best_resource = None
        best_resource_score = -1.0
        if not order.assignments and available_pool:
            for resource in available_pool:
                candidate_score = _resource_fit_score(resource, order, emergency_event)
                if candidate_score > best_resource_score:
                    best_resource = resource
                    best_resource_score = candidate_score

        if order.eta_minutes is None or force_reestimate_eta:
            eta_resource = best_resource if best_resource else (available_pool[0] if available_pool else None)
            if eta_resource:
                update_payload["eta_minutes"] = estimate_eta_minutes(
                    order.priority,
                    eta_resource,
                    emergency_event,
                )
            else:
                update_payload["eta_minutes"] = default_eta_minutes(order.priority)
            eta_reestimated += 1

        if not order.assignments and best_resource is not None:
            resource_id = str(best_resource.id)

            update_payload["assignments"] = [
                {
                    "resource_unit_id": resource_id,
                    "role": "auto_assigned_v2",
                    "quantity": 1.0,
                    "notes": "Assigned by dispatch optimizer v2",
                }
            ]
            update_payload["status"] = DispatchStatus.ASSIGNED.value
            update_payload["started_at"] = now
            update_payload["updated_by"] = f"system_dispatch_optimizer:{triggered_by}"

            metadata["auto_assigned_at"] = now.isoformat()
            metadata["auto_assigned_resource_id"] = resource_id
            metadata["auto_assigned_resource_score"] = round(best_resource_score, 2)
            update_payload["metadata"] = metadata

            await resource_repo.update(
                resource_id,
                {
                    "status": ResourceStatus.DEPLOYED.value,
                    "assigned_dispatch_order_id": str(order.id),
                },
            )
            available_pool = [resource for resource in available_pool if str(resource.id) != resource_id]
            auto_assigned += 1

        if not order.assignments and "status" not in update_payload:
            if order_age_minutes >= 20:
                metadata["requires_manual_assignment"] = True
                metadata["optimizer_checked_at"] = now.isoformat()
                metadata["pending_minutes"] = order_age_minutes
                metadata["replan_recommended"] = order_age_minutes >= 45
                update_payload["metadata"] = metadata
                stale_flagged += 1
            else:
                update_payload["metadata"] = metadata
        elif "metadata" not in update_payload:
            update_payload["metadata"] = metadata

        if update_payload:
            await dispatch_repo.update(str(order.id), update_payload)

    return {
        "optimized": optimized,
        "auto_assigned": auto_assigned,
        "stale_flagged": stale_flagged,
        "eta_reestimated": eta_reestimated,
        "algorithm": "dispatch_optimizer_v2",
        "triggered_by": triggered_by,
        "optimized_at": now.isoformat(),
    }
