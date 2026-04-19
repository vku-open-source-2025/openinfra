"""Geofence service for hazard-triggered alerting."""

from datetime import datetime, timedelta
from typing import Dict, Optional

from app.core.exceptions import NotFoundError
from app.domain.models.geofence import Geofence, GeofenceCreate, GeofenceUpdate
from app.domain.models.hazard_layer import HazardLayer, HazardSeverity
from app.domain.repositories.geofence_repository import GeofenceRepository
from app.infrastructure.notifications.emergency_notifier import EmergencyNotifier


class GeofenceService:
    """Business logic for geofences and geofence-triggered alerts."""

    _SEVERITY_ORDER = {
        HazardSeverity.LOW.value: 1,
        HazardSeverity.MEDIUM.value: 2,
        HazardSeverity.HIGH.value: 3,
        HazardSeverity.CRITICAL.value: 4,
    }

    def __init__(
        self,
        repository: GeofenceRepository,
        emergency_notifier: Optional[EmergencyNotifier] = None,
    ):
        self.repository = repository
        self.notifier = emergency_notifier

    def _severity_meets_threshold(self, hazard_severity: str, threshold: str) -> bool:
        """Check if hazard severity meets geofence threshold."""
        hazard_rank = self._SEVERITY_ORDER.get(hazard_severity, 0)
        threshold_rank = self._SEVERITY_ORDER.get(threshold, 0)
        return hazard_rank >= threshold_rank

    async def create_geofence(self, payload: GeofenceCreate, created_by: Optional[str]) -> Geofence:
        """Create geofence."""
        data = payload.model_dump(exclude_unset=True)
        data["created_by"] = created_by
        return await self.repository.create(data)

    async def get_geofence_by_id(self, geofence_id: str) -> Geofence:
        """Get geofence by id."""
        geofence = await self.repository.find_by_id(geofence_id)
        if not geofence:
            raise NotFoundError("Geofence", geofence_id)
        return geofence

    async def update_geofence(self, geofence_id: str, payload: GeofenceUpdate) -> Geofence:
        """Update geofence."""
        _ = await self.get_geofence_by_id(geofence_id)
        updated = await self.repository.update(
            geofence_id,
            payload.model_dump(exclude_unset=True),
        )
        if not updated:
            raise NotFoundError("Geofence", geofence_id)
        return updated

    async def delete_geofence(self, geofence_id: str) -> bool:
        """Delete geofence."""
        _ = await self.get_geofence_by_id(geofence_id)
        return await self.repository.delete(geofence_id)

    async def list_geofences(self, skip: int = 0, limit: int = 100):
        """List geofences."""
        return await self.repository.list(skip=skip, limit=limit)

    async def check_and_trigger_hazard(self, hazard: HazardLayer) -> Dict[str, int]:
        """Evaluate hazard against geofences and trigger alerts."""
        matched_geofences = await self.repository.find_matching_hazard(
            hazard_geometry=hazard.geometry,
            district=hazard.district,
            ward=hazard.ward,
        )

        triggered = 0
        skipped = 0

        for geofence in matched_geofences:
            if geofence.event_types and hazard.event_type not in geofence.event_types:
                skipped += 1
                continue

            if not self._severity_meets_threshold(
                hazard.severity.value,
                geofence.min_severity.value,
            ):
                skipped += 1
                continue

            if not geofence.id or not hazard.id:
                skipped += 1
                continue

            already_sent = await self.repository.has_recent_alert(
                geofence_id=str(geofence.id),
                hazard_layer_id=str(hazard.id),
                since=datetime.utcnow() - timedelta(minutes=30),
            )
            if already_sent:
                skipped += 1
                continue

            title = f"[{hazard.severity.value.upper()}] {hazard.title}"
            message = (
                f"Hazard '{hazard.title}' matched geofence '{geofence.name}'. "
                f"Event type: {hazard.event_type.value}. Severity: {hazard.severity.value}."
            )

            stats = {"total": 0, "sent": 0, "failed": 0}
            if self.notifier is not None:
                stats = await self.notifier.broadcast_alert(
                    title=title,
                    message=message,
                    severity=hazard.severity.value,
                    target_roles=geofence.target_roles,
                    metadata={
                        "kind": "geofence_hazard_alert",
                        "hazard_layer_id": str(hazard.id),
                        "hazard_id": hazard.hazard_id,
                        "geofence_id": str(geofence.id),
                        "event_type": hazard.event_type.value,
                        "district": hazard.district,
                        "ward": hazard.ward,
                    },
                )

            await self.repository.create_alert_event(
                {
                    "geofence_id": str(geofence.id),
                    "hazard_layer_id": str(hazard.id),
                    "severity": hazard.severity.value,
                    "event_type": hazard.event_type.value,
                    "title": title,
                    "message": message,
                    "notification_stats": stats,
                    "metadata": {
                        "geofence_name": geofence.name,
                        "hazard_source": hazard.source.value,
                    },
                }
            )

            triggered += 1

        return {
            "matched": len(matched_geofences),
            "triggered": triggered,
            "skipped": skipped,
        }
