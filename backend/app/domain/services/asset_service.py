"""Asset domain service."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.domain.models.asset import Asset, AssetCreate, AssetUpdate, AssetStatus, AssetCondition
from app.domain.repositories.asset_repository import AssetRepository
from app.domain.services.audit_service import AuditService
from app.core.exceptions import ConflictError, NotFoundError
import logging

logger = logging.getLogger(__name__)


class AssetService:
    """Asset service for business logic."""

    def __init__(
        self,
        asset_repository: AssetRepository,
        audit_service: Optional[AuditService] = None,
        maintenance_repository: Optional[Any] = None,
        incident_repository: Optional[Any] = None
    ):
        self.repository = asset_repository
        self.audit_service = audit_service
        self.maintenance_repository = maintenance_repository
        self.incident_repository = incident_repository

    async def create_asset(
        self,
        asset_data: AssetCreate,
        created_by: Optional[str] = None
    ) -> Asset:
        """Create a new asset."""
        # Check if asset_code exists
        existing = await self.repository.find_by_code(asset_data.asset_code)
        if existing:
            raise ConflictError(f"Asset code '{asset_data.asset_code}' already exists")

        # Convert to dict
        asset_dict = asset_data.dict(exclude_unset=True)
        asset_dict["created_by"] = created_by

        # Create asset
        asset = await self.repository.create(asset_dict)

        # Log creation
        if self.audit_service:
            await self.audit_service.log_change(
                resource_type="asset",
                resource_id=str(asset.id),
                action="create",
                user_id=created_by,
                description=f"Created asset {asset.asset_code}"
            )

        logger.info(f"Created asset: {asset.asset_code}")
        return asset

    async def get_asset_by_id(self, asset_id: str) -> Asset:
        """Get asset by ID."""
        asset = await self.repository.find_by_id(asset_id)
        if not asset:
            raise NotFoundError("Asset", asset_id)
        return asset

    async def update_asset(
        self,
        asset_id: str,
        updates: AssetUpdate,
        updated_by: Optional[str] = None
    ) -> Asset:
        """Update asset with audit trail."""
        # Get current asset state
        current_asset = await self.get_asset_by_id(asset_id)

        # Prepare updates
        update_dict = updates.dict(exclude_unset=True)
        update_dict["updated_by"] = updated_by

        # Update asset
        updated_asset = await self.repository.update(asset_id, update_dict)
        if not updated_asset:
            raise NotFoundError("Asset", asset_id)

        # Log changes
        if self.audit_service:
            changes = {
                "before": current_asset.dict(exclude={"id", "created_at", "updated_at"}),
                "after": updated_asset.dict(exclude={"id", "created_at", "updated_at"})
            }
            await self.audit_service.log_change(
                resource_type="asset",
                resource_id=asset_id,
                action="update",
                user_id=updated_by,
                changes=changes,
                description=f"Updated asset {updated_asset.asset_code}"
            )

        return updated_asset

    async def delete_asset(
        self,
        asset_id: str,
        deleted_by: Optional[str] = None
    ) -> bool:
        """Delete asset (soft delete)."""
        asset = await self.get_asset_by_id(asset_id)
        result = await self.repository.delete(asset_id)

        if result and self.audit_service:
            await self.audit_service.log_change(
                resource_type="asset",
                resource_id=asset_id,
                action="delete",
                user_id=deleted_by,
                description=f"Deleted asset {asset.asset_code}"
            )

        return result

    async def list_assets(
        self,
        skip: int = 0,
        limit: int = 100,
        feature_type: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Asset]:
        """List assets with filtering."""
        filters = {}
        if feature_type:
            filters["feature_type"] = feature_type
        if status:
            filters["status"] = status
        if category:
            filters["category"] = category

        return await self.repository.list(skip, limit, filters)

    async def add_attachment(
        self,
        asset_id: str,
        file_url: str,
        file_name: str,
        file_type: str,
        uploaded_by: str
    ) -> Asset:
        """Add attachment to asset."""
        asset = await self.get_asset_by_id(asset_id)

        attachment = {
            "file_name": file_name,
            "file_url": file_url,
            "file_type": file_type,
            "uploaded_at": datetime.utcnow(),
            "uploaded_by": uploaded_by
        }

        await self.repository.add_attachment(asset_id, attachment)

        # Log change
        if self.audit_service:
            await self.audit_service.log_change(
                resource_type="asset",
                resource_id=asset_id,
                action="update",
                user_id=uploaded_by,
                description=f"Added attachment {file_name} to asset {asset.asset_code}"
            )

        return await self.get_asset_by_id(asset_id)

    async def remove_attachment(
        self,
        asset_id: str,
        attachment_url: str,
        removed_by: str
    ) -> Asset:
        """Remove attachment from asset."""
        asset = await self.get_asset_by_id(asset_id)
        await self.repository.remove_attachment(asset_id, attachment_url)

        # Log change
        if self.audit_service:
            await self.audit_service.log_change(
                resource_type="asset",
                resource_id=asset_id,
                action="update",
                user_id=removed_by,
                description=f"Removed attachment from asset {asset.asset_code}"
            )

        return await self.get_asset_by_id(asset_id)

    async def get_asset_history(
        self,
        asset_id: str,
        limit: int = 100
    ) -> List:
        """Get asset change history."""
        if not self.audit_service:
            return []
        return await self.audit_service.get_resource_history("asset", asset_id, limit)

    async def calculate_health_score(
        self,
        asset_id: str
    ) -> Dict[str, Any]:
        """Calculate health score for an asset based on multiple factors."""
        asset = await self.get_asset_by_id(asset_id)

        # Base score components
        condition_score = self._get_condition_score(asset.condition)
        status_score = self._get_status_score(asset.status)

        # Maintenance factors (last 90 days)
        maintenance_score = 100.0
        if self.maintenance_repository:
            maintenance_score = await self._calculate_maintenance_score(asset_id)

        # Incident factors (last 90 days)
        incident_score = 100.0
        if self.incident_repository:
            incident_score = await self._calculate_incident_score(asset_id)

        # Age/depreciation factor
        age_score = self._calculate_age_score(asset)

        # Weighted calculation
        # Condition: 30%, Status: 20%, Maintenance: 25%, Incidents: 15%, Age: 10%
        health_score = (
            condition_score * 0.30 +
            status_score * 0.20 +
            maintenance_score * 0.25 +
            incident_score * 0.15 +
            age_score * 0.10
        )

        # Round to 2 decimal places and ensure it's between 0 and 100
        health_score = max(0.0, min(100.0, round(health_score, 2)))

        # Determine health status
        if health_score >= 80:
            health_status = "excellent"
        elif health_score >= 60:
            health_status = "good"
        elif health_score >= 40:
            health_status = "fair"
        else:
            health_status = "poor"

        return {
            "health_score": health_score,
            "health_status": health_status,
            "breakdown": {
                "condition_score": condition_score,
                "status_score": status_score,
                "maintenance_score": maintenance_score,
                "incident_score": incident_score,
                "age_score": age_score
            }
        }

    def _get_condition_score(self, condition: Optional[AssetCondition]) -> float:
        """Get score based on asset condition."""
        if not condition:
            return 75.0  # Default to good if not specified

        condition_scores = {
            AssetCondition.EXCELLENT: 100.0,
            AssetCondition.GOOD: 75.0,
            AssetCondition.FAIR: 50.0,
            AssetCondition.POOR: 25.0
        }
        return condition_scores.get(condition, 75.0)

    def _get_status_score(self, status: AssetStatus) -> float:
        """Get score based on asset status."""
        status_scores = {
            AssetStatus.OPERATIONAL: 100.0,
            AssetStatus.MAINTENANCE: 70.0,
            AssetStatus.DAMAGED: 30.0,
            AssetStatus.RETIRED: 0.0
        }
        return status_scores.get(status, 100.0)

    async def _calculate_maintenance_score(self, asset_id: str) -> float:
        """Calculate score based on maintenance history (last 90 days)."""
        try:
            from app.domain.models.maintenance import MaintenanceStatus

            cutoff_date = datetime.utcnow() - timedelta(days=90)

            # Get all maintenance records for this asset
            maintenance_records = await self.maintenance_repository.list(
                skip=0,
                limit=1000,
                asset_id=asset_id
            )

            # Filter to last 90 days
            recent_maintenance = [
                m for m in maintenance_records
                if m.created_at >= cutoff_date
            ]

            if not recent_maintenance:
                return 100.0  # No maintenance needed is good

            # Calculate completion rate
            # Handle both enum and string status values
            completed = sum(
                1 for m in recent_maintenance
                if (hasattr(m.status, 'value') and m.status.value == MaintenanceStatus.COMPLETED.value) or
                   (isinstance(m.status, str) and m.status == MaintenanceStatus.COMPLETED.value) or
                   m.status == MaintenanceStatus.COMPLETED
            )
            total = len(recent_maintenance)
            completion_rate = (completed / total) * 100 if total > 0 else 100.0

            # Check for overdue maintenance
            overdue_count = sum(
                1 for m in recent_maintenance
                if (
                    (hasattr(m.status, 'value') and m.status.value in [MaintenanceStatus.SCHEDULED.value, MaintenanceStatus.IN_PROGRESS.value]) or
                    (isinstance(m.status, str) and m.status in [MaintenanceStatus.SCHEDULED.value, MaintenanceStatus.IN_PROGRESS.value]) or
                    m.status in [MaintenanceStatus.SCHEDULED, MaintenanceStatus.IN_PROGRESS]
                ) and m.scheduled_date and m.scheduled_date < datetime.utcnow()
            )

            # Penalize overdue maintenance
            overdue_penalty = min(overdue_count * 10, 50)  # Max 50 point penalty

            # Base score from completion rate, minus overdue penalty
            score = completion_rate - overdue_penalty

            return max(0.0, min(100.0, score))
        except Exception as e:
            logger.warning(f"Error calculating maintenance score: {e}")
            return 75.0  # Default to good on error

    async def _calculate_incident_score(self, asset_id: str) -> float:
        """Calculate score based on incident history (last 90 days)."""
        try:
            from app.domain.models.incident import IncidentSeverity, IncidentStatus

            cutoff_date = datetime.utcnow() - timedelta(days=90)

            # Get all incidents for this asset
            incidents = await self.incident_repository.list(
                skip=0,
                limit=1000,
                asset_id=asset_id
            )

            # Filter to last 90 days
            recent_incidents = [
                i for i in incidents
                if i.reported_at and i.reported_at >= cutoff_date
            ]

            if not recent_incidents:
                return 100.0  # No incidents is excellent

            # Calculate severity penalties
            severity_penalties = {
                IncidentSeverity.LOW.value: 5,
                IncidentSeverity.MEDIUM.value: 15,
                IncidentSeverity.HIGH.value: 30,
                IncidentSeverity.CRITICAL.value: 50
            }

            total_penalty = 0
            for incident in recent_incidents:
                severity_value = (
                    incident.severity.value if hasattr(incident.severity, 'value')
                    else str(incident.severity).lower()
                )
                total_penalty += severity_penalties.get(severity_value, 10)

            # Check for unresolved incidents
            resolved_statuses = [IncidentStatus.RESOLVED.value, IncidentStatus.CLOSED.value]
            unresolved = sum(
                1 for i in recent_incidents
                if (
                    (hasattr(i.status, 'value') and i.status.value not in resolved_statuses) or
                    (isinstance(i.status, str) and i.status not in resolved_statuses) or
                    (i.status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED])
                )
            )
            unresolved_penalty = unresolved * 20  # Additional penalty for unresolved

            # Start with 100 and subtract penalties
            score = 100.0 - total_penalty - unresolved_penalty

            return max(0.0, min(100.0, score))
        except Exception as e:
            logger.warning(f"Error calculating incident score: {e}")
            return 75.0  # Default to good on error

    def _calculate_age_score(self, asset: Asset) -> float:
        """Calculate score based on asset age and depreciation."""
        try:
            # If no creation date, default to good
            if not asset.created_at:
                return 75.0

            age_days = (datetime.utcnow() - asset.created_at).days
            age_years = age_days / 365.0

            # Base score decreases with age
            # New assets (0-1 year): 100
            # 1-5 years: 90-100
            # 5-10 years: 70-90
            # 10-20 years: 50-70
            # 20+ years: 30-50

            if age_years < 1:
                base_score = 100.0
            elif age_years < 5:
                base_score = 100.0 - (age_years - 1) * 2.5  # 100 to 90
            elif age_years < 10:
                base_score = 90.0 - (age_years - 5) * 4  # 90 to 70
            elif age_years < 20:
                base_score = 70.0 - (age_years - 10) * 2  # 70 to 50
            else:
                base_score = max(30.0, 50.0 - (age_years - 20) * 1)  # 50 to 30

            # Apply depreciation rate if available
            if asset.depreciation_rate and asset.depreciation_rate > 0:
                depreciation_factor = min(asset.depreciation_rate * age_years / 100, 0.3)
                base_score = base_score * (1 - depreciation_factor)

            return max(0.0, min(100.0, base_score))
        except Exception as e:
            logger.warning(f"Error calculating age score: {e}")
            return 75.0  # Default to good on error
