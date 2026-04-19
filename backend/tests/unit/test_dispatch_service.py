"""Unit tests for dispatch service workflow rules."""

from __future__ import annotations

from typing import Optional

import pytest

from app.core.exceptions import ValidationError
from app.domain.models.dispatch_order import (
    DispatchOrder,
    DispatchOrderCreate,
    DispatchOrderUpdate,
    DispatchStatus,
)
from app.domain.services.dispatch_service import DispatchService


class FakeDispatchOrderRepository:
    """In-memory repository for dispatch service tests."""

    def __init__(self):
        self._items: dict[str, DispatchOrder] = {}

    async def create(self, payload: dict) -> DispatchOrder:
        order_id = str(len(self._items) + 1)
        order = DispatchOrder(**{**payload, "_id": order_id})
        self._items[order_id] = order
        return order

    async def find_by_id(self, order_id: str) -> Optional[DispatchOrder]:
        return self._items.get(order_id)

    async def update(self, order_id: str, updates: dict) -> Optional[DispatchOrder]:
        current = self._items.get(order_id)
        if not current:
            return None

        payload = current.model_dump(by_alias=True)
        payload.update(updates)
        payload["_id"] = order_id
        updated = DispatchOrder(**payload)
        self._items[order_id] = updated
        return updated

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ):
        orders = list(self._items.values())
        if emergency_event_id:
            orders = [order for order in orders if order.emergency_event_id == emergency_event_id]
        if status:
            orders = [order for order in orders if order.status.value == status]
        if priority:
            orders = [order for order in orders if order.priority.value == priority]
        return orders[skip : skip + limit]


@pytest.mark.asyncio
async def test_cannot_complete_dispatch_order_directly_from_pending():
    repository = FakeDispatchOrderRepository()
    service = DispatchService(repository)

    created = await service.create_order(
        DispatchOrderCreate(
            emergency_event_id="ev-1",
            task_title="Evacuate Sector A",
            priority="high",
        ),
        assigned_by="operator-1",
    )

    with pytest.raises(ValidationError):
        await service.complete_order(str(created.id), updated_by="operator-2")


@pytest.mark.asyncio
async def test_assign_then_complete_dispatch_order():
    repository = FakeDispatchOrderRepository()
    service = DispatchService(repository)

    created = await service.create_order(
        DispatchOrderCreate(
            emergency_event_id="ev-2",
            task_title="Deploy rescue boat",
            priority="critical",
        ),
        assigned_by="operator-1",
    )

    assigned = await service.assign_order(str(created.id), updated_by="operator-2")
    assert assigned.status == DispatchStatus.ASSIGNED
    assert assigned.started_at is not None

    completed = await service.complete_order(str(created.id), updated_by="operator-3")
    assert completed.status == DispatchStatus.COMPLETED
    assert completed.completed_at is not None


@pytest.mark.asyncio
async def test_cannot_edit_core_fields_after_dispatch_completion():
    repository = FakeDispatchOrderRepository()
    service = DispatchService(repository)

    created = await service.create_order(
        DispatchOrderCreate(
            emergency_event_id="ev-3",
            task_title="Clear blocked road",
            priority="medium",
        ),
        assigned_by="operator-1",
    )

    await service.assign_order(str(created.id), updated_by="operator-2")
    await service.complete_order(str(created.id), updated_by="operator-3")

    with pytest.raises(ValidationError):
        await service.update_order(
            str(created.id),
            DispatchOrderUpdate(task_title="Updated title after completion"),
            updated_by="operator-4",
        )
