"""Maintenance service for managing maintenance workflows."""
from typing import Optional, List
from datetime import datetime, timedelta
from app.domain.models.maintenance import (
    Maintenance, MaintenanceCreate, MaintenanceUpdate,
    MaintenanceStartRequest, MaintenanceCompleteRequest,
    MaintenanceStatus, MaintenanceType, RecurrencePattern
)
from app.domain.repositories.maintenance_repository import MaintenanceRepository
from app.domain.services.budget_service import BudgetService
from app.domain.services.asset_service import AssetService
from app.core.exceptions import NotFoundError, ValidationError
import logging
import uuid

logger = logging.getLogger(__name__)


class MaintenanceService:
    """Maintenance service for business logic."""

    def __init__(
        self,
        maintenance_repository: MaintenanceRepository,
        asset_service: Optional[AssetService] = None,
        budget_service: Optional[BudgetService] = None
    ):
        self.repository = maintenance_repository
        self.asset_service = asset_service
        self.budget_service = budget_service

    def _generate_work_order_number(self) -> str:
        """Generate unique work order number."""
        year = datetime.utcnow().year
        sequence = uuid.uuid4().hex[:6].upper()
        return f"WO-{year}-{sequence}"

    async def create_maintenance(
        self,
        maintenance_data: MaintenanceCreate,
        created_by: str
    ) -> Maintenance:
        """Create a new maintenance work order."""
        # Verify asset exists
        if self.asset_service:
            try:
                await self.asset_service.get_asset_by_id(maintenance_data.asset_id)
            except NotFoundError:
                raise ValidationError(f"Asset {maintenance_data.asset_id} not found")

        # Generate work order number
        work_order_number = self._generate_work_order_number()

        # Check if number exists (unlikely but possible)
        existing = await self.repository.find_by_work_order_number(work_order_number)
        if existing:
            work_order_number = self._generate_work_order_number()

        maintenance_dict = maintenance_data.dict(exclude_unset=True)
        maintenance_dict["work_order_number"] = work_order_number
        maintenance_dict["created_by"] = created_by
        maintenance_dict["status"] = MaintenanceStatus.SCHEDULED.value

        # Calculate next maintenance date if recurring
        if maintenance_data.recurring and maintenance_data.recurrence_pattern:
            maintenance_dict["next_maintenance_date"] = self._calculate_next_maintenance_date(
                maintenance_data.scheduled_date,
                maintenance_data.recurrence_pattern
            )

        maintenance = await self.repository.create(maintenance_dict)

        # Update asset status if needed
        if self.asset_service:
            try:
                await self.asset_service.update_asset(
                    maintenance_data.asset_id,
                    {"status": "maintenance"},
                    updated_by=created_by
                )
            except Exception as e:
                logger.warning(f"Could not update asset status: {e}")

        logger.info(f"Created maintenance work order: {work_order_number}")
        return maintenance

    def _calculate_next_maintenance_date(
        self,
        current_date: datetime,
        pattern: RecurrencePattern
    ) -> datetime:
        """Calculate next maintenance date based on recurrence pattern."""
        if pattern == RecurrencePattern.DAILY:
            return current_date + timedelta(days=1)
        elif pattern == RecurrencePattern.WEEKLY:
            return current_date + timedelta(weeks=1)
        elif pattern == RecurrencePattern.MONTHLY:
            return current_date + timedelta(days=30)
        elif pattern == RecurrencePattern.YEARLY:
            return current_date + timedelta(days=365)
        else:
            return current_date + timedelta(days=30)  # Default to monthly

    async def get_maintenance_by_id(self, maintenance_id: str) -> Maintenance:
        """Get maintenance by ID."""
        maintenance = await self.repository.find_by_id(maintenance_id)
        if not maintenance:
            raise NotFoundError("Maintenance", maintenance_id)
        return maintenance

    async def start_maintenance(
        self,
        maintenance_id: str,
        start_request: MaintenanceStartRequest,
        started_by: str
    ) -> Maintenance:
        """Start maintenance work."""
        maintenance = await self.get_maintenance_by_id(maintenance_id)

        if maintenance.status != MaintenanceStatus.SCHEDULED.value:
            raise ValidationError("Only scheduled maintenance can be started")

        actual_start_time = start_request.actual_start_time or datetime.utcnow()

        updated = await self.repository.update(
            maintenance_id,
            {
                "status": MaintenanceStatus.IN_PROGRESS.value,
                "actual_start_time": actual_start_time,
                "updated_at": datetime.utcnow()
            }
        )

        if not updated:
            raise NotFoundError("Maintenance", maintenance_id)

        logger.info(f"Started maintenance: {maintenance.work_order_number}")
        return updated

    async def complete_maintenance(
        self,
        maintenance_id: str,
        complete_request: MaintenanceCompleteRequest,
        completed_by: str
    ) -> Maintenance:
        """Complete maintenance work."""
        maintenance = await self.get_maintenance_by_id(maintenance_id)

        if maintenance.status != MaintenanceStatus.IN_PROGRESS.value:
            raise ValidationError("Only in-progress maintenance can be completed")

        actual_end_time = complete_request.actual_end_time or datetime.utcnow()

        # Calculate actual duration
        actual_duration = None
        if maintenance.actual_start_time:
            delta = actual_end_time - maintenance.actual_start_time
            actual_duration = int(delta.total_seconds() / 60)

        # Calculate costs
        parts_cost = sum(
            part.total_cost or (part.unit_cost or 0) * part.quantity
            for part in complete_request.parts_used
        )
        total_cost = (
            (complete_request.labor_cost or 0) +
            parts_cost +
            (complete_request.other_costs or 0)
        )

        # Create budget transaction if budget_id exists
        if maintenance.budget_id and self.budget_service:
            try:
                from app.domain.models.budget import BudgetTransactionCreate
                transaction_data = BudgetTransactionCreate(
                    budget_id=maintenance.budget_id,
                    amount=total_cost,
                    transaction_date=actual_end_time,
                    description=f"Maintenance work order {maintenance.work_order_number}",
                    category="labor" if complete_request.labor_cost else "materials",
                    maintenance_record_id=maintenance_id
                )
                await self.budget_service.create_transaction(transaction_data, completed_by)
            except Exception as e:
                logger.warning(f"Could not create budget transaction: {e}")

        # Update maintenance record
        update_dict = {
            "status": MaintenanceStatus.COMPLETED.value,
            "actual_end_time": actual_end_time,
            "actual_duration": actual_duration,
            "work_performed": complete_request.work_performed,
            "parts_used": [part.dict() for part in complete_request.parts_used],
            "tools_used": complete_request.tools_used,
            "labor_cost": complete_request.labor_cost,
            "parts_cost": parts_cost,
            "other_costs": complete_request.other_costs,
            "total_cost": total_cost,
            "quality_check": complete_request.quality_check.dict() if complete_request.quality_check else None,
            "follow_up_required": complete_request.follow_up_required,
            "follow_up_notes": complete_request.follow_up_notes,
            "impact_assessment": complete_request.impact_assessment,
            "completed_by": completed_by,
            "updated_at": datetime.utcnow()
        }

        updated = await self.repository.update(maintenance_id, update_dict)
        if not updated:
            raise NotFoundError("Maintenance", maintenance_id)

        # Update asset status back to operational
        if self.asset_service:
            try:
                await self.asset_service.update_asset(
                    maintenance.asset_id,
                    {"status": "operational"},
                    updated_by=completed_by
                )
            except Exception as e:
                logger.warning(f"Could not update asset status: {e}")

        # Create next recurring maintenance if needed
        if maintenance.recurring and maintenance.recurrence_pattern:
            await self._create_next_recurring_maintenance(maintenance, completed_by)

        logger.info(f"Completed maintenance: {maintenance.work_order_number}")
        return updated

    async def _create_next_recurring_maintenance(
        self,
        completed_maintenance: Maintenance,
        created_by: str
    ):
        """Create next recurring maintenance record."""
        if not completed_maintenance.next_maintenance_date:
            return

        next_maintenance = MaintenanceCreate(
            asset_id=completed_maintenance.asset_id,
            type=completed_maintenance.type,
            priority=completed_maintenance.priority,
            title=f"Recurring: {completed_maintenance.title}",
            description=completed_maintenance.description,
            scheduled_date=completed_maintenance.next_maintenance_date,
            estimated_duration=completed_maintenance.estimated_duration,
            assigned_to=completed_maintenance.assigned_to,
            assigned_team=completed_maintenance.assigned_team,
            supervisor_id=completed_maintenance.supervisor_id,
            budget_id=completed_maintenance.budget_id,
            recurring=True,
            recurrence_pattern=completed_maintenance.recurrence_pattern
        )

        await self.create_maintenance(next_maintenance, created_by)

    async def assign_maintenance(
        self,
        maintenance_id: str,
        assigned_to: str,
        assigned_by: str
    ) -> Maintenance:
        """Assign maintenance to a technician."""
        maintenance = await self.get_maintenance_by_id(maintenance_id)

        updated = await self.repository.update(
            maintenance_id,
            {
                "assigned_to": assigned_to,
                "updated_at": datetime.utcnow()
            }
        )

        if not updated:
            raise NotFoundError("Maintenance", maintenance_id)

        logger.info(f"Assigned maintenance {maintenance.work_order_number} to {assigned_to}")
        return updated

    async def cancel_maintenance(
        self,
        maintenance_id: str,
        cancellation_reason: str,
        cancelled_by: str
    ) -> Maintenance:
        """Cancel maintenance work order."""
        maintenance = await self.get_maintenance_by_id(maintenance_id)

        if maintenance.status == MaintenanceStatus.COMPLETED.value:
            raise ValidationError("Cannot cancel completed maintenance")

        updated = await self.repository.update(
            maintenance_id,
            {
                "status": MaintenanceStatus.CANCELLED.value,
                "cancellation_reason": cancellation_reason,
                "cancelled_by": cancelled_by,
                "updated_at": datetime.utcnow()
            }
        )

        if not updated:
            raise NotFoundError("Maintenance", maintenance_id)

        # Update asset status back to operational
        if self.asset_service:
            try:
                await self.asset_service.update_asset(
                    maintenance.asset_id,
                    {"status": "operational"},
                    updated_by=cancelled_by
                )
            except Exception as e:
                logger.warning(f"Could not update asset status: {e}")

        logger.info(f"Cancelled maintenance: {maintenance.work_order_number}")
        return updated

    async def add_photos(
        self,
        maintenance_id: str,
        photo_urls: List[str],
        photo_type: str = "after"  # "before" | "after"
    ) -> Maintenance:
        """Add photos to maintenance record."""
        maintenance = await self.get_maintenance_by_id(maintenance_id)

        update_dict = {}
        if photo_type == "before":
            update_dict["before_photos"] = maintenance.before_photos + photo_urls
        else:
            update_dict["after_photos"] = maintenance.after_photos + photo_urls

        updated = await self.repository.update(maintenance_id, update_dict)
        if not updated:
            raise NotFoundError("Maintenance", maintenance_id)
        return updated

    async def list_maintenance(
        self,
        skip: int = 0,
        limit: int = 100,
        asset_id: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Maintenance]:
        """List maintenance records with filtering."""
        return await self.repository.list(skip, limit, asset_id, status, assigned_to, priority)

    async def get_upcoming_maintenance(self, days: int = 7) -> List[Maintenance]:
        """Get upcoming maintenance records."""
        return await self.repository.find_upcoming(days)

    async def update_maintenance(
        self,
        maintenance_id: str,
        updates: MaintenanceUpdate
    ) -> Maintenance:
        """Update maintenance record."""
        maintenance = await self.get_maintenance_by_id(maintenance_id)

        if maintenance.status == MaintenanceStatus.COMPLETED.value:
            raise ValidationError("Cannot update completed maintenance")

        update_dict = updates.dict(exclude_unset=True)
        updated = await self.repository.update(maintenance_id, update_dict)
        if not updated:
            raise NotFoundError("Maintenance", maintenance_id)
        return updated
