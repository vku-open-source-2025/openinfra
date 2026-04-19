"""Unit tests for dispatch optimizer v2 scoring helpers."""

from types import SimpleNamespace

from app.domain.models.dispatch_order import DispatchPriority
from app.domain.models.emergency import EmergencySeverity
from app.domain.services.dispatch_optimizer_scoring import (
    estimate_eta_minutes,
    score_dispatch_order,
)


def test_score_dispatch_order_prefers_critical_priority_and_age():
    critical_score = score_dispatch_order(
        priority=DispatchPriority.CRITICAL,
        age_minutes=60,
        emergency_severity=EmergencySeverity.HIGH,
        manual_boost=0,
    )
    low_score = score_dispatch_order(
        priority=DispatchPriority.LOW,
        age_minutes=10,
        emergency_severity=EmergencySeverity.LOW,
        manual_boost=0,
    )

    assert critical_score > low_score


def test_estimate_eta_minutes_rewards_local_vehicle_resource():
    resource = SimpleNamespace(resource_type=SimpleNamespace(value="vehicle"), district="Hai Chau")
    event = SimpleNamespace(location=SimpleNamespace(district="Hai Chau"))

    eta = estimate_eta_minutes(
        priority=DispatchPriority.HIGH,
        resource=resource,
        emergency_event=event,
    )

    assert eta < 25
    assert eta >= 8
