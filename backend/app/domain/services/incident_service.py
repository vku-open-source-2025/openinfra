"""Incident service for managing incidents."""
from typing import Optional, List
from datetime import datetime
from app.domain.models.incident import (
    Incident, IncidentCreate, IncidentUpdate, IncidentComment,
    IncidentStatus, ResolutionType
)
from app.domain.repositories.incident_repository import IncidentRepository
from app.domain.services.maintenance_service import MaintenanceService
from app.core.exceptions import NotFoundError, ConflictError
import logging
import uuid

logger = logging.getLogger(__name__)


class IncidentService:
    """Incident service for business logic."""

    def __init__(
        self,
        incident_repository: IncidentRepository,
        maintenance_service: Optional[MaintenanceService] = None,
        asset_service: Optional[Any] = None
    ):
        self.repository = incident_repository
        self.maintenance_service = maintenance_service
        self.asset_service = asset_service

    def _generate_incident_number(self) -> str:
        """Generate unique incident number."""
        year = datetime.utcnow().year
        # In production, get next sequence from database
        sequence = uuid.uuid4().hex[:6].upper()
        return f"INC-{year}-{sequence}"

    async def create_incident(
        self,
        incident_data: IncidentCreate,
        reported_by: Optional[str] = None,
        reporter_type: str = "citizen"
    ) -> Incident:
        """Create a new incident."""
        # Generate incident number
        incident_number = self._generate_incident_number()

        # Check if number exists (unlikely but possible)
        existing = await self.repository.find_by_number(incident_number)
        if existing:
            incident_number = self._generate_incident_number()  # Retry

        incident_dict = incident_data.dict(exclude_unset=True)
        
        # Populate location from asset if missing
        if incident_data.asset_id and not incident_data.location and self.asset_service:
            try:
                asset = await self.asset_service.get_asset_by_id(incident_data.asset_id)
                if asset:
                    # Construct location from asset
                    geometry = asset.geometry if asset.geometry else {"type": "Point", "coordinates": [0, 0]}
                    
                    # Get address from asset location if available
                    address = "Location not specified"
                    if asset.location and hasattr(asset.location, 'address'):
                        address = asset.location.address
                    elif asset.location and isinstance(asset.location, dict):
                        address = asset.location.get('address', "Location not specified")
                        
                    incident_dict["location"] = {
                        "geometry": geometry,
                        "address": address
                    }
            except Exception as e:
                logger.warning(f"Failed to fetch asset location for incident: {e}")

        incident_dict["incident_number"] = incident_number
        incident_dict["reported_by"] = reported_by
        incident_dict["reporter_type"] = reporter_type
        incident_dict["status"] = IncidentStatus.REPORTED.value

        incident = await self.repository.create(incident_dict)
        logger.info(f"Created incident: {incident.incident_number}")
        return incident

    async def get_incident_by_id(self, incident_id: str) -> Incident:
        """Get incident by ID."""
        incident = await self.repository.find_by_id(incident_id)
        if not incident:
            raise NotFoundError("Incident", incident_id)
        return incident

    async def acknowledge_incident(
        self,
        incident_id: str,
        acknowledged_by: str
    ) -> Incident:
        """Acknowledge an incident."""
        incident = await self.get_incident_by_id(incident_id)

        # Calculate response time
        response_time = None
        if incident.reported_at:
            delta = datetime.utcnow() - incident.reported_at
            response_time = int(delta.total_seconds() / 60)

        updated = await self.repository.update(
            incident_id,
            {
                "status": IncidentStatus.ACKNOWLEDGED.value,
                "acknowledged_at": datetime.utcnow(),
                "acknowledged_by": acknowledged_by,
                "response_time_minutes": response_time
            }
        )
        if not updated:
            raise NotFoundError("Incident", incident_id)
        return updated

    async def assign_incident(
        self,
        incident_id: str,
        assigned_to: str,
        assigned_by: str
    ) -> Incident:
        """Assign incident to a technician."""
        incident = await self.get_incident_by_id(incident_id)

        # Auto-create maintenance record if linked to an asset
        if incident.asset_id:
            try:
                maintenance_id = await self.create_maintenance_from_incident(incident_id, assigned_by)
                
                # Assign the maintenance to the technician as well
                if self.maintenance_service:
                    await self.maintenance_service.assign_maintenance(maintenance_id, assigned_to, assigned_by)
                    
                update_data = {
                    "assigned_to": assigned_to,
                    "status": IncidentStatus.INVESTIGATING.value,
                    "updated_at": datetime.utcnow(),
                    "maintenance_record_id": maintenance_id
                }
            except Exception as e:
                logger.error(f"Failed to create maintenance for incident {incident_id}: {e}")
                # Fallback to just assigning the incident without maintenance (or raise error based on policy)
                update_data = {
                    "assigned_to": assigned_to,
                    "status": IncidentStatus.INVESTIGATING.value,
                    "updated_at": datetime.utcnow()
                }
        else:
            update_data = {
                "assigned_to": assigned_to,
                "status": IncidentStatus.INVESTIGATING.value,
                "updated_at": datetime.utcnow()
            }

        updated = await self.repository.update(incident_id, update_data)
        if not updated:
            raise NotFoundError("Incident", incident_id)

        # Add internal comment
        await self.add_comment(
            incident_id,
            f"Incident assigned to technician by {assigned_by}",
            assigned_by,
            is_internal=True
        )

        return updated

    async def approve_incident_resolution(
        self,
        incident_id: str,
        approved_by: str
    ) -> Incident:
        """Approve cost/resolution of linked maintenance and resolve incident."""
        incident = await self.get_incident_by_id(incident_id)

        if not incident.maintenance_record_id:
             raise ValidationError("Incident has no linked maintenance record to approve")

        if self.maintenance_service:
            # Approve the maintenance record
            await self.maintenance_service.approve_resolution(incident.maintenance_record_id, approved_by)
            
            # Resolve the incident
            return await self.resolve_incident(
                incident_id, 
                approved_by, 
                "Resolution approved by admin via maintenance cost approval.", 
                ResolutionType.FIXED
            )
        else:
             raise RuntimeError("Maintenance service not available")

    async def resolve_incident(
        self,
        incident_id: str,
        resolved_by: str,
        resolution_notes: str,
        resolution_type: ResolutionType
    ) -> Incident:
        """Resolve an incident."""
        incident = await self.get_incident_by_id(incident_id)

        # Calculate resolution time
        resolution_time = None
        if incident.reported_at:
            delta = datetime.utcnow() - incident.reported_at
            resolution_time = int(delta.total_seconds() / 60)

        updated = await self.repository.update(
            incident_id,
            {
                "status": IncidentStatus.RESOLVED.value,
                "resolved_at": datetime.utcnow(),
                "resolved_by": resolved_by,
                "resolution_notes": resolution_notes,
                "resolution_type": resolution_type.value,
                "resolution_time_minutes": resolution_time
            }
        )
        if not updated:
            raise NotFoundError("Incident", incident_id)
        return updated

    async def create_maintenance_from_incident(
        self,
        incident_id: str,
        created_by: str
    ) -> str:
        """Create a maintenance work order from incident."""
        incident = await self.get_incident_by_id(incident_id)

        if not incident.asset_id:
            raise ValueError("Incident must be linked to an asset to create maintenance")

        if self.maintenance_service:
            # Create maintenance record
            from app.domain.models.maintenance import MaintenanceCreate, MaintenancePriority, MaintenanceType
            priority = MaintenancePriority.HIGH if incident.severity.value in ["high", "critical"] else MaintenancePriority.MEDIUM
            maintenance_data = MaintenanceCreate(
                asset_id=incident.asset_id,
                type=MaintenanceType.CORRECTIVE,
                priority=priority,
                title=f"Maintenance for incident {incident.incident_number}",
                description=f"Maintenance created from incident {incident.incident_number}: {incident.description}",
                scheduled_date=datetime.utcnow(),
                estimated_duration=120  # Default 2 hours
            )
            maintenance = await self.maintenance_service.create_maintenance(maintenance_data, created_by)

            # Link maintenance to incident
            await self.repository.update(
                incident_id,
                {"maintenance_record_id": str(maintenance.id)}
            )

            return str(maintenance.id)
        else:
            raise RuntimeError("Maintenance service not available")

    async def add_comment(
        self,
        incident_id: str,
        comment_text: str,
        user_id: Optional[str],
        is_internal: bool = False
    ) -> Incident:
        """Add comment to incident."""
        comment = IncidentComment(
            user_id=user_id,
            comment=comment_text,
            posted_at=datetime.utcnow(),
            is_internal=is_internal
        )

        await self.repository.add_comment(incident_id, comment.dict())
        return await self.get_incident_by_id(incident_id)

    async def upvote_incident(
        self,
        incident_id: str,
        user_id: str
    ) -> Incident:
        """Upvote or remove upvote from incident."""
        await self.repository.upvote(incident_id, user_id)
        return await self.get_incident_by_id(incident_id)

    async def list_incidents(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        asset_id: Optional[str] = None,
        reported_by: Optional[str] = None
    ) -> List[Incident]:
        """List incidents with filtering."""
        return await self.repository.list(skip, limit, status, severity, asset_id, reported_by)

    async def update_incident(
        self,
        incident_id: str,
        updates: IncidentUpdate
    ) -> Incident:
        """Update incident."""
        update_dict = updates.dict(exclude_unset=True)
        updated = await self.repository.update(incident_id, update_dict)
        if not updated:
            raise NotFoundError("Incident", incident_id)
        return updated
