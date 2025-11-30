"""Report service for managing reports."""
from typing import Optional, List
from datetime import datetime
import uuid
from app.domain.models.report import Report, ReportCreate, ReportStatus
from app.domain.repositories.report_repository import ReportRepository
from app.infrastructure.reports.report_generator import ReportGenerator
from app.core.exceptions import NotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)


class ReportService:
    """Report service for business logic."""

    def __init__(
        self,
        report_repository: ReportRepository,
        report_generator: ReportGenerator
    ):
        self.repository = report_repository
        self.generator = report_generator

    def _generate_report_code(self) -> str:
        """Generate unique report code."""
        year = datetime.utcnow().year
        sequence = uuid.uuid4().hex[:8].upper()
        return f"RPT-{year}-{sequence}"

    async def create_report(
        self,
        report_data: ReportCreate,
        created_by: str
    ) -> Report:
        """Create a new report."""
        report_code = self._generate_report_code()

        report_dict = report_data.dict(exclude_unset=True)
        report_dict["report_code"] = report_code
        report_dict["created_by"] = created_by
        report_dict["status"] = ReportStatus.PENDING.value

        report = await self.repository.create(report_dict)

        # If not scheduled, generate immediately
        if not report_data.scheduled:
            await self.generate_report(str(report.id))

        logger.info(f"Created report: {report.report_code}")
        return report

    async def generate_report(self, report_id: str) -> Report:
        """Generate report file."""
        report = await self.repository.find_by_id(report_id)
        if not report:
            raise NotFoundError("Report", report_id)

        # Update status to generating
        await self.repository.update(
            report_id,
            {
                "status": ReportStatus.GENERATING.value,
                "updated_at": datetime.utcnow()
            }
        )

        try:
            # Generate report file
            file_url = await self.generator.generate_report(report)

            # Update report with file URL
            updated = await self.repository.update(
                report_id,
                {
                    "status": ReportStatus.COMPLETED.value,
                    "file_url": file_url,
                    "generated_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            )

            if not updated:
                raise NotFoundError("Report", report_id)

            logger.info(f"Generated report: {report.report_code}")
            return updated
        except Exception as e:
            # Update status to failed
            await self.repository.update(
                report_id,
                {
                    "status": ReportStatus.FAILED.value,
                    "error_message": str(e),
                    "updated_at": datetime.utcnow()
                }
            )
            logger.error(f"Error generating report {report.report_code}: {e}")
            raise

    async def get_report_by_id(self, report_id: str) -> Report:
        """Get report by ID."""
        report = await self.repository.find_by_id(report_id)
        if not report:
            raise NotFoundError("Report", report_id)
        return report

    async def list_reports(
        self,
        skip: int = 0,
        limit: int = 100,
        type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Report]:
        """List reports with filtering."""
        return await self.repository.list(skip, limit, type, status)

    async def get_scheduled_reports(self) -> List[Report]:
        """Get reports that need to be generated."""
        return await self.repository.find_scheduled_reports()
