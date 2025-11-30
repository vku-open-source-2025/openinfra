"""Reports API router."""
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import List, Optional
from app.domain.models.report import Report, ReportCreate
from app.domain.services.report_service import ReportService
from app.api.v1.dependencies import get_report_service
from app.api.v1.middleware import get_current_user
from app.domain.models.user import User

router = APIRouter()


@router.get("", response_model=List[Report])
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    type: Optional[str] = None,
    status: Optional[str] = None,
    report_service: ReportService = Depends(get_report_service)
):
    """List reports."""
    return await report_service.list_reports(skip, limit, type, status)


@router.post("", response_model=Report, status_code=201)
async def create_report(
    report_data: ReportCreate,
    current_user: User = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service)
):
    """Create a new report."""
    return await report_service.create_report(report_data, str(current_user.id))


@router.get("/{report_id}", response_model=Report)
async def get_report(
    report_id: str,
    report_service: ReportService = Depends(get_report_service)
):
    """Get report details."""
    return await report_service.get_report_by_id(report_id)


@router.post("/{report_id}/generate", response_model=Report)
async def generate_report(
    report_id: str,
    report_service: ReportService = Depends(get_report_service)
):
    """Generate report file."""
    return await report_service.generate_report(report_id)


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    report_service: ReportService = Depends(get_report_service)
):
    """Download report file."""
    report = await report_service.get_report_by_id(report_id)

    if report.status != "completed" or not report.file_url:
        raise HTTPException(status_code=404, detail="Report not available")

    # In production, return file from storage
    return {
        "file_url": report.file_url,
        "report_code": report.report_code,
        "format": report.format.value
    }
