"""After-action report service."""

import math
import uuid
from datetime import datetime
from typing import List, Optional

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.models.after_action_report import (
    AfterActionGenerateRequest,
    AfterActionKPI,
    AfterActionReport,
    AfterActionReportUpdate,
    AfterActionStatus,
)
from app.domain.models.dispatch_order import DispatchOrder, DispatchStatus
from app.domain.models.emergency import EmergencyEvent
from app.domain.models.sitrep import Sitrep, SitrepStatus
from app.domain.repositories.after_action_report_repository import AfterActionReportRepository
from app.domain.repositories.dispatch_order_repository import DispatchOrderRepository
from app.domain.repositories.emergency_repository import EmergencyRepository
from app.domain.repositories.sitrep_repository import SitrepRepository


class AfterActionReportService:
    """Business logic for after-action report generation and KPI tracking."""

    def __init__(
        self,
        after_action_repository: AfterActionReportRepository,
        emergency_repository: EmergencyRepository,
        dispatch_repository: DispatchOrderRepository,
        sitrep_repository: SitrepRepository,
    ):
        self.repository = after_action_repository
        self.emergency_repository = emergency_repository
        self.dispatch_repository = dispatch_repository
        self.sitrep_repository = sitrep_repository

    def _generate_report_code(self) -> str:
        """Generate human-readable after-action report code."""
        suffix = uuid.uuid4().hex[:8].upper()
        return f"AAR-{datetime.utcnow():%Y%m%d}-{suffix}"

    @staticmethod
    def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
        """Clamp score into accepted range."""
        return max(minimum, min(maximum, value))

    @staticmethod
    def _minutes_between(start: Optional[datetime], end: Optional[datetime]) -> Optional[float]:
        """Get positive minute difference between two timestamps."""
        if not start or not end:
            return None
        return max((end - start).total_seconds() / 60.0, 0.0)

    def _response_speed_score(self, response_minutes: Optional[float]) -> float:
        """Map response-time minutes to normalized score."""
        if response_minutes is None:
            return 0.0
        if response_minutes <= 15:
            return 100.0
        if response_minutes <= 30:
            return 85.0
        if response_minutes <= 60:
            return 70.0
        if response_minutes <= 120:
            return 50.0
        return 25.0

    def _compute_kpi(
        self,
        event: EmergencyEvent,
        dispatch_orders: List[DispatchOrder],
        sitreps: List[Sitrep],
    ) -> AfterActionKPI:
        """Compute post-incident KPIs from event response artifacts."""
        event_start = event.started_at or event.created_at
        event_end = event.ended_at or datetime.utcnow()
        event_duration_minutes = self._minutes_between(event_start, event_end) or 0.0

        started_dispatch_times = [
            order.started_at
            for order in dispatch_orders
            if order.started_at is not None
        ]
        first_dispatch_start = min(started_dispatch_times) if started_dispatch_times else None
        response_time_minutes = self._minutes_between(event_start, first_dispatch_start)

        total_dispatch = len(dispatch_orders)
        completed_dispatch = sum(
            1 for order in dispatch_orders if order.status == DispatchStatus.COMPLETED
        )
        dispatch_completion_rate = (
            (completed_dispatch / total_dispatch) * 100.0 if total_dispatch else 0.0
        )

        published_sitreps = [
            sitrep
            for sitrep in sitreps
            if sitrep.status == SitrepStatus.PUBLISHED
        ]
        expected_sitreps = max(1, math.ceil(event_duration_minutes / 120.0))
        sitrep_coverage_rate = self._clamp((len(published_sitreps) / expected_sitreps) * 100.0)

        total_assignments = sum(len(order.assignments) for order in dispatch_orders)
        avg_assignments = total_assignments / total_dispatch if total_dispatch else 0.0
        if total_dispatch == 0:
            resource_efficiency_score = 0.0
        elif avg_assignments <= 1.5:
            resource_efficiency_score = 95.0
        elif avg_assignments <= 2.5:
            resource_efficiency_score = 80.0
        elif avg_assignments <= 3.5:
            resource_efficiency_score = 65.0
        else:
            resource_efficiency_score = 45.0

        response_speed_score = self._response_speed_score(response_time_minutes)
        overall_score = self._clamp(
            (response_speed_score * 0.35)
            + (dispatch_completion_rate * 0.35)
            + (sitrep_coverage_rate * 0.15)
            + (resource_efficiency_score * 0.15)
        )

        return AfterActionKPI(
            response_time_minutes=round(response_time_minutes, 2)
            if response_time_minutes is not None
            else None,
            response_speed_score=round(response_speed_score, 2),
            dispatch_completion_rate=round(dispatch_completion_rate, 2),
            sitrep_coverage_rate=round(sitrep_coverage_rate, 2),
            resource_efficiency_score=round(resource_efficiency_score, 2),
            overall_score=round(overall_score, 2),
        )

    def _build_timeline(
        self,
        event: EmergencyEvent,
        dispatch_orders: List[DispatchOrder],
        sitreps: List[Sitrep],
    ) -> list[dict]:
        """Build chronological timeline entries from event artifacts."""
        timeline = []

        timeline.append(
            {
                "timestamp": event.created_at,
                "source": "emergency",
                "action": "event_created",
                "details": {
                    "event_code": event.event_code,
                    "title": event.title,
                    "severity": event.severity.value,
                },
            }
        )

        if event.started_at:
            timeline.append(
                {
                    "timestamp": event.started_at,
                    "source": "emergency",
                    "action": "event_started",
                    "details": {"status": event.status.value},
                }
            )

        if event.ended_at:
            timeline.append(
                {
                    "timestamp": event.ended_at,
                    "source": "emergency",
                    "action": "event_ended",
                    "details": {"status": event.status.value},
                }
            )

        for order in dispatch_orders:
            timeline.append(
                {
                    "timestamp": order.created_at,
                    "source": "dispatch",
                    "action": "order_created",
                    "details": {
                        "order_id": str(order.id),
                        "task_title": order.task_title,
                        "status": order.status.value,
                    },
                }
            )
            if order.started_at:
                timeline.append(
                    {
                        "timestamp": order.started_at,
                        "source": "dispatch",
                        "action": "order_started",
                        "details": {
                            "order_id": str(order.id),
                            "status": order.status.value,
                        },
                    }
                )
            if order.completed_at:
                timeline.append(
                    {
                        "timestamp": order.completed_at,
                        "source": "dispatch",
                        "action": "order_completed",
                        "details": {
                            "order_id": str(order.id),
                            "status": order.status.value,
                        },
                    }
                )

        for sitrep in sitreps:
            timeline.append(
                {
                    "timestamp": sitrep.created_at,
                    "source": "sitrep",
                    "action": "sitrep_created",
                    "details": {
                        "sitrep_id": str(sitrep.id),
                        "title": sitrep.title,
                        "status": sitrep.status.value,
                    },
                }
            )
            if sitrep.published_at:
                timeline.append(
                    {
                        "timestamp": sitrep.published_at,
                        "source": "sitrep",
                        "action": "sitrep_published",
                        "details": {
                            "sitrep_id": str(sitrep.id),
                            "status": sitrep.status.value,
                        },
                    }
                )

        timeline.sort(key=lambda item: item["timestamp"])
        return timeline

    def _build_summary(
        self,
        event: EmergencyEvent,
        kpi: AfterActionKPI,
        dispatch_orders: List[DispatchOrder],
        sitreps: List[Sitrep],
    ) -> str:
        """Build default executive summary."""
        return (
            f"Emergency event '{event.title}' ({event.event_type.value}) concluded with "
            f"overall KPI score {kpi.overall_score:.2f}. "
            f"Dispatch completion reached {kpi.dispatch_completion_rate:.2f}% across "
            f"{len(dispatch_orders)} orders, with SITREP coverage {kpi.sitrep_coverage_rate:.2f}% "
            f"from {len(sitreps)} SITREP records."
        )

    def _default_lessons(self, kpi: AfterActionKPI) -> List[str]:
        """Generate baseline lessons learned from KPI profile."""
        lessons = ["Maintain structured SITREP cadence during active incidents."]
        if kpi.dispatch_completion_rate < 70:
            lessons.append("Dispatch closure discipline needs stronger operational follow-through.")
        if kpi.response_speed_score < 60:
            lessons.append("Initial response mobilization requires faster triage and assignment.")
        return lessons

    def _default_recommendations(self, kpi: AfterActionKPI) -> List[str]:
        """Generate baseline recommendations from KPI profile."""
        recommendations = []
        if kpi.response_speed_score < 70:
            recommendations.append(
                "Introduce automated first-dispatch escalation for high-severity emergencies."
            )
        if kpi.sitrep_coverage_rate < 80:
            recommendations.append(
                "Enforce SITREP publishing checkpoints every 2 hours for active incidents."
            )
        if kpi.dispatch_completion_rate < 85:
            recommendations.append(
                "Adopt dispatch completion review at shift handover to reduce open tasks."
            )
        if not recommendations:
            recommendations.append("Current response process is stable; continue continuous KPI monitoring.")
        return recommendations

    async def get_report_by_id(self, report_id: str) -> AfterActionReport:
        """Get report by id."""
        report = await self.repository.find_by_id(report_id)
        if not report:
            raise NotFoundError("AfterActionReport", report_id)
        return report

    async def list_reports(
        self,
        skip: int = 0,
        limit: int = 100,
        emergency_event_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[AfterActionReport]:
        """List after-action reports."""
        return await self.repository.list(
            skip=skip,
            limit=limit,
            emergency_event_id=emergency_event_id,
            status=status,
        )

    async def generate_for_event(
        self,
        request: AfterActionGenerateRequest,
        generated_by: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AfterActionReport:
        """Generate report for one emergency event."""
        event = await self.emergency_repository.find_by_id(request.emergency_event_id)
        if not event:
            raise NotFoundError("EmergencyEvent", request.emergency_event_id)

        existing = await self.repository.find_latest_by_event(request.emergency_event_id)
        if existing and not request.force_regenerate:
            return existing

        dispatch_orders = await self.dispatch_repository.list(
            skip=0,
            limit=1000,
            emergency_event_id=request.emergency_event_id,
        )
        sitreps = await self.sitrep_repository.list(
            skip=0,
            limit=300,
            emergency_event_id=request.emergency_event_id,
        )

        kpi = self._compute_kpi(event, dispatch_orders, sitreps)
        timeline = self._build_timeline(event, dispatch_orders, sitreps)

        metadata = {
            **request.metadata,
            "event_code": event.event_code,
            "event_type": event.event_type.value,
            "event_severity": event.severity.value,
        }
        if request_id:
            metadata["request_id"] = request_id

        payload = {
            "report_code": existing.report_code if existing else self._generate_report_code(),
            "emergency_event_id": request.emergency_event_id,
            "title": request.title or f"After-Action Report: {event.title}",
            "summary": request.summary_override
            or self._build_summary(event, kpi, dispatch_orders, sitreps),
            "status": AfterActionStatus.DRAFT.value,
            "timeline": timeline,
            "kpi": kpi.model_dump(),
            "lessons_learned": request.lessons_learned or self._default_lessons(kpi),
            "recommendations": request.recommendations or self._default_recommendations(kpi),
            "generated_by": generated_by,
            "generated_at": datetime.utcnow(),
            "metadata": metadata,
        }

        if existing and request.force_regenerate and existing.id:
            updated = await self.repository.update(str(existing.id), payload)
            if updated:
                return updated

        return await self.repository.create(payload)

    async def update_report(
        self,
        report_id: str,
        payload: AfterActionReportUpdate,
        updated_by: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AfterActionReport:
        """Update draft report."""
        current = await self.get_report_by_id(report_id)
        if current.status != AfterActionStatus.DRAFT:
            raise ValidationError("Only draft after-action reports can be updated")

        update_payload = payload.model_dump(exclude_unset=True)
        metadata = dict(current.metadata or {})
        if updated_by:
            metadata["updated_by"] = updated_by
            metadata["updated_at"] = datetime.utcnow().isoformat()
        if request_id:
            metadata["request_id"] = request_id
        if "metadata" in update_payload and update_payload["metadata"] is not None:
            metadata.update(update_payload["metadata"])
        update_payload["metadata"] = metadata

        updated = await self.repository.update(report_id, update_payload)
        if not updated:
            raise NotFoundError("AfterActionReport", report_id)
        return updated

    async def publish_report(
        self,
        report_id: str,
        published_by: Optional[str],
        request_id: Optional[str] = None,
    ) -> AfterActionReport:
        """Publish a draft report."""
        current = await self.get_report_by_id(report_id)
        if current.status == AfterActionStatus.PUBLISHED:
            return current
        if current.status == AfterActionStatus.ARCHIVED:
            raise ValidationError("Cannot publish archived after-action report")

        updates = {
            "status": AfterActionStatus.PUBLISHED.value,
            "published_by": published_by,
            "published_at": datetime.utcnow(),
        }
        if request_id:
            updates["metadata"] = {**dict(current.metadata or {}), "request_id": request_id}

        updated = await self.repository.update(report_id, updates)
        if not updated:
            raise NotFoundError("AfterActionReport", report_id)
        return updated
