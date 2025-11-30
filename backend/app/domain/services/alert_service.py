"""Alert service for managing alerts."""
from typing import Optional, List
from datetime import datetime
from app.domain.models.alert import Alert, AlertStatus
from app.domain.repositories.alert_repository import AlertRepository
from app.core.exceptions import NotFoundError
import logging

logger = logging.getLogger(__name__)


class AlertService:
    """Alert service for business logic."""

    def __init__(self, alert_repository: AlertRepository):
        self.repository = alert_repository

    async def create_alert(self, alert: Alert) -> Alert:
        """Create a new alert."""
        alert_dict = alert.dict(exclude_unset=True)
        created_alert = await self.repository.create(alert_dict)
        logger.info(f"Created alert: {created_alert.alert_code} ({created_alert.severity})")
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
        acknowledged_by: str
    ) -> Alert:
        """Acknowledge an alert."""
        alert = await self.get_alert_by_id(alert_id)
        updated = await self.repository.update(
            alert_id,
            {
                "status": AlertStatus.ACKNOWLEDGED.value,
                "acknowledged_at": datetime.utcnow(),
                "acknowledged_by": acknowledged_by
            }
        )
        if not updated:
            raise NotFoundError("Alert", alert_id)
        return updated

    async def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution_notes: Optional[str] = None
    ) -> Alert:
        """Resolve an alert."""
        alert = await self.get_alert_by_id(alert_id)
        updated = await self.repository.update(
            alert_id,
            {
                "status": AlertStatus.RESOLVED.value,
                "resolved_at": datetime.utcnow(),
                "resolved_by": resolved_by,
                "resolution_notes": resolution_notes
            }
        )
        if not updated:
            raise NotFoundError("Alert", alert_id)
        return updated

    async def dismiss_alert(
        self,
        alert_id: str,
        dismissed_by: str
    ) -> Alert:
        """Dismiss an alert."""
        alert = await self.get_alert_by_id(alert_id)
        updated = await self.repository.update(
            alert_id,
            {
                "status": AlertStatus.DISMISSED.value,
                "resolved_at": datetime.utcnow(),
                "resolved_by": dismissed_by
            }
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
        asset_id: Optional[str] = None
    ) -> List[Alert]:
        """List alerts with filtering."""
        return await self.repository.list(skip, limit, status, severity, asset_id)
