"""SMS notification service (Twilio integration)."""
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class SMSService:
    """SMS notification service using Twilio."""

    def __init__(self):
        self.account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
        self.auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
        self.from_number = getattr(settings, "TWILIO_FROM_NUMBER", "")
        self.enabled = bool(self.account_sid and self.auth_token)

    async def send_sms(
        self,
        to_number: str,
        message: str
    ) -> bool:
        """Send SMS notification."""
        try:
            if not self.enabled:
                logger.warning("Twilio credentials not configured, skipping SMS")
                return False

            # Import Twilio client
            try:
                from twilio.rest import Client
            except ImportError:
                logger.error("twilio package not installed. Install with: pip install twilio")
                return False

            client = Client(self.account_sid, self.auth_token)

            message = client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )

            logger.info(f"SMS sent to {to_number}, SID: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Error sending SMS to {to_number}: {e}")
            return False
