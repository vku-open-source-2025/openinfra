"""Local file storage implementation."""
import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from app.infrastructure.storage.storage_service import StorageService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class LocalStorageService(StorageService):
    """Local file storage service."""

    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file: UploadFile,
        bucket: str = "default",
        prefix: str = "",
        filename: Optional[str] = None
    ) -> str:
        """Upload file to local storage."""
        # Generate filename if not provided
        if not filename:
            ext = Path(file.filename).suffix if file.filename else ""
            filename = f"{uuid.uuid4()}{ext}"

        # Create directory structure
        upload_dir = self.base_path / bucket / prefix
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = upload_dir / filename
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        # Return relative path as URL
        relative_path = f"/uploads/{bucket}/{prefix}{filename}" if prefix else f"/uploads/{bucket}/{filename}"
        logger.info(f"Uploaded file to {file_path}")
        return relative_path

    async def delete_file(self, file_url: str) -> bool:
        """Delete file from local storage."""
        try:
            # Remove /uploads prefix if present
            if file_url.startswith("/uploads/"):
                file_path = self.base_path / file_url.replace("/uploads/", "")
            else:
                file_path = self.base_path / file_url

            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_url}: {e}")
            return False

    async def get_file_url(self, file_path: str) -> str:
        """Get public URL for file."""
        if file_path.startswith("/"):
            return file_path
        return f"/uploads/{file_path}"
