"""Celery tasks for report generation."""

from app.celery_app import app as celery_app
from app.infrastructure.database.mongodb import get_database, db as database_manager
from app.domain.services.report_service import ReportService
from app.domain.repositories.report_repository import ReportRepository
from app.infrastructure.database.repositories.mongo_report_repository import (
    MongoReportRepository,
)
from app.infrastructure.reports.report_generator import ReportGenerator
import logging
import asyncio

logger = logging.getLogger(__name__)


def run_async(coro):
    """
    Safely run async coroutine in Celery task.
    Handles event loop creation properly for prefork workers.

    In Celery prefork workers, each worker process is forked, so we need
    to create a fresh event loop. Motor requires a valid event loop to work.
    """
    # In prefork workers, there should be no existing event loop
    # Create a new one for this task BEFORE any Motor operations
    loop = None
    try:
        # Try to get existing event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Loop is closed")
        except RuntimeError:
            # No event loop or it's closed - create new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Ensure database connection uses this event loop
        # Motor client will automatically use the current event loop
        if database_manager.client is None:
            database_manager.connect()

        # Run the coroutine
        return loop.run_until_complete(coro)
    finally:
        # Note: We don't close the loop here because Motor connections
        # may need to reuse it. The loop will be cleaned up when the process exits.
        pass


async def _generate_scheduled_reports_async():
    """Async implementation of generate scheduled reports."""
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


@celery_app.task(name="generate_scheduled_reports")
def generate_scheduled_reports():
    """Generate scheduled reports."""
    try:
        result = run_async(_generate_scheduled_reports_async())
        if asyncio.iscoroutine(result):
            raise ValueError("Function returned a coroutine instead of a value")
        return result
    except Exception as e:
        logger.error(f"Error in generate_scheduled_reports task: {e}", exc_info=True)
        raise
