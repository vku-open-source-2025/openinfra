"""Incident service for managing incidents."""
from typing import Optional, List, Any
from datetime import datetime
from app.domain.models.incident import (
    Incident, IncidentCreate, IncidentUpdate, IncidentComment,
    IncidentStatus, ResolutionType
)
from app.domain.models.merge_suggestion import MergeSuggestion, MergeSuggestionStatus
from app.domain.repositories.incident_repository import IncidentRepository
from app.domain.services.maintenance_service import MaintenanceService
from app.domain.services.duplicate_detection_service import DuplicateDetectionService
from app.domain.services.incident_merge_service import IncidentMergeService
from app.infrastructure.database.repositories.mongo_merge_suggestion_repository import MongoMergeSuggestionRepository
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
from app.core.config import settings
import logging
import uuid

logger = logging.getLogger(__name__)


class IncidentService:
    """Incident service for business logic."""

    def __init__(
        self,
        incident_repository: IncidentRepository,
        maintenance_service: Optional[MaintenanceService] = None,
        asset_service: Optional[Any] = None,
        duplicate_detection_service: Optional[DuplicateDetectionService] = None,
        merge_service: Optional[IncidentMergeService] = None,
        merge_suggestion_repository: Optional[MongoMergeSuggestionRepository] = None
    ):
        self.repository = incident_repository
        self.maintenance_service = maintenance_service
        self.asset_service = asset_service
        self.duplicate_detection_service = duplicate_detection_service
        self.merge_service = merge_service
        self.merge_suggestion_repository = merge_suggestion_repository

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

        # Check for duplicates and create merge suggestions (async, don't block)
        # Only create suggestion if incident has required fields
        if (self.duplicate_detection_service and self.merge_suggestion_repository and 
            incident.id and (incident.title or incident.description)):
            try:
                duplicates = await self.duplicate_detection_service.detect_duplicates(incident)
                if duplicates:
                    # Create merge suggestion for highest similarity match
                    best_match = duplicates[0]
                    if best_match.similarity_score >= settings.DUPLICATE_SIMILARITY_THRESHOLD:
                        # Check if suggestion already exists
                        existing_suggestions = await self.merge_suggestion_repository.find_by_primary_incident(
                            str(incident.id),
                            MergeSuggestionStatus.PENDING
                        )
                        # Check if this duplicate is already in a pending suggestion
                        duplicate_already_suggested = any(
                            best_match.incident_id in s.duplicate_incident_ids
                            for s in existing_suggestions
                        )
                        if not duplicate_already_suggested:
                            await self.merge_suggestion_repository.create({
                                "primary_incident_id": str(incident.id),
                                "duplicate_incident_ids": [best_match.incident_id],
                                "similarity_score": best_match.similarity_score,
                                "match_reasons": best_match.match_reasons,
                                "suggested_by": "system",
                                "status": MergeSuggestionStatus.PENDING.value
                            })
                            logger.info(f"Created merge suggestion for incident {incident.incident_number} with {best_match.incident_id}")
            except Exception as e:
                logger.error(f"Error detecting duplicates for incident {incident.id}: {e}", exc_info=True)
                # Don't fail incident creation if duplicate detection fails

        return incident

    async def get_incident_by_id(self, incident_id: str, populate_asset: bool = True) -> Incident:
        """Get incident by ID."""
        incident = await self.repository.find_by_id(incident_id, populate_asset=populate_asset)
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

        # Check if incident was marked as spam risk
        is_spam_risk = (
            incident.ai_verification_status == "to_be_verified" and
            incident.ai_confidence_score is not None and
            incident.ai_confidence_score < 0.5
        )
        
        # Auto-create maintenance record if linked to an asset
        if incident.asset_id:
            try:
                # Pass technician_id to create_maintenance_from_incident so it can handle spam risk
                maintenance_id = await self.create_maintenance_from_incident(
                    incident_id, assigned_by, technician_id=assigned_to
                )
                
                # Assign the maintenance to the technician as well
                if self.maintenance_service:
                    await self.maintenance_service.assign_maintenance(maintenance_id, assigned_to, assigned_by)
                    
                update_data = {
                    "assigned_to": assigned_to,
                    "status": IncidentStatus.INVESTIGATING.value,
                    "updated_at": datetime.utcnow(),
                    "maintenance_record_id": maintenance_id
                }
                # Note: create_maintenance_from_incident already handles spam risk verification
            except Exception as e:
                logger.error(f"Failed to create maintenance for incident {incident_id}: {e}")
                # Fallback to just assigning the incident without maintenance (or raise error based on policy)
                update_data = {
                    "assigned_to": assigned_to,
                    "status": IncidentStatus.INVESTIGATING.value,
                    "updated_at": datetime.utcnow()
                }
                # Mark as verified if spam risk (when maintenance creation fails)
                if is_spam_risk:
                    update_data["ai_verification_status"] = "verified"
                    update_data["ai_confidence_score"] = 0.8
                    update_data["ai_verification_reason"] = (
                        f"Verified by admin action: Technician assigned. "
                        f"Original AI score: {incident.ai_confidence_score:.2f}"
                    )
                    update_data["ai_verified_at"] = datetime.utcnow()
                    logger.info(
                        f"Incident {incident_id} marked as verified due to technician assignment "
                        f"(was spam risk with score {incident.ai_confidence_score})"
                    )
        else:
            update_data = {
                "assigned_to": assigned_to,
                "status": IncidentStatus.INVESTIGATING.value,
                "updated_at": datetime.utcnow()
            }
            # Mark as verified if spam risk (when no asset_id, so no maintenance created)
            if is_spam_risk:
                update_data["ai_verification_status"] = "verified"
                update_data["ai_confidence_score"] = 0.8
                update_data["ai_verification_reason"] = (
                    f"Verified by admin action: Technician assigned. "
                    f"Original AI score: {incident.ai_confidence_score:.2f}"
                )
                update_data["ai_verified_at"] = datetime.utcnow()
                logger.info(
                    f"Incident {incident_id} marked as verified due to technician assignment "
                    f"(was spam risk with score {incident.ai_confidence_score})"
                )

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
        created_by: str,
        technician_id: Optional[str] = None
    ) -> str:
        """Create a maintenance work order from incident."""
        try:
            incident = await self.get_incident_by_id(incident_id)
            logger.info(f"Creating maintenance for incident {incident_id}, asset_id={incident.asset_id}, technician_id={technician_id}")

            if not incident.asset_id:
                raise ValueError("Incident must be linked to an asset to create maintenance")

            if not self.maintenance_service:
                logger.error("Maintenance service is not available")
                raise RuntimeError("Maintenance service not available")

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
                estimated_duration=120,  # Default 2 hours
                assigned_to=technician_id
            )
            logger.debug(f"Maintenance data: {maintenance_data.dict()}")
            maintenance = await self.maintenance_service.create_maintenance(maintenance_data, created_by)
            logger.info(f"Created maintenance record {maintenance.id}")

            # Link maintenance to incident and update status if technician is assigned
            update_data = {
                "maintenance_record_id": str(maintenance.id),
                "updated_at": datetime.utcnow()
            }
            
            # If technician is assigned, transition incident to assigned status
            if technician_id:
                update_data["assigned_to"] = technician_id
                # Only update status if incident is in acknowledged or reported state
                if incident.status in [IncidentStatus.ACKNOWLEDGED.value, IncidentStatus.REPORTED.value]:
                    update_data["status"] = IncidentStatus.ASSIGNED.value
                
                # If incident was marked as spam risk but admin assigned technician,
                # mark it as verified (useful ticket)
                is_spam_risk = (
                    incident.ai_verification_status == "to_be_verified" and
                    incident.ai_confidence_score is not None and
                    incident.ai_confidence_score < 0.5
                )
                if is_spam_risk:
                    update_data["ai_verification_status"] = "verified"
                    update_data["ai_confidence_score"] = 0.8  # Set to verified threshold
                    update_data["ai_verification_reason"] = (
                        f"Verified by admin action: Technician assigned for maintenance. "
                        f"Original AI score: {incident.ai_confidence_score:.2f}"
                    )
                    update_data["ai_verified_at"] = datetime.utcnow()
                    logger.info(
                        f"Incident {incident_id} marked as verified due to technician assignment "
                        f"(was spam risk with score {incident.ai_confidence_score})"
                    )
            
            await self.repository.update(incident_id, update_data)
            logger.info(f"Updated incident {incident_id} with maintenance record")

            return str(maintenance.id)
        except ValueError as e:
            logger.error(f"ValueError creating maintenance: {e}")
            raise
        except RuntimeError as e:
            logger.error(f"RuntimeError creating maintenance: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating maintenance from incident {incident_id}: {e}", exc_info=True)
            raise

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

        # Ensure user_id is included in the dict even if it's None
        comment_dict = comment.dict(exclude_none=False)
        await self.repository.add_comment(incident_id, comment_dict)
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
        reported_by: Optional[str] = None,
        populate_asset: bool = True,
        verification_status: Optional[str] = None
    ) -> List[Incident]:
        """List incidents with filtering."""
        return await self.repository.list(
            skip, limit, status, severity, asset_id, reported_by, 
            populate_asset, verification_status
        )

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

    async def update_verification(
        self,
        incident_id: str,
        verification_status: str,
        confidence_score: Optional[float],
        verification_reason: Optional[str]
    ) -> Incident:
        """Update AI verification status for an incident."""
        from datetime import datetime
        
        update_data = {
            "ai_verification_status": verification_status,
            "ai_confidence_score": confidence_score,
            "ai_verification_reason": verification_reason,
            "ai_verified_at": datetime.utcnow()
        }
        
        updated = await self.repository.update(incident_id, update_data)
        if not updated:
            raise NotFoundError("Incident", incident_id)
        
        logger.info(
            f"Updated verification for incident {incident_id}: "
            f"status={verification_status}, score={confidence_score}"
        )
        return updated

    async def close_incident(
        self,
        incident_id: str,
        closed_by: str,
        notes: Optional[str] = None
    ) -> Incident:
        """Close a resolved incident."""
        incident = await self.repository.find_by_id(incident_id)
        if not incident:
            raise NotFoundError("Incident", incident_id)
        
        if incident.status not in ["resolved", "acknowledged", "reported"]:
            raise ValueError(f"Cannot close incident in status: {incident.status}")
        
        update_data = {
            "status": "closed",
            "closed_at": datetime.now(),
            "closed_by": closed_by
        }
        if notes:
            update_data["resolution_notes"] = notes
        
        updated = await self.repository.update(incident_id, update_data)
        logger.info(f"Incident {incident_id} closed by {closed_by}")
        return updated

    async def reject_incident(
        self,
        incident_id: str,
        rejected_by: str,
        reason: str
    ) -> Incident:
        """Reject an incident as invalid or spam."""
        incident = await self.repository.find_by_id(incident_id)
        if not incident:
            raise NotFoundError("Incident", incident_id)
        
        update_data = {
            "status": "closed",
            "resolution_type": "not_an_issue",
            "resolution_notes": f"Rejected: {reason}",
            "resolved_at": datetime.now(),
            "resolved_by": rejected_by,
            "closed_at": datetime.now(),
            "closed_by": rejected_by
        }
        
        updated = await self.repository.update(incident_id, update_data)
        logger.info(f"Incident {incident_id} rejected by {rejected_by}: {reason}")
        return updated

    async def manual_verify_incident(
        self,
        incident_id: str,
        verified_by: str
    ) -> Incident:
        """Manually verify an incident by human admin."""
        incident = await self.repository.find_by_id(incident_id)
        if not incident:
            raise NotFoundError("Incident", incident_id)
        
        update_data = {
            "ai_verification_status": "verified",
            "ai_confidence_score": 1.0,
            "ai_verification_reason": f"Manually verified by admin",
            "ai_verified_at": datetime.now()
        }
        
        updated = await self.repository.update(incident_id, update_data)
        logger.info(f"Incident {incident_id} manually verified by {verified_by}")
        return updated

    async def check_duplicates(self, incident_id: str) -> List:
        """Manually check for duplicate incidents."""
        incident = await self.get_incident_by_id(incident_id)
        if not self.duplicate_detection_service:
            return []
        return await self.duplicate_detection_service.detect_duplicates(incident)

    async def get_merge_suggestions(
        self,
        incident_id: str,
        status: Optional[MergeSuggestionStatus] = None
    ) -> List[MergeSuggestion]:
        """Get merge suggestions for an incident."""
        if not self.merge_suggestion_repository:
            return []
        return await self.merge_suggestion_repository.find_by_primary_incident(incident_id, status)

    async def approve_merge(
        self,
        suggestion_id: str,
        approved_by: str
    ) -> Incident:
        """Approve and execute a merge suggestion."""
        if not self.merge_suggestion_repository or not self.merge_service:
            raise RuntimeError("Merge service not available")

        suggestion = await self.merge_suggestion_repository.find_by_id(suggestion_id)
        if not suggestion:
            raise NotFoundError("MergeSuggestion", suggestion_id)

        if suggestion.status != MergeSuggestionStatus.PENDING:
            raise ConflictError("Merge suggestion is not pending")

        # Validate that incidents still exist and are mergeable
        primary = await self.repository.find_by_id(suggestion.primary_incident_id)
        if not primary:
            raise NotFoundError("Incident", suggestion.primary_incident_id)
        
        if primary.status in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
            raise ConflictError(f"Primary incident {primary.incident_number} is already resolved/closed")

        # Check if any duplicates are already resolved
        valid_duplicate_ids = []
        for dup_id in suggestion.duplicate_incident_ids:
            dup = await self.repository.find_by_id(dup_id)
            if dup and dup.status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
                valid_duplicate_ids.append(dup_id)
            elif dup:
                logger.warning(f"Duplicate {dup_id} already resolved, skipping from merge")

        if not valid_duplicate_ids:
            raise ValueError("No valid duplicate incidents to merge (all already resolved)")

        # Execute merge
        try:
            merged_incident = await self.merge_service.merge_incidents(
                primary_id=suggestion.primary_incident_id,
                duplicate_ids=valid_duplicate_ids,
                merged_by=approved_by,
                merge_notes=f"Approved merge suggestion {suggestion_id}"
            )

            # Update suggestion status
            await self.merge_suggestion_repository.update(
                suggestion_id,
                {
                    "status": MergeSuggestionStatus.APPROVED.value,
                    "approved_by": approved_by,
                    "reviewed_at": datetime.utcnow()
                }
            )

            return merged_incident
        except Exception as e:
            logger.error(f"Error executing merge for suggestion {suggestion_id}: {e}", exc_info=True)
            raise

    async def reject_merge(
        self,
        suggestion_id: str,
        rejected_by: str,
        review_notes: Optional[str] = None
    ) -> bool:
        """Reject a merge suggestion."""
        if not self.merge_suggestion_repository:
            raise RuntimeError("Merge suggestion repository not available")

        suggestion = await self.merge_suggestion_repository.find_by_id(suggestion_id)
        if not suggestion:
            raise NotFoundError("MergeSuggestion", suggestion_id)

        if suggestion.status != MergeSuggestionStatus.PENDING:
            raise ConflictError("Merge suggestion is not pending")

        # Update suggestion status
        updated = await self.merge_suggestion_repository.update(
            suggestion_id,
            {
                "status": MergeSuggestionStatus.REJECTED.value,
                "rejected_by": rejected_by,
                "reviewed_at": datetime.utcnow(),
                "review_notes": review_notes
            }
        )

        return updated is not None

    async def merge_incidents(
        self,
        primary_id: str,
        duplicate_ids: List[str],
        merged_by: str,
        merge_notes: Optional[str] = None
    ) -> Incident:
        """Manually merge incidents."""
        if not self.merge_service:
            raise RuntimeError("Merge service not available")
        return await self.merge_service.merge_incidents(
            primary_id=primary_id,
            duplicate_ids=duplicate_ids,
            merged_by=merged_by,
            merge_notes=merge_notes
        )
