"""Emergency operation plan service."""

import json
import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.models.eop_plan import (
    EOPPlan,
    EOPAction,
    EOPAssignment,
    EOPPlanCreate,
    EOPPlanStatus,
    EOPPlanUpdate,
)
from app.domain.repositories.emergency_repository import EmergencyRepository
from app.domain.repositories.eop_plan_repository import EOPPlanRepository

if TYPE_CHECKING:
    from app.infrastructure.external.ag05_context_service import AG05ContextService
    from app.infrastructure.external.gemini_service import GeminiService


logger = logging.getLogger(__name__)


class EOPService:
    """Business logic for EOP planning workflow."""

    def __init__(
        self,
        repository: EOPPlanRepository,
        emergency_repository: Optional[EmergencyRepository] = None,
        gemini_service: Optional["GeminiService"] = None,
        ag05_context_service: Optional["AG05ContextService"] = None,
    ):
        self.repository = repository
        self.emergency_repository = emergency_repository
        self.gemini_service = gemini_service
        self.ag05_context_service = ag05_context_service

    @staticmethod
    def _extract_first_json_object(raw_text: str) -> Optional[dict]:
        """Extract first JSON object from LLM output."""
        if not raw_text:
            return None

        raw_text = raw_text.strip()
        try:
            parsed = json.loads(raw_text)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{[\s\S]*\}", raw_text)
        if not match:
            return None

        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None

    def _build_fallback_plan_payload(self, event, additional_context: Optional[str]) -> dict:
        """Build deterministic fallback EOP payload when AI output is unavailable."""
        event_type = event.event_type.value
        severity = event.severity.value
        location = event.location.address if event.location and event.location.address else "unknown area"

        base_actions = [
            {
                "action_id": "ACT-001",
                "title": "Activate incident command",
                "description": "Establish command structure and assign section leads.",
                "phase": "command",
                "priority": "high",
                "owner_role": "incident_commander",
                "estimated_minutes": 15,
                "dependencies": [],
            },
            {
                "action_id": "ACT-002",
                "title": "Deploy initial field teams",
                "description": "Dispatch rapid response units to confirm impact scope.",
                "phase": "response",
                "priority": "high",
                "owner_role": "operations_lead",
                "estimated_minutes": 30,
                "dependencies": ["ACT-001"],
            },
            {
                "action_id": "ACT-003",
                "title": "Publish public safety advisory",
                "description": "Issue citizen instructions through official communication channels.",
                "phase": "communication",
                "priority": "medium",
                "owner_role": "communications_lead",
                "estimated_minutes": 20,
                "dependencies": ["ACT-001"],
            },
        ]

        if event_type in {"flood", "storm"}:
            base_actions.append(
                {
                    "action_id": "ACT-004",
                    "title": "Prepare evacuation corridors",
                    "description": "Coordinate traffic control and shelter routing for affected wards.",
                    "phase": "evacuation",
                    "priority": "high",
                    "owner_role": "logistics_lead",
                    "estimated_minutes": 45,
                    "dependencies": ["ACT-002"],
                }
            )

        summary = (
            f"Operational plan for {event.title} ({event_type}, severity {severity}) in {location}. "
            "Plan prioritizes command activation, rapid field response, and public communication."
        )
        if additional_context:
            summary = f"{summary} Additional context: {additional_context}"

        return {
            "title": f"AI EOP Draft - {event.title}",
            "summary": summary,
            "objectives": [
                "Protect human life and critical infrastructure.",
                "Contain cascading risk and stabilize the affected zone.",
                "Maintain transparent communication with stakeholders.",
            ],
            "operational_phases": ["command", "response", "stabilization", "recovery"],
            "actions": base_actions,
            "assignment_matrix": [
                {
                    "action_id": action["action_id"],
                    "status": "pending",
                    "notes": "Generated by AI draft assistant",
                }
                for action in base_actions
            ],
            "evacuation_plan": [
                "Prioritize evacuation for high-risk zones and vulnerable populations.",
                "Coordinate shelters with local authorities and utility operators.",
            ],
            "fallback_plan": [
                "Escalate to regional support if local resources drop below minimum threshold.",
                "Switch to manual radio channel if digital communications are disrupted.",
            ],
            "communications_plan": [
                "Publish official updates every 30 minutes during active response.",
                "Use verified multi-channel alerts for evacuation and safety directives.",
            ],
        }

    def _normalize_generated_plan(self, payload: dict) -> dict:
        """Normalize AI-generated payload to schema-safe EOP fields."""
        normalized_actions = []
        for index, action in enumerate(payload.get("actions", []), start=1):
            if not isinstance(action, dict):
                continue
            action_id = str(action.get("action_id") or f"ACT-{index:03d}")
            title = str(action.get("title") or "Untitled action").strip()
            if not title:
                title = "Untitled action"

            estimated_minutes = action.get("estimated_minutes")
            if estimated_minutes is not None:
                try:
                    estimated_minutes = int(estimated_minutes)
                except (TypeError, ValueError):
                    estimated_minutes = None

            normalized_actions.append(
                EOPAction(
                    action_id=action_id,
                    title=title,
                    description=action.get("description"),
                    phase=str(action.get("phase") or "response"),
                    priority=str(action.get("priority") or "medium"),
                    owner_role=action.get("owner_role"),
                    estimated_minutes=estimated_minutes,
                    dependencies=[str(dep) for dep in (action.get("dependencies") or [])],
                )
            )

        assignment_matrix = []
        for item in payload.get("assignment_matrix", []):
            if not isinstance(item, dict):
                continue
            action_id = str(item.get("action_id") or "")
            if not action_id:
                continue
            assignment_matrix.append(
                EOPAssignment(
                    action_id=action_id,
                    resource_unit_id=item.get("resource_unit_id"),
                    assignee_id=item.get("assignee_id"),
                    status=str(item.get("status") or "pending"),
                    notes=item.get("notes"),
                )
            )

        return {
            "title": str(payload.get("title") or "AI Generated Emergency Plan"),
            "summary": payload.get("summary"),
            "objectives": [str(v) for v in (payload.get("objectives") or []) if str(v).strip()],
            "operational_phases": [
                str(v) for v in (payload.get("operational_phases") or []) if str(v).strip()
            ],
            "actions": normalized_actions,
            "assignment_matrix": assignment_matrix,
            "evacuation_plan": [str(v) for v in (payload.get("evacuation_plan") or [])],
            "fallback_plan": [str(v) for v in (payload.get("fallback_plan") or [])],
            "communications_plan": [str(v) for v in (payload.get("communications_plan") or [])],
        }

    @staticmethod
    def _format_ag05_snippets(snippets: List[Dict[str, str]]) -> str:
        """Format AG05 snippets for prompt context inclusion."""
        formatted = []
        for snippet in snippets:
            source_id = str(snippet.get("source_id") or "AG05").strip()
            text = str(snippet.get("text") or "").strip()
            if text:
                formatted.append(f"[{source_id}] {text}")
        return "\n".join(formatted)

    @staticmethod
    def _build_ag05_retrieval_query(event: Any, additional_context: Optional[str]) -> str:
        """Build retrieval query text from emergency event context."""
        location = event.location.address if event.location and event.location.address else "unknown"
        parts = [
            f"Emergency title: {event.title}",
            f"Event type: {event.event_type.value}",
            f"Severity: {event.severity.value}",
            f"Status: {event.status.value}",
            f"Location: {location}",
            f"Instructions: {event.instructions or 'none'}",
            f"Estimated impact: {event.estimated_impact or 'none'}",
        ]
        if additional_context:
            parts.append(f"Additional context: {additional_context}")
        return "\n".join(parts)

    async def generate_draft(
        self,
        emergency_event_id: str,
        generated_by: Optional[str] = None,
        additional_context: Optional[str] = None,
        force_new_version: bool = True,
        request_id: Optional[str] = None,
    ) -> EOPPlan:
        """Generate EOP draft from emergency context with AI + fallback strategy."""
        if self.emergency_repository is None:
            raise ValidationError("Emergency repository is not configured for EOP generation")

        event = await self.emergency_repository.find_by_id(emergency_event_id)
        if not event:
            raise NotFoundError("EmergencyEvent", emergency_event_id)

        existing = await self.repository.list(
            skip=0,
            limit=100,
            emergency_event_id=emergency_event_id,
        )
        if not force_new_version:
            reusable_drafts = [plan for plan in existing if plan.status == EOPPlanStatus.DRAFT]
            if reusable_drafts:
                reusable_drafts.sort(key=lambda plan: plan.version, reverse=True)
                return reusable_drafts[0]

        ag05_snippets: List[Dict[str, str]] = []
        if self.ag05_context_service is not None:
            try:
                retrieval_query = self._build_ag05_retrieval_query(event, additional_context)
                ag05_snippets = await self.ag05_context_service.retrieve_snippets(
                    retrieval_query,
                    max_snippets=4,
                )
            except Exception as exc:
                logger.warning("AG05 context retrieval failed for event %s: %s", emergency_event_id, exc)

        ag05_context_text = self._format_ag05_snippets(ag05_snippets)
        merged_context = additional_context
        if ag05_context_text:
            merged_context = (
                f"{additional_context}\n\nAG05 corpus snippets:\n{ag05_context_text}"
                if additional_context
                else f"AG05 corpus snippets:\n{ag05_context_text}"
            )

        fallback_payload = self._build_fallback_plan_payload(event, merged_context)
        normalized_payload = self._normalize_generated_plan(fallback_payload)

        if self.gemini_service is not None:
            prompt = (
                "You are an emergency planner. Generate an Emergency Operation Plan JSON with keys: "
                "title, summary, objectives, operational_phases, actions, assignment_matrix, "
                "evacuation_plan, fallback_plan, communications_plan. "
                "Each action must include action_id, title, description, phase, priority, owner_role, "
                "estimated_minutes, dependencies. "
                "Return ONLY valid JSON object and no markdown. "
                f"Emergency context: title={event.title}, event_type={event.event_type.value}, "
                f"severity={event.severity.value}, status={event.status.value}, "
                f"location={event.location.model_dump() if event.location else 'unknown'}, "
                f"instructions={event.instructions}, estimated_impact={event.estimated_impact}. "
                f"Additional context: {additional_context or 'none'}. "
                f"AG05 vector corpus snippets (with source IDs): {ag05_context_text or 'none'}"
            )

            generated_text = await self.gemini_service.generate_text_completion(prompt)
            parsed = self._extract_first_json_object(generated_text or "")
            if parsed:
                normalized_payload = self._normalize_generated_plan(parsed)

        plan_metadata = {
            "generated_by_ai": True,
            "generation_source": "gemini" if self.gemini_service else "fallback",
            "additional_context": additional_context,
            "ag05_sources": [
                str(snippet.get("source_id"))
                for snippet in ag05_snippets
                if snippet.get("source_id")
            ],
            "ag05_snippet_count": len(ag05_snippets),
        }
        if request_id:
            plan_metadata["request_id"] = request_id

        plan_create = EOPPlanCreate(
            emergency_event_id=emergency_event_id,
            title=normalized_payload["title"],
            summary=normalized_payload.get("summary"),
            objectives=normalized_payload.get("objectives", []),
            operational_phases=normalized_payload.get("operational_phases", []),
            actions=normalized_payload.get("actions", []),
            assignment_matrix=normalized_payload.get("assignment_matrix", []),
            evacuation_plan=normalized_payload.get("evacuation_plan", []),
            fallback_plan=normalized_payload.get("fallback_plan", []),
            communications_plan=normalized_payload.get("communications_plan", []),
            metadata=plan_metadata,
        )

        return await self.create_plan(
            plan_create,
            created_by=generated_by,
            request_id=request_id,
        )

    async def create_plan(
        self,
        payload: EOPPlanCreate,
        created_by: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> EOPPlan:
        """Create a new EOP draft."""
        data = payload.model_dump(exclude_unset=True)
        existing = await self.repository.list(
            skip=0,
            limit=1000,
            emergency_event_id=payload.emergency_event_id,
        )
        current_max_version = max((plan.version for plan in existing), default=0)
        data["version"] = current_max_version + 1
        if created_by or request_id:
            metadata = dict(data.get("metadata", {}))
            if created_by:
                metadata["created_by"] = created_by
            if request_id:
                metadata["request_id"] = request_id
            data["metadata"] = metadata
        return await self.repository.create(data)

    async def get_plan_by_id(self, plan_id: str) -> EOPPlan:
        """Get EOP plan by id."""
        plan = await self.repository.find_by_id(plan_id)
        if not plan:
            raise NotFoundError("EOPPlan", plan_id)
        return plan

    async def list_plans(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[EOPPlan]:
        """List EOP plans with optional filters."""
        return await self.repository.list(skip, limit, emergency_event_id, status)

    async def update_plan(
        self,
        plan_id: str,
        updates: EOPPlanUpdate,
        updated_by: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> EOPPlan:
        """Update EOP plan fields."""
        current = await self.get_plan_by_id(plan_id)

        if current.status in {EOPPlanStatus.PUBLISHED, EOPPlanStatus.ARCHIVED}:
            raise ValidationError(
                f"Cannot update EOP plan in status '{current.status.value}'"
            )

        update_payload = updates.model_dump(exclude_unset=True)
        current_metadata = dict(current.metadata or {})
        incoming_metadata = update_payload.get("metadata")
        if incoming_metadata is not None:
            current_metadata.update(incoming_metadata)
        if updated_by:
            current_metadata["updated_by"] = updated_by
        if request_id:
            current_metadata["request_id"] = request_id
        if incoming_metadata is not None or updated_by or request_id:
            update_payload["metadata"] = current_metadata

        if (
            "review_notes" in update_payload
            and current.status == EOPPlanStatus.DRAFT
            and "status" not in update_payload
        ):
            update_payload["status"] = EOPPlanStatus.REVIEW_PENDING

        updated = await self.repository.update(plan_id, update_payload)
        if not updated:
            raise NotFoundError("EOPPlan", plan_id)
        return updated

    async def approve_plan(
        self,
        plan_id: str,
        approved_by: str,
        review_notes: Optional[str] = None,
    ) -> EOPPlan:
        """Approve an EOP plan."""
        current = await self.get_plan_by_id(plan_id)

        if current.status not in {EOPPlanStatus.DRAFT, EOPPlanStatus.REVIEW_PENDING}:
            raise ValidationError(
                f"Only draft or review-pending EOP plans can be approved. Current status: {current.status.value}"
            )

        updates = {
            "status": EOPPlanStatus.APPROVED.value,
            "approved_by": approved_by,
            "approved_at": datetime.utcnow(),
        }
        if review_notes:
            updates["review_notes"] = review_notes

        updated = await self.repository.update(plan_id, updates)
        if not updated:
            raise NotFoundError("EOPPlan", plan_id)
        return updated

    async def publish_plan(self, plan_id: str, published_by: str) -> EOPPlan:
        """Publish an approved EOP plan."""
        current = await self.get_plan_by_id(plan_id)

        if current.status != EOPPlanStatus.APPROVED:
            raise ValidationError(
                f"Only approved EOP plans can be published. Current status: {current.status.value}"
            )

        updated = await self.repository.update(
            plan_id,
            {
                "status": EOPPlanStatus.PUBLISHED.value,
                "published_by": published_by,
                "published_at": datetime.utcnow(),
            },
        )
        if not updated:
            raise NotFoundError("EOPPlan", plan_id)
        return updated
