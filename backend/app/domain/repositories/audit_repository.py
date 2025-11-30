"""Audit repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.audit_log import AuditLog


class AuditRepository(ABC):
    """Audit repository interface."""

    @abstractmethod
    async def create(self, audit_data: dict) -> AuditLog:
        """Create audit log entry."""
        pass

    @abstractmethod
    async def get_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a resource."""
        pass

    @abstractmethod
    async def get_by_user(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a user."""
        pass
