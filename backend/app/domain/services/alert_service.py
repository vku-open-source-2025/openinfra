"""Alert service for managing alerts."""

from typing import Optional, List, Any
from datetime import datetime
from app.domain.models.alert import Alert, AlertStatus, AlertSeverity
from app.domain.models.incident import (
    IncidentCreate,
    IncidentCategory,
    IncidentSeverity,
)
from app.domain.repositories.alert_repository import AlertRepository
from app.core.exceptions import NotFoundError
import logging

logger = logging.getLogger(__name__)


class AlertService:
    """Alert service for business logic."""

    def __init__(self, alert_repository: AlertRepository):
        self.repository = alert_repository

    def _map_alert_severity_to_incident_severity(
        self, alert_severity: AlertSeverity
    ) -> IncidentSeverity:
        """Map alert severity to incident severity."""
        mapping = {
            AlertSeverity.INFO: IncidentSeverity.LOW,
            AlertSeverity.WARNING: IncidentSeverity.MEDIUM,
            AlertSeverity.CRITICAL: IncidentSeverity.HIGH,
            AlertSeverity.EMERGENCY: IncidentSeverity.CRITICAL,
        }
        return mapping.get(alert_severity, IncidentSeverity.MEDIUM)

    def _map_alert_type_to_incident_category(self, alert_type: str) -> IncidentCategory:
        """Map alert type to incident category."""
        mapping = {
            "threshold_exceeded": IncidentCategory.MALFUNCTION,
            "sensor_offline": IncidentCategory.MALFUNCTION,
            "maintenance_due": IncidentCategory.OTHER,
            "custom": IncidentCategory.OTHER,
        }
        return mapping.get(alert_type, IncidentCategory.OTHER)

    async def create_alert(self, alert: Alert) -> Alert:
        """Create a new alert."""
        alert_dict = alert.dict(exclude_unset=True)
        created_alert = await self.repository.create(alert_dict)
        logger.info(
            f"Created alert: {created_alert.alert_code} ({created_alert.severity})"
        )
        return created_alert

    async def get_alert_by_id(self, alert_id: str) -> Alert:
        """Get alert by ID."""
        alert = await self.repository.find_by_id(alert_id)
        if not alert:
            raise NotFoundError("Alert", alert_id)
        return alert

    async def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
        incident_service: Optional[Any] = None,
    ) -> Alert:
        """Acknowledge an alert and create corresponding incident."""
        alert = await self.get_alert_by_id(alert_id)

        # Create incident if incident_service is provided and alert doesn't already have an incident
        incident_id = None
        if incident_service and not alert.incident_created:
            try:
                # Map alert fields to incident fields
                incident_severity = self._map_alert_severity_to_incident_severity(
                    alert.severity
                )
                incident_category = self._map_alert_type_to_incident_category(
                    alert.type
                )

                # Create incident data
                incident_data = IncidentCreate(
                    asset_id=alert.asset_id,
                    title=alert.title,
                    description=alert.message,
                    category=incident_category,
                    severity=incident_severity,
                    reported_via="system",
                    public_visible=True,
                )

                # Create incident
                incident = await incident_service.create_incident(
                    incident_data, reported_by=acknowledged_by, reporter_type="system"
                )

                incident_id = incident.id
                logger.info(
                    f"Created incident {incident.incident_number} from alert {alert.alert_code}"
                )
            except Exception as e:
                logger.error(f"Failed to create incident from alert {alert_id}: {e}")
                # Continue with alert acknowledgment even if incident creation fails

        # Update alert status and incident information
        update_data = {
            "status": AlertStatus.ACKNOWLEDGED.value,
            "acknowledged_at": datetime.utcnow(),
            "acknowledged_by": acknowledged_by,
        }

        if incident_id:
            update_data["incident_created"] = True
            update_data["incident_id"] = incident_id

        updated = await self.repository.update(alert_id, update_data)
        if not updated:
            raise NotFoundError("Alert", alert_id)
        return updated

    async def resolve_alert(
        self, alert_id: str, resolved_by: str, resolution_notes: Optional[str] = None
    ) -> Alert:
        """Resolve an alert."""
        _ = await self.get_alert_by_id(alert_id)  # Validate alert exists
        updated = await self.repository.update(
            alert_id,
            {
                "status": AlertStatus.RESOLVED.value,
                "resolved_at": datetime.utcnow(),
                "resolved_by": resolved_by,
                "resolution_notes": resolution_notes,
            },
        )
        if not updated:
            raise NotFoundError("Alert", alert_id)
        return updated

    async def dismiss_alert(self, alert_id: str, dismissed_by: str) -> Alert:
        """Dismiss an alert."""
        _ = await self.get_alert_by_id(alert_id)  # Validate alert exists
        updated = await self.repository.update(
            alert_id,
            {
                "status": AlertStatus.DISMISSED.value,
                "resolved_at": datetime.utcnow(),
                "resolved_by": dismissed_by,
            },
        )
        if not updated:
            raise NotFoundError("Alert", alert_id)
        return updated

    async def list_alerts(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> List[Alert]:
        """List alerts with filtering."""
        return await self.repository.list(skip, limit, status, severity, asset_id)
