"""File storage service interface."""
from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
from fastapi import UploadFile


class StorageService(ABC):
    """Storage service interface."""

    @abstractmethod
    async def upload_file(
        self,
        file: UploadFile,
        bucket: str,
        prefix: str = "",
        filename: Optional[str] = None
    ) -> str:
        """Upload file and return URL."""
        pass

    @abstractmethod
    async def delete_file(self, file_url: str) -> bool:
        """Delete file by URL."""
        pass

    @abstractmethod
    async def get_file_url(self, file_path: str) -> str:
        """Get public URL for file."""
        pass
