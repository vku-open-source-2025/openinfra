"""Unit tests for SITREP service workflow rules."""

from __future__ import annotations

from typing import Optional

import pytest

from app.core.exceptions import ValidationError
from app.domain.models.sitrep import Sitrep, SitrepCreate, SitrepDelta, SitrepUpdate, SitrepStatus
from app.domain.services.sitrep_service import SitrepService


class FakeSitrepRepository:
    """In-memory repository for SITREP service tests."""

    def __init__(self):
        self._items: dict[str, Sitrep] = {}

    async def create(self, payload: dict) -> Sitrep:
        sitrep_id = str(len(self._items) + 1)
        sitrep = Sitrep(**{**payload, "_id": sitrep_id})
        self._items[sitrep_id] = sitrep
        return sitrep

    async def find_by_id(self, sitrep_id: str) -> Optional[Sitrep]:
        return self._items.get(sitrep_id)

    async def update(self, sitrep_id: str, updates: dict) -> Optional[Sitrep]:
        current = self._items.get(sitrep_id)
        if not current:
            return None

        payload = current.model_dump(by_alias=True)
        payload.update(updates)
        payload["_id"] = sitrep_id
        updated = Sitrep(**payload)
        self._items[sitrep_id] = updated
        return updated

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
    ):
        sitreps = list(self._items.values())
        if emergency_event_id:
            sitreps = [s for s in sitreps if s.emergency_event_id == emergency_event_id]
        if status:
            sitreps = [s for s in sitreps if s.status.value == status]
        return sitreps[skip : skip + limit]

    async def append_delta(self, sitrep_id: str, delta: SitrepDelta) -> Optional[Sitrep]:
        current = self._items.get(sitrep_id)
        if not current:
            return None

        payload = current.model_dump(by_alias=True)
        payload["deltas"] = [*current.deltas, delta]
        payload["_id"] = sitrep_id
        updated = Sitrep(**payload)
        self._items[sitrep_id] = updated
        return updated


@pytest.mark.asyncio
async def test_publish_empty_sitrep_is_rejected():
    repository = FakeSitrepRepository()
    service = SitrepService(repository)

    created = await service.create_sitrep(
        SitrepCreate(
            emergency_event_id="ev-1",
            title="Initial SITREP",
        ),
        created_by="operator-1",
    )

    with pytest.raises(ValidationError):
        await service.publish_sitrep(str(created.id), published_by="operator-2")


@pytest.mark.asyncio
async def test_cannot_edit_snapshot_after_publish():
    repository = FakeSitrepRepository()
    service = SitrepService(repository)

    created = await service.create_sitrep(
        SitrepCreate(
            emergency_event_id="ev-2",
            title="SITREP v1",
            snapshot={"affected_people": 120},
        ),
        created_by="operator-1",
    )

    published = await service.publish_sitrep(str(created.id), published_by="operator-2")
    assert published.status == SitrepStatus.PUBLISHED

    with pytest.raises(ValidationError):
        await service.update_sitrep(
            str(created.id),
            SitrepUpdate(snapshot={"affected_people": 80}),
        )


@pytest.mark.asyncio
async def test_archived_sitrep_rejects_new_delta():
    repository = FakeSitrepRepository()
    service = SitrepService(repository)

    created = await service.create_sitrep(
        SitrepCreate(
            emergency_event_id="ev-3",
            title="Archive candidate",
            snapshot={"status": "contained"},
        ),
        created_by="operator-1",
    )

    archived = await service.update_sitrep(
        str(created.id),
        SitrepUpdate(status=SitrepStatus.ARCHIVED),
    )
    assert archived.status == SitrepStatus.ARCHIVED

    with pytest.raises(ValidationError):
        await service.append_delta(
            str(created.id),
            SitrepDelta(action_type="manual_update", changes={"note": "late delta"}),
        )
