"""Dispatch order service."""

from datetime import datetime
from typing import List, Optional

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.models.dispatch_order import (
    DispatchOrder,
    DispatchOrderCreate,
    DispatchOrderUpdate,
    DispatchStatus,
)
from app.domain.repositories.dispatch_order_repository import DispatchOrderRepository


class DispatchService:
    """Business logic for dispatch operations."""

    _ALLOWED_STATUS_TRANSITIONS = {
        DispatchStatus.PENDING: {DispatchStatus.ASSIGNED, DispatchStatus.CANCELED},
        DispatchStatus.ASSIGNED: {
            DispatchStatus.IN_TRANSIT,
            DispatchStatus.ON_SCENE,
            DispatchStatus.COMPLETED,
            DispatchStatus.REASSIGNED,
            DispatchStatus.CANCELED,
        },
        DispatchStatus.IN_TRANSIT: {
            DispatchStatus.ON_SCENE,
            DispatchStatus.COMPLETED,
            DispatchStatus.REASSIGNED,
            DispatchStatus.CANCELED,
        },
        DispatchStatus.ON_SCENE: {
            DispatchStatus.COMPLETED,
            DispatchStatus.REASSIGNED,
            DispatchStatus.CANCELED,
        },
        DispatchStatus.REASSIGNED: {DispatchStatus.ASSIGNED, DispatchStatus.CANCELED},
        DispatchStatus.COMPLETED: set(),
        DispatchStatus.CANCELED: set(),
    }

    def __init__(self, repository: DispatchOrderRepository):
        self.repository = repository

    def _normalize_status(self, raw_status: Optional[object]) -> Optional[DispatchStatus]:
        """Normalize status value into enum for transition validation."""
        if raw_status is None:
            return None
        if isinstance(raw_status, DispatchStatus):
            return raw_status
        return DispatchStatus(str(raw_status))

    def _validate_status_transition(
        self,
        current_status: DispatchStatus,
        next_status: DispatchStatus,
    ):
        """Ensure dispatch status transitions follow lifecycle rules."""
        if current_status == next_status:
            return

        allowed_next = self._ALLOWED_STATUS_TRANSITIONS.get(current_status, set())
        if next_status not in allowed_next:
            raise ValidationError(
                f"Invalid dispatch status transition: {current_status.value} -> {next_status.value}"
            )

    async def create_order(
        self,
        payload: DispatchOrderCreate,
        assigned_by: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> DispatchOrder:
        """Create a new dispatch order."""
        data = payload.model_dump(exclude_unset=True)
        if assigned_by:
            data["assigned_by"] = assigned_by
        if request_id:
            data["metadata"] = {**data.get("metadata", {}), "request_id": request_id}
        return await self.repository.create(data)

    async def get_order_by_id(self, order_id: str) -> DispatchOrder:
        """Get dispatch order by id."""
        order = await self.repository.find_by_id(order_id)
        if not order:
            raise NotFoundError("DispatchOrder", order_id)
        return order

    async def list_orders(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List[DispatchOrder]:
        """List dispatch orders with filters."""
        return await self.repository.list(
            skip=skip,
            limit=limit,
            emergency_event_id=emergency_event_id,
            status=status,
            priority=priority,
        )

    async def update_order(
        self,
        order_id: str,
        updates: DispatchOrderUpdate,
        updated_by: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> DispatchOrder:
        """Update dispatch order details."""
        current = await self.get_order_by_id(order_id)

        update_payload = updates.model_dump(exclude_unset=True)
        if updated_by:
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
        if next_status is not None:
            self._validate_status_transition(current.status, next_status)

            if next_status == DispatchStatus.ASSIGNED and "started_at" not in update_payload:
                update_payload["started_at"] = datetime.utcnow()

            if next_status == DispatchStatus.COMPLETED and "completed_at" not in update_payload:
                update_payload["completed_at"] = datetime.utcnow()

        if (
            current.status in {DispatchStatus.COMPLETED, DispatchStatus.CANCELED}
            and any(
                key in update_payload
                for key in (
                    "task_title",
                    "task_description",
                    "target_location",
                    "priority",
                    "assignments",
                    "eta_minutes",
                )
            )
        ):
            raise ValidationError(
                f"Cannot modify immutable fields for dispatch order in status '{current.status.value}'"
            )

        updated = await self.repository.update(order_id, update_payload)
        if not updated:
            raise NotFoundError("DispatchOrder", order_id)
        return updated

    async def assign_order(
        self,
        order_id: str,
        updated_by: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> DispatchOrder:
        """Mark order as assigned and set start timestamp."""
        current = await self.get_order_by_id(order_id)
        self._validate_status_transition(current.status, DispatchStatus.ASSIGNED)

        updates = {
            "status": DispatchStatus.ASSIGNED.value,
            "started_at": datetime.utcnow(),
        }
        if updated_by:
            updates["updated_by"] = updated_by
        if request_id:
            updates["metadata"] = {**dict(current.metadata or {}), "request_id": request_id}

        updated = await self.repository.update(order_id, updates)
        if not updated:
            raise NotFoundError("DispatchOrder", order_id)
        return updated

    async def complete_order(
        self,
        order_id: str,
        updated_by: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> DispatchOrder:
        """Mark order as completed."""
        current = await self.get_order_by_id(order_id)
        self._validate_status_transition(current.status, DispatchStatus.COMPLETED)

        updates = {
            "status": DispatchStatus.COMPLETED.value,
            "completed_at": datetime.utcnow(),
        }
        if updated_by:
            updates["updated_by"] = updated_by
        if request_id:
            updates["metadata"] = {**dict(current.metadata or {}), "request_id": request_id}

        updated = await self.repository.update(order_id, updates)
        if not updated:
            raise NotFoundError("DispatchOrder", order_id)
        return updated
