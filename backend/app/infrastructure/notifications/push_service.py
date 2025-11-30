"""Push notification service (Firebase Cloud Messaging)."""
from typing import Optional, List
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class PushService:
    """Push notification service using FCM."""

    def __init__(self):
        self.fcm_server_key = getattr(settings, "FCM_SERVER_KEY", "")
        self.enabled = bool(self.fcm_server_key)

    async def send_push(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> dict:
        """Send push notification to devices."""
        try:
            if not self.enabled:
                logger.warning("FCM server key not configured, skipping push notification")
                return {"success": 0, "failure": len(device_tokens)}

            # Import FCM client
            try:
                from pyfcm import FCMNotification
            except ImportError:
                logger.error("pyfcm package not installed. Install with: pip install pyfcm")
                return {"success": 0, "failure": len(device_tokens)}

            push_service = FCMNotification(api_key=self.fcm_server_key)

            result = push_service.notify_multiple_devices(
                registration_ids=device_tokens,
                message_title=title,
                message_body=body,
                data_message=data or {}
            )

            logger.info(f"Push notification sent to {len(device_tokens)} devices")
            return {
                "success": result.get("success", 0),
                "failure": result.get("failure", 0)
            }
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return {"success": 0, "failure": len(device_tokens)}
