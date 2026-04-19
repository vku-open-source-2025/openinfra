"""Pure scoring helpers for dispatch optimizer v2."""

from typing import Optional

from app.domain.models.dispatch_order import DispatchPriority
from app.domain.models.emergency import EmergencySeverity


def default_eta_minutes(priority: DispatchPriority) -> int:
    """Base ETA matrix by dispatch priority."""
    if priority == DispatchPriority.CRITICAL:
        return 15
    if priority == DispatchPriority.HIGH:
        return 25
    if priority == DispatchPriority.MEDIUM:
        return 40
    return 60


def _priority_weight(priority: DispatchPriority) -> int:
    """Map dispatch priority to numeric weight for optimizer scoring."""
    if priority == DispatchPriority.CRITICAL:
        return 100
    if priority == DispatchPriority.HIGH:
        return 70
    if priority == DispatchPriority.MEDIUM:
        return 45
    return 20


def _severity_weight(severity: Optional[EmergencySeverity]) -> int:
    """Map emergency severity to numeric score contribution."""
    if severity == EmergencySeverity.CRITICAL:
        return 40
    if severity == EmergencySeverity.HIGH:
        return 30
    if severity == EmergencySeverity.MEDIUM:
        return 15
    if severity == EmergencySeverity.LOW:
        return 5
    return 0


def score_dispatch_order(
    priority: DispatchPriority,
    age_minutes: int,
    emergency_severity: Optional[EmergencySeverity],
    manual_boost: float,
) -> float:
    """Compute optimization score for one dispatch order."""
    return (
        _priority_weight(priority)
        + min(age_minutes, 180) * 0.6
        + _severity_weight(emergency_severity)
        + manual_boost
    )


def estimate_eta_minutes(priority: DispatchPriority, resource, emergency_event) -> int:
    """Estimate ETA from order priority and coarse location fit."""
    eta = default_eta_minutes(priority)

    if emergency_event and emergency_event.location and emergency_event.location.district:
        if resource.district and resource.district == emergency_event.location.district:
            eta -= 10
    if resource.resource_type.value in {"vehicle", "rescue_equipment"}:
        eta -= 5

    return max(8, eta)
