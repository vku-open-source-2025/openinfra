"""Duplicate detection service for incidents."""
from typing import List, Optional
from app.domain.models.incident import Incident
from app.domain.models.merge_suggestion import DuplicateMatch
from app.domain.repositories.incident_repository import IncidentRepository
from app.infrastructure.external.gemini_service import GeminiService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class DuplicateDetectionService:
    """Service for detecting duplicate incidents."""

    def __init__(
        self,
        incident_repository: IncidentRepository,
        gemini_service: GeminiService
    ):
        self.repository = incident_repository
        self.gemini_service = gemini_service

    async def detect_duplicates(self, incident: Incident) -> List[DuplicateMatch]:
        """Detect potential duplicate incidents.
        
        Considers multiple scenarios:
        1. Multiple reports of same issue before fix (active incidents)
        2. Recurrence: Same issue happens again after being resolved
        3. Reports while technician is working (in progress incidents)
        """
        try:
            # Get potential duplicates from repository
            location_dict = None
            if incident.location:
                try:
                    location_dict = incident.location.dict() if hasattr(incident.location, 'dict') else incident.location
                except Exception as e:
                    logger.warning(f"Error serializing location for incident {incident.id}: {e}")
                    location_dict = None

            # Include resolved incidents to detect recurrence (longer time window)
            candidates = await self.repository.find_potential_duplicates(
                asset_id=incident.asset_id,
                location=location_dict,
                location_radius_meters=settings.DUPLICATE_LOCATION_RADIUS_METERS,
                time_window_hours=settings.DUPLICATE_TIME_WINDOW_HOURS,
                category=incident.category.value if incident.category else None,
                severity=incident.severity.value if incident.severity else None,
                exclude_incident_ids=[incident.id] if incident.id else None,
                limit=50,
                include_resolved=True,  # Include resolved incidents for recurrence detection
                resolved_time_window_hours=getattr(settings, 'DUPLICATE_RESOLVED_TIME_WINDOW_HOURS', 720)  # 30 days default
            )

            if not candidates:
                return []

            # Prepare text content for new incident
            new_text = f"{incident.title} {incident.description}".strip()
            new_images = incident.photos[:settings.GEMINI_MAX_IMAGES_PER_INCIDENT] if incident.photos else []

            # Calculate similarity for each candidate
            matches = []
            for candidate in candidates:
                try:
                    # Prepare text content for candidate
                    candidate_text = f"{candidate.title} {candidate.description}".strip()
                    candidate_images = candidate.photos[:settings.GEMINI_MAX_IMAGES_PER_INCIDENT] if candidate.photos else []

                    # Calculate multimodal similarity
                    similarity_score = await self.gemini_service.calculate_multimodal_similarity(
                        text1=new_text,
                        images1=new_images,
                        text2=candidate_text,
                        images2=candidate_images
                    )

                    # Filter by threshold
                    if similarity_score >= settings.DUPLICATE_SIMILARITY_THRESHOLD:
                        # Determine match reasons
                        match_reasons = []
                        if incident.asset_id and candidate.asset_id == incident.asset_id:
                            match_reasons.append("same_asset")
                        if similarity_score >= 0.9:
                            match_reasons.append("very_similar_description")
                        elif similarity_score >= 0.85:
                            match_reasons.append("similar_description")
                        if new_images and candidate_images:
                            match_reasons.append("similar_images")
                        if incident.location and candidate.location:
                            match_reasons.append("nearby_location")
                        
                        # Add temporal context
                        if candidate.status == "resolved":
                            match_reasons.append("possible_recurrence")
                        elif candidate.status in ["assigned", "investigating", "in_progress"]:
                            match_reasons.append("reported_during_work")

                        matches.append(DuplicateMatch(
                            incident_id=str(candidate.id),
                            similarity_score=similarity_score,
                            match_reasons=match_reasons
                        ))
                except Exception as e:
                    logger.error(f"Error calculating similarity for candidate {candidate.id}: {e}")
                    continue

            # Sort by similarity score (highest first)
            matches.sort(key=lambda x: x.similarity_score, reverse=True)
            return matches

        except Exception as e:
            logger.error(f"Error detecting duplicates for incident {incident.id}: {e}")
            return []

