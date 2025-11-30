"""Audit service for logging changes."""
from typing import Optional, Dict, Any
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.models.audit_log import AuditLog
import logging

logger = logging.getLogger(__name__)


class AuditService:
    """Audit service for tracking changes."""

    def __init__(self, audit_repository: AuditRepository):
        self.repository = audit_repository

    async def log_change(
        self,
        resource_type: str,
        resource_id: str,
        action: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        user_role: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        request_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        http_method: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Log a change to a resource."""
        if not description:
            description = f"{action.capitalize()} {resource_type} {resource_id}"

        audit_data = {
            "user_id": user_id,
            "username": username,
            "user_role": user_role,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "description": description,
            "changes": changes or {},
            "request_id": request_id,
            "endpoint": endpoint,
            "http_method": http_method,
            "status": status,
            "error_message": error_message
        }

        try:
            return await self.repository.create(audit_data)
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            raise

    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100
    ) -> list[AuditLog]:
        """Get change history for a resource."""
        return await self.repository.get_by_resource(resource_type, resource_id, limit)

    async def get_user_activity(
        self,
        user_id: str,
        limit: int = 100
    ) -> list[AuditLog]:
        """Get activity history for a user."""
        return await self.repository.get_by_user(user_id, limit)
