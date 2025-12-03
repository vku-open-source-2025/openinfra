"""Audit log domain model."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class AuditLog(BaseModel):
    """Audit log entity."""
    id: Optional[str] = Field(validation_alias="_id", serialization_alias="id", default=None)
    user_id: Optional[str] = None
    username: Optional[str] = None
    user_role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Action
    action: str  # "create" | "read" | "update" | "delete" | "login" | "logout"
    resource_type: str  # "asset" | "user" | "maintenance" | "incident" | "budget"
    resource_id: Optional[str] = None

    # Details
    description: str
    changes: Dict[str, Any] = Field(default_factory=dict)  # {before: {}, after: {}}

    # Context
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    endpoint: Optional[str] = None
    http_method: Optional[str] = None

    # Result
    status: str = "success"  # "success" | "failure"
    error_message: Optional[str] = None

    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Compliance
    data_classification: Optional[str] = None  # "public" | "internal" | "confidential" | "restricted"
    retention_period: Optional[int] = None  # Days to retain
