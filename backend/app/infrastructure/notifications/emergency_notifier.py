"""Emergency notification helper for broadcast alerts."""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from app.domain.models.notification import NotificationChannel, NotificationCreate, NotificationType

if TYPE_CHECKING:
    from app.domain.services.notification_service import NotificationService
    from app.domain.services.user_service import UserService

logger = logging.getLogger(__name__)


class EmergencyNotifier:
    """Broadcast emergency notifications with ordered channel fallback."""

    def __init__(
        self,
        notification_service: "NotificationService",
        user_service: "UserService",
    ):
        self.notification_service = notification_service
        self.user_service = user_service
        self.last_user_attempts: Dict[str, Dict[str, Any]] = {}

    async def _collect_recipient_ids(self, target_roles: List[str]) -> Set[str]:
        """Collect unique active user IDs by role."""
        recipient_ids: Set[str] = set()
        for role in target_roles:
            users = await self.user_service.list_users(
                skip=0,
                limit=1000,
                role=role,
                status="active",
            )
            for user in users:
                if user.id:
                    recipient_ids.add(str(user.id))
        return recipient_ids

    async def broadcast_alert(
        self,
        title: str,
        message: str,
        severity: str = "high",
        target_roles: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Broadcast alert with fallback; per-user attempts are kept on this instance."""
        roles = target_roles or ["admin", "technician"]
        recipients = await self._collect_recipient_ids(roles)
        metadata_payload = metadata or {}
        request_id = metadata_payload.get("request_id")
        event_id = metadata_payload.get("event_id")

        fallback_channels = [
            NotificationChannel.PUSH,
            NotificationChannel.EMAIL,
            NotificationChannel.IN_APP,
        ]

        priority = "urgent" if severity == "critical" else "high"
        stats: Dict[str, Any] = {
            # `total` is kept for backward compatibility with existing callers.
            "total": len(recipients),
            "attempted": len(recipients),
            "sent": 0,
            "failed": 0,
            "fallback_used": 0,
        }
        delivery_summary: Dict[str, Any] = {
            "total_attempts": 0,
            "total_success": 0,
            "total_failure": 0,
            "channels": {
                channel.value: {
                    "attempts": 0,
                    "success": 0,
                    "failure": 0,
                }
                for channel in fallback_channels
            },
        }
        stats["delivery_summary"] = delivery_summary
        user_attempts: Dict[str, Dict[str, Any]] = {}

        for user_id in recipients:
            attempts: List[Dict[str, Any]] = []
            delivered = False

            for idx, channel in enumerate(fallback_channels):
                attempt_info: Dict[str, Any] = {
                    "channel": channel.value,
                    "attempt": idx + 1,
                    "status": "planned" if dry_run else "pending",
                }

                if dry_run:
                    attempts.append(attempt_info)
                    continue

                payload = NotificationCreate(
                    user_id=user_id,
                    type=NotificationType.SYSTEM,
                    title=title,
                    message=message,
                    priority=priority,
                    channels=[channel],
                    metadata={
                        "kind": "emergency_alert",
                        "severity": severity,
                        "fallback_channel": channel.value,
                        "fallback_attempt": idx + 1,
                        "fallback_chain": [c.value for c in fallback_channels],
                        **metadata_payload,
                    },
                )

                channel_metrics = delivery_summary["channels"][channel.value]
                channel_metrics["attempts"] += 1
                delivery_summary["total_attempts"] += 1

                try:
                    send_with_status = getattr(
                        self.notification_service,
                        "create_notification_with_delivery_status",
                        None,
                    )
                    if callable(send_with_status):
                        _, attempt_delivered = await send_with_status(payload)
                    else:
                        await self.notification_service.create_notification(payload)
                        attempt_delivered = True
                except Exception as exc:
                    logger.warning(
                        "Emergency delivery failed user=%s channel=%s request_id=%s event_id=%s err=%s",
                        user_id,
                        channel.value,
                        request_id,
                        event_id,
                        exc,
                    )
                    attempt_delivered = False
                    attempt_info["error"] = str(exc)

                attempt_info["status"] = "sent" if attempt_delivered else "failed"
                if attempt_delivered:
                    channel_metrics["success"] += 1
                    delivery_summary["total_success"] += 1
                else:
                    channel_metrics["failure"] += 1
                    delivery_summary["total_failure"] += 1
                attempts.append(attempt_info)

                if attempt_delivered:
                    delivered = True
                    if idx > 0:
                        stats["fallback_used"] += 1
                    break

            if dry_run:
                user_attempts[user_id] = {
                    "status": "dry_run",
                    "attempts": attempts,
                }
                continue

            if delivered:
                stats["sent"] += 1
                final_status = "sent"
            else:
                stats["failed"] += 1
                final_status = "failed"

            user_attempts[user_id] = {
                "status": final_status,
                "attempts": attempts,
            }

        self.last_user_attempts = user_attempts
        logger.info(
            "Emergency alert summary request_id=%s event_id=%s users=%s sent=%s failed=%s attempts=%s",
            request_id,
            event_id,
            stats["attempted"],
            stats["sent"],
            stats["failed"],
            delivery_summary["total_attempts"],
        )
        return stats
