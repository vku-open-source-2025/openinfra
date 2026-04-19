"""Unit tests for EOP service workflow rules."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import pytest

from app.core.exceptions import ValidationError
from app.domain.models.eop_plan import EOPPlan, EOPPlanCreate, EOPPlanUpdate
from app.domain.models.emergency import (
    EmergencyEvent,
    EmergencyEventType,
    EmergencySeverity,
    EmergencySource,
    EmergencyStatus,
)
from app.domain.services.eop_service import EOPService


class FakeEOPPlanRepository:
    """In-memory repository for EOP service tests."""

    def __init__(self):
        self._items: dict[str, EOPPlan] = {}

    async def create(self, payload: dict) -> EOPPlan:
        plan_id = str(len(self._items) + 1)
        plan = EOPPlan(**{**payload, "_id": plan_id})
        self._items[plan_id] = plan
        return plan

    async def find_by_id(self, plan_id: str) -> Optional[EOPPlan]:
        return self._items.get(plan_id)

    async def update(self, plan_id: str, updates: dict) -> Optional[EOPPlan]:
        current = self._items.get(plan_id)
        if not current:
            return None

        payload = current.model_dump(by_alias=True)
        payload.update(updates)
        payload["_id"] = plan_id
        updated = EOPPlan(**payload)
        self._items[plan_id] = updated
        return updated

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
    ):
        plans = list(self._items.values())
        if emergency_event_id:
            plans = [plan for plan in plans if plan.emergency_event_id == emergency_event_id]
        if status:
            plans = [plan for plan in plans if plan.status.value == status]
        return plans[skip : skip + limit]


class FakeEmergencyRepository:
    """In-memory emergency repository for EOP generation tests."""

    def __init__(self):
        self._event = EmergencyEvent(
            _id="ev-gen",
            event_code="EMG-TEST-001",
            title="Urban Flooding",
            event_type=EmergencyEventType.FLOOD,
            severity=EmergencySeverity.HIGH,
            status=EmergencyStatus.ACTIVE,
            source=EmergencySource.MANUAL,
            instructions=["Close low-lying roads", "Prepare evacuation support"],
            created_at=datetime.utcnow(),
        )

    async def find_by_id(self, event_id: str):
        if event_id == "ev-gen":
            return self._event
        return None


class FakeGeminiService:
    """Stub Gemini service for deterministic output."""

    async def generate_text_completion(self, _prompt: str, model: Optional[str] = None):
        _ = model
        return json.dumps(
            {
                "title": "AI Draft Flood Plan",
                "summary": "Generated summary from AI.",
                "objectives": ["Protect lives", "Stabilize network"],
                "operational_phases": ["command", "response", "recovery"],
                "actions": [
                    {
                        "action_id": "AI-001",
                        "title": "Deploy pumps",
                        "description": "Deploy mobile pumps to critical points.",
                        "phase": "response",
                        "priority": "high",
                        "owner_role": "operations_lead",
                        "estimated_minutes": 35,
                        "dependencies": [],
                    }
                ],
                "assignment_matrix": [
                    {
                        "action_id": "AI-001",
                        "status": "pending",
                    }
                ],
                "evacuation_plan": ["Coordinate evacuations by district."],
                "fallback_plan": ["Escalate if flood level rises."],
                "communications_plan": ["Broadcast updates every 30 minutes."],
            }
        )


@pytest.mark.asyncio
async def test_publish_requires_approved_eop_plan():
    repository = FakeEOPPlanRepository()
    service = EOPService(repository)

    created = await service.create_plan(
        EOPPlanCreate(
            emergency_event_id="ev-1",
            title="Flood Containment Plan",
        ),
        created_by="operator-1",
    )

    with pytest.raises(ValidationError):
        await service.publish_plan(str(created.id), published_by="operator-2")


@pytest.mark.asyncio
async def test_approve_then_publish_eop_plan_successfully():
    repository = FakeEOPPlanRepository()
    service = EOPService(repository)

    created = await service.create_plan(
        EOPPlanCreate(
            emergency_event_id="ev-2",
            title="Storm Response Plan",
        ),
        created_by="operator-1",
    )

    approved = await service.approve_plan(
        str(created.id),
        approved_by="operator-2",
        review_notes="Reviewed and approved",
    )
    assert approved.status.value == "approved"

    published = await service.publish_plan(str(created.id), published_by="operator-3")
    assert published.status.value == "published"
    assert published.published_by == "operator-3"


@pytest.mark.asyncio
async def test_cannot_update_published_eop_plan():
    repository = FakeEOPPlanRepository()
    service = EOPService(repository)

    created = await service.create_plan(
        EOPPlanCreate(
            emergency_event_id="ev-3",
            title="Landslide Plan",
        ),
        created_by="operator-1",
    )

    await service.approve_plan(str(created.id), approved_by="operator-2")
    await service.publish_plan(str(created.id), published_by="operator-3")

    with pytest.raises(ValidationError):
        await service.update_plan(
            str(created.id),
            EOPPlanUpdate(summary="Attempted post-publish edit"),
            updated_by="operator-4",
        )


@pytest.mark.asyncio
async def test_generate_eop_draft_with_fallback_when_gemini_missing():
    repository = FakeEOPPlanRepository()
    service = EOPService(repository, emergency_repository=FakeEmergencyRepository())

    draft = await service.generate_draft(
        emergency_event_id="ev-gen",
        generated_by="operator-1",
        additional_context="High rainfall expected for next 6 hours",
    )

    assert draft.emergency_event_id == "ev-gen"
    assert draft.status.value == "draft"
    assert len(draft.actions) >= 3
    assert draft.metadata.get("generation_source") == "fallback"


@pytest.mark.asyncio
async def test_generate_eop_draft_uses_ai_payload_when_available():
    repository = FakeEOPPlanRepository()
    service = EOPService(
        repository,
        emergency_repository=FakeEmergencyRepository(),
        gemini_service=FakeGeminiService(),
    )

    draft = await service.generate_draft(
        emergency_event_id="ev-gen",
        generated_by="operator-2",
    )

    assert draft.title == "AI Draft Flood Plan"
    assert len(draft.actions) == 1
    assert draft.actions[0].action_id == "AI-001"
    assert draft.metadata.get("generation_source") == "gemini"
