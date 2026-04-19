"""Emergency service for command-center workflows."""

import uuid
from datetime import datetime
from typing import List, Optional

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.models.emergency import (
    EmergencyEvent,
    EmergencyEventCreate,
    EmergencyEventUpdate,
    EmergencyStatus,
)
from app.domain.repositories.emergency_repository import EmergencyRepository


class EmergencyService:
    """Emergency service containing emergency business logic."""

    _ALLOWED_STATUS_TRANSITIONS = {
        EmergencyStatus.MONITORING: {EmergencyStatus.ACTIVE, EmergencyStatus.CANCELED},
        EmergencyStatus.ACTIVE: {
            EmergencyStatus.CONTAINED,
            EmergencyStatus.RESOLVED,
            EmergencyStatus.CANCELED,
        },
        EmergencyStatus.CONTAINED: {
            EmergencyStatus.ACTIVE,
            EmergencyStatus.RESOLVED,
            EmergencyStatus.CANCELED,
        },
        EmergencyStatus.RESOLVED: set(),
        EmergencyStatus.CANCELED: set(),
    }

    def __init__(self, emergency_repository: EmergencyRepository):
        self.repository = emergency_repository

    def _generate_event_code(self) -> str:
        """Generate a stable event code for operators."""
        suffix = uuid.uuid4().hex[:6].upper()
        return f"EMG-{datetime.utcnow():%Y%m%d}-{suffix}"

    def _normalize_status(self, raw_status: Optional[object]) -> Optional[EmergencyStatus]:
        """Normalize status value to enum for transition checks."""
        if raw_status is None:
            return None
        if isinstance(raw_status, EmergencyStatus):
            return raw_status
        return EmergencyStatus(str(raw_status))

    def _validate_status_transition(
        self,
        current_status: EmergencyStatus,
        next_status: EmergencyStatus,
    ):
        """Ensure emergency state transition respects lifecycle rules."""
        if current_status == next_status:
            return

        allowed_next = self._ALLOWED_STATUS_TRANSITIONS.get(current_status, set())
        if next_status not in allowed_next:
            raise ValidationError(
                f"Invalid emergency status transition: {current_status.value} -> {next_status.value}"
            )

    async def create_event(
        self,
        event_data: EmergencyEventCreate,
        created_by: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> EmergencyEvent:
        """Create an emergency event."""
        payload = event_data.model_dump(exclude_unset=True)
        payload["event_code"] = self._generate_event_code()
        payload["created_by"] = created_by
        payload["updated_by"] = created_by
        if request_id:
            payload["metadata"] = {**payload.get("metadata", {}), "request_id": request_id}

        if payload.get("status") == EmergencyStatus.ACTIVE.value and not payload.get(
            "started_at"
        ):
            payload["started_at"] = datetime.utcnow()

        return await self.repository.create(payload)

    async def get_event_by_id(self, event_id: str) -> EmergencyEvent:
        """Get emergency event by ID."""
        event = await self.repository.find_by_id(event_id)
        if not event:
            raise NotFoundError("EmergencyEvent", event_id)
        return event

    async def list_events(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        query_text: Optional[str] = None,
    ) -> List[EmergencyEvent]:
        """List emergency events with optional filters."""
        return await self.repository.list(
            skip=skip,
            limit=limit,
            status=status,
            severity=severity,
            event_type=event_type,
            query_text=query_text,
        )

    async def update_event(
        self,
        event_id: str,
        updates: EmergencyEventUpdate,
        updated_by: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> EmergencyEvent:
        """Update an emergency event."""
        current = await self.get_event_by_id(event_id)

        update_payload = updates.model_dump(exclude_unset=True)
        update_payload["updated_by"] = updated_by

        existing_metadata = dict(current.metadata or {})
        incoming_metadata = update_payload.get("metadata")
        if incoming_metadata is not None:
            existing_metadata.update(incoming_metadata)
        if request_id:
            existing_metadata["request_id"] = request_id
        if incoming_metadata is not None or request_id:
            update_payload["metadata"] = existing_metadata

        next_status = self._normalize_status(update_payload.get("status"))
        if (
            next_status == EmergencyStatus.ACTIVE
            and not current.started_at
            and "started_at" not in update_payload
        ):
            update_payload["started_at"] = datetime.utcnow()

        if (
            next_status is not None
            and next_status != current.status
        ):
            self._validate_status_transition(current.status, next_status)

        if (
            next_status in {EmergencyStatus.RESOLVED, EmergencyStatus.CANCELED}
            and "ended_at" not in update_payload
        ):
            update_payload["ended_at"] = datetime.utcnow()

        updated = await self.repository.update(event_id, update_payload)
        if not updated:
            raise NotFoundError("EmergencyEvent", event_id)

        return updated

    async def resolve_event(
        self,
        event_id: str,
        resolution_note: Optional[str],
        updated_by: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> EmergencyEvent:
        """Resolve an emergency event quickly from operator actions."""
        event = await self.get_event_by_id(event_id)

        if event.status in {EmergencyStatus.RESOLVED, EmergencyStatus.CANCELED}:
            raise ValidationError(
                f"Cannot resolve emergency event in status '{event.status.value}'"
            )

        self._validate_status_transition(event.status, EmergencyStatus.RESOLVED)

        metadata = dict(event.metadata or {})

        if resolution_note:
            metadata["resolution_note"] = resolution_note
        if request_id:
            metadata["request_id"] = request_id

        updates = EmergencyEventUpdate(
            status=EmergencyStatus.RESOLVED,
            ended_at=datetime.utcnow(),
            metadata=metadata,
        )
        return await self.update_event(
            event_id,
            updates,
            updated_by=updated_by,
            request_id=request_id,
        )
