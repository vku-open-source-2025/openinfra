"""Resource inventory and allocation service."""

from typing import List, Optional

from app.core.exceptions import NotFoundError
from app.domain.models.resource_unit import ResourceStatus, ResourceUnit, ResourceUnitCreate, ResourceUnitUpdate
from app.domain.repositories.resource_unit_repository import ResourceUnitRepository


class ResourceService:
    """Business logic for emergency resources."""

    def __init__(self, repository: ResourceUnitRepository):
        self.repository = repository

    async def create_resource(
        self,
        payload: ResourceUnitCreate,
        request_id: Optional[str] = None,
    ) -> ResourceUnit:
        """Create resource inventory entry."""
        data = payload.model_dump(exclude_unset=True)
        if request_id:
            data["metadata"] = {**data.get("metadata", {}), "request_id": request_id}
        return await self.repository.create(data)

    async def get_resource_by_id(self, resource_id: str) -> ResourceUnit:
        """Get resource by id."""
        resource = await self.repository.find_by_id(resource_id)
        if not resource:
            raise NotFoundError("ResourceUnit", resource_id)
        return resource

    async def list_resources(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        resource_type: Optional[str] = None,
        district: Optional[str] = None,
    ) -> List[ResourceUnit]:
        """List resource units with filters."""
        return await self.repository.list(skip, limit, status, resource_type, district)

    async def update_resource(
        self,
        resource_id: str,
        updates: ResourceUnitUpdate,
        request_id: Optional[str] = None,
    ) -> ResourceUnit:
        """Update resource details."""
        current = await self.get_resource_by_id(resource_id)
        update_payload = updates.model_dump(exclude_unset=True)

        existing_metadata = dict(current.metadata or {})
        incoming_metadata = update_payload.get("metadata")
        if incoming_metadata is not None:
            existing_metadata.update(incoming_metadata)
        if request_id:
            existing_metadata["request_id"] = request_id
        if incoming_metadata is not None or request_id:
            update_payload["metadata"] = existing_metadata

        updated = await self.repository.update(
            resource_id,
            update_payload,
        )
        if not updated:
            raise NotFoundError("ResourceUnit", resource_id)
        return updated

    async def set_resource_status(
        self,
        resource_id: str,
        status: ResourceStatus,
        request_id: Optional[str] = None,
    ) -> ResourceUnit:
        """Update resource status quickly from operations panel."""
        current = await self.get_resource_by_id(resource_id)
        updates = {"status": status.value}
        if request_id:
            updates["metadata"] = {**dict(current.metadata or {}), "request_id": request_id}

        updated = await self.repository.update(resource_id, updates)
        if not updated:
            raise NotFoundError("ResourceUnit", resource_id)
        return updated
