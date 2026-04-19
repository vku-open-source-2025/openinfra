"""Notifications API router."""
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from app.domain.models.notification import Notification
from app.domain.services.notification_service import NotificationService
from app.domain.services.user_service import UserService
from app.api.v1.dependencies import get_notification_service, get_user_service
from app.api.v1.middleware import get_current_user
from app.domain.models.user import User
from app.infrastructure.notifications.emergency_notifier import EmergencyNotifier

router = APIRouter()


class EmergencyAlertRequest(BaseModel):
    """Payload for broadcasting emergency alerts to operator groups."""

    title: str = Field(min_length=3, max_length=140)
    message: str = Field(min_length=5, max_length=2000)
    severity: Literal["low", "medium", "high", "critical"] = "high"
    target_roles: List[str] = Field(default_factory=lambda: ["admin", "technician"])
    metadata: Optional[dict] = None


@router.get("", response_model=List[Notification])
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Get user's notifications."""
    return await notification_service.get_user_notifications(
        str(current_user.id),
        skip,
        limit,
        unread_only
    )


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Get count of unread notifications."""
    count = await notification_service.get_unread_count(str(current_user.id))
    return {"unread_count": count}


@router.post("/{notification_id}/read", response_model=Notification)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Mark notification as read."""
    notification = await notification_service.mark_as_read(notification_id)
    # Verify ownership
    if notification.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    return notification


@router.post("/mark-all-read")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Mark all notifications as read."""
    await notification_service.mark_all_as_read(str(current_user.id))
    return {"message": "All notifications marked as read"}


@router.post("/emergency-alert")
async def send_emergency_alert(
    payload: EmergencyAlertRequest,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
    user_service: UserService = Depends(get_user_service),
):
    """Broadcast emergency alert to selected user roles."""
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    notifier = EmergencyNotifier(notification_service, user_service)
    stats = await notifier.broadcast_alert(
        title=payload.title,
        message=payload.message,
        severity=payload.severity,
        target_roles=payload.target_roles,
        metadata=payload.metadata,
    )
    return {
        "message": "Emergency alert dispatched",
        "stats": stats,
    }
