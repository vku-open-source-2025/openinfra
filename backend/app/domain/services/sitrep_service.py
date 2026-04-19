"""Situation report (SITREP) service."""

from datetime import datetime
from typing import List, Optional

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.models.sitrep import Sitrep, SitrepCreate, SitrepDelta, SitrepStatus, SitrepUpdate
from app.domain.repositories.sitrep_repository import SitrepRepository


class SitrepService:
    """Business logic for SITREP workflows."""

    _ALLOWED_STATUS_TRANSITIONS = {
        SitrepStatus.DRAFT: {SitrepStatus.PUBLISHED, SitrepStatus.ARCHIVED},
        SitrepStatus.PUBLISHED: {SitrepStatus.ARCHIVED},
        SitrepStatus.ARCHIVED: set(),
    }

    def __init__(self, repository: SitrepRepository):
        self.repository = repository

    def _normalize_status(self, raw_status: Optional[object]) -> Optional[SitrepStatus]:
        """Normalize status value into enum for transition validation."""
        if raw_status is None:
            return None
        if isinstance(raw_status, SitrepStatus):
            return raw_status
        return SitrepStatus(str(raw_status))

    def _validate_status_transition(
        self,
        current_status: SitrepStatus,
        next_status: SitrepStatus,
    ):
        """Validate SITREP lifecycle transition."""
        if current_status == next_status:
            return

        allowed_next = self._ALLOWED_STATUS_TRANSITIONS.get(current_status, set())
        if next_status not in allowed_next:
            raise ValidationError(
                f"Invalid SITREP status transition: {current_status.value} -> {next_status.value}"
            )

    async def create_sitrep(
        self,
        payload: SitrepCreate,
        created_by: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Sitrep:
        """Create a new sitrep draft."""
        data = payload.model_dump(exclude_unset=True)
        if created_by:
            data["metadata"] = {**data.get("metadata", {}), "created_by": created_by}
        if request_id:
            data["metadata"] = {**data.get("metadata", {}), "request_id": request_id}
        return await self.repository.create(data)

    async def get_sitrep_by_id(self, sitrep_id: str) -> Sitrep:
        """Get sitrep by id."""
        sitrep = await self.repository.find_by_id(sitrep_id)
        if not sitrep:
            raise NotFoundError("Sitrep", sitrep_id)
        return sitrep

    async def list_sitreps(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Sitrep]:
        """List sitreps with filters."""
        return await self.repository.list(skip, limit, emergency_event_id, status)

    async def update_sitrep(
        self,
        sitrep_id: str,
        updates: SitrepUpdate,
        request_id: Optional[str] = None,
    ) -> Sitrep:
        """Update sitrep snapshot metadata."""
        current = await self.get_sitrep_by_id(sitrep_id)

        if current.status == SitrepStatus.ARCHIVED:
            raise ValidationError("Cannot update an archived SITREP")

        update_payload = updates.model_dump(exclude_unset=True)
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

        if (
            current.status == SitrepStatus.PUBLISHED
            and any(field in update_payload for field in ("title", "snapshot"))
        ):
            raise ValidationError("Cannot modify title/snapshot after SITREP is published")

        updated = await self.repository.update(
            sitrep_id,
            update_payload,
        )
        if not updated:
            raise NotFoundError("Sitrep", sitrep_id)
        return updated

    async def append_delta(self, sitrep_id: str, delta: SitrepDelta) -> Sitrep:
        """Append timeline delta entry."""
        current = await self.get_sitrep_by_id(sitrep_id)
        if current.status == SitrepStatus.ARCHIVED:
            raise ValidationError("Cannot append delta to an archived SITREP")

        updated = await self.repository.append_delta(sitrep_id, delta)
        if not updated:
            raise NotFoundError("Sitrep", sitrep_id)
        return updated

    async def publish_sitrep(
        self,
        sitrep_id: str,
        published_by: str,
        request_id: Optional[str] = None,
    ) -> Sitrep:
        """Publish a sitrep."""
        current = await self.get_sitrep_by_id(sitrep_id)
        self._validate_status_transition(current.status, SitrepStatus.PUBLISHED)

        if not current.snapshot and not current.deltas:
            raise ValidationError("Cannot publish empty SITREP")

        updates = {
            "status": SitrepStatus.PUBLISHED.value,
            "published_by": published_by,
            "published_at": datetime.utcnow(),
        }
        if request_id:
            updates["metadata"] = {**dict(current.metadata or {}), "request_id": request_id}

        updated = await self.repository.update(sitrep_id, updates)
        if not updated:
            raise NotFoundError("Sitrep", sitrep_id)
        return updated
