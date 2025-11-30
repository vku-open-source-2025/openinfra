"""QR code generation service."""
import qrcode
from io import BytesIO
from typing import Optional
import base64
import logging

logger = logging.getLogger(__name__)


class QRCodeService:
    """QR code generation service."""

    @staticmethod
    def generate_qr_code(
        data: str,
        size: int = 10,
        border: int = 4
    ) -> str:
        """Generate QR code as base64 encoded PNG."""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            raise

    @staticmethod
    def generate_asset_qr_code(asset_code: str, base_url: str = "https://openinfra.example.com") -> str:
        """Generate QR code for asset public info."""
        url = f"{base_url}/public/assets/{asset_code}"
        return QRCodeService.generate_qr_code(url)

    @staticmethod
    def generate_incident_qr_code(incident_number: str, base_url: str = "https://openinfra.example.com") -> str:
        """Generate QR code for incident reporting."""
        url = f"{base_url}/public/incidents/report?ref={incident_number}"
        return QRCodeService.generate_qr_code(url)
