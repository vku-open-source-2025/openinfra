"""Alerts API router."""

from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from app.domain.models.alert import Alert
from app.domain.services.alert_service import AlertService
from app.domain.services.incident_service import IncidentService
from app.api.v1.dependencies import get_alert_service, get_incident_service
from app.api.v1.middleware import get_current_user
from app.domain.models.user import User
from pydantic import BaseModel

router = APIRouter()


class AlertAcknowledgeRequest(BaseModel):
    """Alert acknowledge request schema."""

    pass


class AlertResolveRequest(BaseModel):
    """Alert resolve request schema."""

    resolution_notes: Optional[str] = None


@router.get("", response_model=List[Alert])
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    asset_id: Optional[str] = None,
    alert_service: AlertService = Depends(get_alert_service),
):
    """List alerts with filtering."""
    return await alert_service.list_alerts(skip, limit, status, severity, asset_id)


@router.get("/{alert_id}", response_model=Alert)
async def get_alert(
    alert_id: str, alert_service: AlertService = Depends(get_alert_service)
):
    """Get alert details."""
    return await alert_service.get_alert_by_id(alert_id)


@router.post("/{alert_id}/acknowledge", response_model=Alert)
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service),
    incident_service: IncidentService = Depends(get_incident_service),
):
    """Acknowledge an alert and create corresponding incident."""
    return await alert_service.acknowledge_alert(
        alert_id, str(current_user.id), incident_service=incident_service
    )


@router.post("/{alert_id}/resolve", response_model=Alert)
async def resolve_alert(
    alert_id: str,
    request: AlertResolveRequest,
    current_user: User = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service),
):
    """Resolve an alert."""
    return await alert_service.resolve_alert(
        alert_id, str(current_user.id), request.resolution_notes
    )


@router.post("/{alert_id}/dismiss", response_model=Alert)
async def dismiss_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service),
):
    """Dismiss an alert."""
    return await alert_service.dismiss_alert(alert_id, str(current_user.id))
