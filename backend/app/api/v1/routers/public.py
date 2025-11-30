"""Public API router (no authentication required)."""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from app.domain.models.asset import Asset
from app.domain.models.incident import Incident, IncidentCreate
from app.domain.services.asset_service import AssetService
from app.domain.services.incident_service import IncidentService
from app.api.v1.dependencies import get_asset_service, get_incident_service
from app.infrastructure.services.qr_service import QRCodeService
from app.core.config import settings
from pydantic import BaseModel

router = APIRouter()


class PublicAssetInfo(BaseModel):
    """Public asset information (limited fields)."""
    asset_code: str
    name: str
    feature_type: str
    category: Optional[str] = None
    status: str
    location: Optional[dict] = None
    qr_code: Optional[str] = None


@router.get("/assets/{code}", response_model=PublicAssetInfo)
async def get_public_asset_info(
    code: str,
    asset_service: AssetService = Depends(get_asset_service)
):
    """Get public asset information via QR/NFC code."""
    # Find asset by code
    from app.infrastructure.database.repositories.mongo_asset_repository import MongoAssetRepository
    from app.infrastructure.database.mongodb import get_database
    db = await get_database()
    repo = MongoAssetRepository(db)
    asset = await repo.find_by_code(code)

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if not asset.public_info_visible:
        raise HTTPException(status_code=403, detail="Asset information is not publicly visible")

    # Generate QR code
    base_url = getattr(settings, "PUBLIC_BASE_URL", "https://openinfra.example.com")
    qr_code = QRCodeService.generate_asset_qr_code(asset.asset_code, base_url)

    return PublicAssetInfo(
        asset_code=asset.asset_code,
        name=asset.name or f"{asset.feature_type}",
        feature_type=asset.feature_type,
        category=asset.category,
        status=asset.status.value,
        location=asset.location.dict() if asset.location else None,
        qr_code=qr_code
    )


@router.post("/incidents", response_model=Incident, status_code=201)
async def create_anonymous_incident(
    incident_data: IncidentCreate,
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Create an anonymous incident report (no authentication required)."""
    # Rate limiting should be implemented here in production
    return await incident_service.create_incident(
        incident_data,
        reported_by=None,
        reporter_type="citizen"
    )


@router.get("/incidents/{incident_id}", response_model=Incident)
async def get_public_incident(
    incident_id: str,
    incident_service: IncidentService = Depends(get_incident_service)
):
    """Get public incident information."""
    incident = await incident_service.get_incident_by_id(incident_id)

    if not incident.public_visible:
        raise HTTPException(status_code=403, detail="Incident is not publicly visible")

    return incident


@router.get("/assets/{code}/qr-code")
async def get_asset_qr_code(
    code: str
):
    """Get QR code image for asset."""
    base_url = getattr(settings, "PUBLIC_BASE_URL", "https://openinfra.example.com")
    qr_code_data = QRCodeService.generate_asset_qr_code(code, base_url)

    return {
        "asset_code": code,
        "qr_code": qr_code_data,
        "url": f"{base_url}/public/assets/{code}"
    }
