"""Notifications API router."""
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import List
from app.domain.models.notification import Notification
from app.domain.services.notification_service import NotificationService
from app.api.v1.dependencies import get_notification_service
from app.api.v1.middleware import get_current_user
from app.domain.models.user import User

router = APIRouter()


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
