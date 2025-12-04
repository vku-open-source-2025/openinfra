"""MinIO object storage implementation."""

import logging
from typing import Optional
from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error
from app.infrastructure.storage.storage_service import StorageService
from app.core.config import settings
import io

logger = logging.getLogger(__name__)


class MinIOStorageService(StorageService):
    """MinIO object storage service."""

    def __init__(self):
        """Initialize MinIO client."""
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
            region=settings.MINIO_REGION,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if it doesn't."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise

    async def upload_file(
        self,
        file: UploadFile,
        bucket: Optional[str] = None,
        prefix: str = "",
        filename: Optional[str] = None,
    ) -> str:
        """Upload file to MinIO."""
        bucket = bucket or self.bucket_name

        # Generate filename if not provided
        if not filename:
            ext = ""
            if file.filename:
                ext = "." + file.filename.split(".")[-1] if "." in file.filename else ""
            import uuid

            filename = f"{uuid.uuid4()}{ext}"

        # Construct object name with prefix
        object_name = f"{prefix}{filename}" if prefix else filename

        try:
            # Read file content
            content = await file.read()
            content_length = len(content)

            # Upload to MinIO
            self.client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=io.BytesIO(content),
                length=content_length,
                content_type=file.content_type or "application/octet-stream",
            )

            # Return URL (MinIO format)
            url = f"/{bucket}/{object_name}"
            logger.info(f"Uploaded file to MinIO: {bucket}/{object_name}")
            return url

        except S3Error as e:
            logger.error(f"Error uploading file to MinIO: {e}")
            raise

    async def delete_file(self, file_url: str) -> bool:
        """Delete file from MinIO."""
        try:
            # Parse URL format: /bucket/object_name
            if file_url.startswith("/"):
                parts = file_url[1:].split("/", 1)
                if len(parts) == 2:
                    bucket, object_name = parts
                else:
                    bucket = self.bucket_name
                    object_name = parts[0]
            else:
                bucket = self.bucket_name
                object_name = file_url

            self.client.remove_object(bucket, object_name)
            logger.info(f"Deleted file from MinIO: {bucket}/{object_name}")
            return True

        except S3Error as e:
            logger.error(f"Error deleting file from MinIO: {e}")
            return False

    async def get_file_url(self, file_path: str) -> str:
        """Get public URL for file."""
        # If using MinIO, construct URL
        if file_path.startswith("/"):
            return file_path

        # Otherwise, assume it's relative to bucket
        return f"/{self.bucket_name}/{file_path}"

    def get_presigned_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """Get presigned URL for temporary access."""
        try:
            from datetime import timedelta

            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(seconds=expires_seconds),
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
