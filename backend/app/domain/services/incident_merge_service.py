"""Incident merge service for combining duplicate incidents."""
from typing import List, Optional
from datetime import datetime
from app.domain.models.incident import Incident, IncidentStatus, ResolutionType, IncidentSeverity
from app.domain.repositories.incident_repository import IncidentRepository
import logging

logger = logging.getLogger(__name__)


class IncidentMergeService:
    """Service for merging duplicate incidents."""

    def __init__(self, incident_repository: IncidentRepository):
        self.repository = incident_repository

    async def merge_incidents(
        self,
        primary_id: str,
        duplicate_ids: List[str],
        merged_by: str,
        merge_notes: Optional[str] = None
    ) -> Incident:
        """Merge duplicate incidents into primary incident."""
        # Input validation
        if not primary_id:
            raise ValueError("Primary incident ID is required")
        if not duplicate_ids:
            raise ValueError("At least one duplicate incident ID is required")
        if primary_id in duplicate_ids:
            raise ValueError("Primary incident cannot be in duplicate list")
        if len(set(duplicate_ids)) != len(duplicate_ids):
            raise ValueError("Duplicate IDs must be unique")
        if len(duplicate_ids) > 10:
            raise ValueError("Cannot merge more than 10 incidents at once")

        # Get primary incident
        primary = await self.repository.find_by_id(primary_id)
        if not primary:
            raise ValueError(f"Primary incident {primary_id} not found")

        # Check if primary is already resolved/closed
        if primary.status in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
            raise ValueError(f"Cannot merge into resolved/closed incident {primary.incident_number}")

        # Get duplicate incidents
        duplicates = []
        for dup_id in duplicate_ids:
            if dup_id == primary_id:
                logger.warning(f"Skipping duplicate ID {dup_id} (same as primary)")
                continue
            dup = await self.repository.find_by_id(dup_id)
            if not dup:
                logger.warning(f"Duplicate incident {dup_id} not found, skipping")
                continue
            # Check if duplicate is already resolved as duplicate
            if dup.resolution_type == ResolutionType.DUPLICATE:
                logger.warning(f"Duplicate incident {dup_id} already marked as duplicate, skipping")
                continue
            # Check for circular references
            if str(primary.id) in dup.related_incidents:
                logger.warning(f"Circular reference detected: {dup_id} already related to {primary_id}")
                continue
            duplicates.append(dup)

        if not duplicates:
            raise ValueError("No valid duplicate incidents to merge")

        # Select primary (oldest or highest severity)
        # If primary is not the oldest, we should use the oldest as primary
        all_incidents = [primary] + duplicates
        oldest = min(all_incidents, key=lambda x: x.reported_at)
        
        # If oldest is not the current primary, swap
        if oldest.id != primary.id:
            logger.info(f"Swapping primary from {primary.id} to oldest {oldest.id}")
            primary, oldest = oldest, primary
            # Update duplicate_ids to exclude the new primary
            duplicate_ids = [d.id for d in duplicates if d.id != primary.id]

        # Merge data
        merged_reporter_ids = [primary.reported_by] if primary.reported_by else []
        merged_reporter_ids.extend([d.reported_by for d in duplicates if d.reported_by])
        merged_reporter_ids = list(set(merged_reporter_ids))  # Deduplicate

        # Merge upvotes and upvoted_by
        merged_upvoted_by = set(primary.upvoted_by)
        for dup in duplicates:
            merged_upvoted_by.update(dup.upvoted_by)
        merged_upvotes = len(merged_upvoted_by)

        # Merge comments (preserve chronological order)
        merged_comments = list(primary.comments)
        for dup in duplicates:
            merged_comments.extend(dup.comments)
        # Sort by posted_at
        merged_comments.sort(key=lambda x: x.posted_at)

        # Merge photos, videos, attachments
        merged_photos = list(set(primary.photos))
        for dup in duplicates:
            merged_photos.extend([p for p in dup.photos if p not in merged_photos])

        merged_videos = list(set(primary.videos))
        for dup in duplicates:
            merged_videos.extend([v for v in dup.videos if v not in merged_videos])

        merged_attachments = list(primary.attachments)
        for dup in duplicates:
            merged_attachments.extend([
                a for a in dup.attachments
                if a.file_url not in [att.file_url for att in merged_attachments]
            ])

        # Merge related incidents (avoid circular references)
        merged_related = set(primary.related_incidents)
        all_ids = {str(primary.id)} | {str(d.id) for d in duplicates}
        for dup in duplicates:
            # Add related incidents, excluding circular references
            for related_id in dup.related_incidents:
                if related_id not in all_ids:
                    merged_related.add(related_id)
            merged_related.add(str(dup.id))  # Add duplicate itself

        # Take highest severity
        severity_order = {
            IncidentSeverity.CRITICAL: 4,
            IncidentSeverity.HIGH: 3,
            IncidentSeverity.MEDIUM: 2,
            IncidentSeverity.LOW: 1
        }
        highest_severity = max(
            [primary] + duplicates,
            key=lambda x: severity_order.get(x.severity, 0)
        ).severity

        # Combine descriptions if different (limit total length)
        descriptions = [primary.description]
        max_description_length = 50000  # Limit to 50k characters
        for dup in duplicates:
            if dup.description and dup.description not in descriptions:
                descriptions.append(dup.description)
        
        combined_description = primary.description
        if len(descriptions) > 1:
            additional = "\n\n".join(descriptions[1:])
            combined_description = f"{primary.description}\n\n--- Additional reports ---\n{additional}"
            # Truncate if too long
            if len(combined_description) > max_description_length:
                combined_description = combined_description[:max_description_length] + "\n\n[Description truncated due to length]"

        # Update primary incident
        update_data = {
            "merged_reporter_ids": merged_reporter_ids,
            "upvotes": merged_upvotes,
            "upvoted_by": list(merged_upvoted_by),
            "comments": [c.dict() for c in merged_comments],
            "photos": merged_photos,
            "videos": merged_videos,
            "attachments": [a.dict() for a in merged_attachments],
            "related_incidents": list(merged_related),
            "severity": highest_severity.value,
            "description": combined_description,
            "updated_at": datetime.utcnow()
        }

        updated_primary = await self.repository.update(primary.id, update_data)
        if not updated_primary:
            raise ValueError(f"Failed to update primary incident {primary.id}")

        # Add merge comment to primary
        merge_comment_text = f"Merged {len(duplicates)} duplicate incident(s): {', '.join([d.incident_number for d in duplicates])}"
        if merge_notes:
            merge_comment_text += f"\nNotes: {merge_notes}"
        merge_comment_text += f"\nMerged by: {merged_by}"

        await self.repository.add_comment(
            primary.id,
            {
                "user_id": merged_by,
                "comment": merge_comment_text,
                "posted_at": datetime.utcnow(),
                "is_internal": True
            }
        )

        # Mark duplicates as resolved
        for dup in duplicates:
            await self.repository.update(
                dup.id,
                {
                    "status": IncidentStatus.RESOLVED.value,
                    "resolved_at": datetime.utcnow(),
                    "resolved_by": merged_by,
                    "resolution_type": ResolutionType.DUPLICATE.value,
                    "resolution_notes": f"Merged into incident {primary.incident_number}",
                    "related_incidents": [str(primary.id)],
                    "updated_at": datetime.utcnow()
                }
            )

        logger.info(f"Merged {len(duplicates)} incidents into {primary.incident_number}")
        return await self.repository.find_by_id(primary.id)

