"""Celery tasks for report generation."""
from app.celery_app import celery_app
from app.infrastructure.database.mongodb import get_database
from app.domain.services.report_service import ReportService
from app.domain.repositories.report_repository import ReportRepository
from app.infrastructure.database.repositories.mongo_report_repository import MongoReportRepository
from app.infrastructure.reports.report_generator import ReportGenerator
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="generate_scheduled_reports")
async def generate_scheduled_reports():
    """Generate scheduled reports."""
    try:
        db = await get_database()
        report_repo = MongoReportRepository(db)
        report_generator = ReportGenerator()
        report_service = ReportService(report_repo, report_generator)

        # Get scheduled reports
        scheduled_reports = await report_service.get_scheduled_reports()

        generated = 0
        for report in scheduled_reports:
            try:
                await report_service.generate_report(str(report.id))
                generated += 1
            except Exception as e:
                logger.error(f"Error generating scheduled report {report.report_code}: {e}")
                continue

        logger.info(f"Generated {generated} scheduled reports")
        return {"generated": generated, "total": len(scheduled_reports)}
    except Exception as e:
        logger.error(f"Error in generate_scheduled_reports task: {e}")
        raise
