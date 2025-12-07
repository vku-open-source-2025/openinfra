"""Cloudflare Turnstile verification service."""
import httpx
from typing import Optional
from app.core.config import settings


class TurnstileService:
    """Service for verifying Cloudflare Turnstile captcha tokens."""

    @staticmethod
    async def verify_token(token: str, remote_ip: Optional[str] = None) -> bool:
        """
        Verify a Turnstile token with Cloudflare.
        
        Args:
            token: The turnstile response token from the client
            remote_ip: Optional client IP address for additional validation
            
        Returns:
            True if token is valid, False otherwise
        """
        if not settings.TURNSTILE_SECRET_KEY:
            # If no secret key configured, skip verification (development mode)
            return True

        payload = {
            "secret": settings.TURNSTILE_SECRET_KEY,
            "response": token,
        }
        
        if remote_ip:
            payload["remoteip"] = remote_ip

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.TURNSTILE_VERIFY_URL,
                    data=payload,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    return False
                
                result = response.json()
                return result.get("success", False)
                
        except Exception as e:
            # Log the error in production
            print(f"Turnstile verification error: {e}")
            return False


# Singleton instance
turnstile_service = TurnstileService()
