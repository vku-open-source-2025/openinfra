"""Hazard layers API router."""

import asyncio
import re
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.v1.dependencies import get_hazard_layer_service
from app.api.v1.middleware import get_current_user
from app.domain.models.hazard_layer import HazardLayer, HazardLayerCreate, HazardLayerUpdate
from app.domain.models.user import User, UserRole
from app.domain.services.hazard_layer_service import HazardLayerService
from app.services.hazard_ingest_service import HazardIngestService

router = APIRouter()


class PolygonQuery(BaseModel):
    """Polygon filter payload."""

    polygon: dict = Field(description="GeoJSON Polygon/MultiPolygon")
    limit: int = Field(default=500, ge=1, le=2000)


class ExpireResponse(BaseModel):
    """Response for expire stale hazards endpoint."""

    updated: int


class FeedLastCheckStatus(BaseModel):
    """Last reachability check details for a feed."""

    checked: bool
    checked_at: Optional[str] = None
    status: str
    reachable: Optional[bool] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    timeout_seconds: float
    error: Optional[str] = None


class FeedIngestStatus(BaseModel):
    """Configuration and health for one hazard feed."""

    configured: bool
    url_present: bool
    last_check: FeedLastCheckStatus


class OverallIngestStatus(BaseModel):
    """Aggregated ingest readiness status."""

    status: str
    ready: bool
    configured_feeds: int
    total_feeds: int
    reachability_checked: bool
    checked_at: str


class HazardIngestStatusResponse(BaseModel):
    """Hazard ingest status response model."""

    feeds: Dict[str, FeedIngestStatus]
    overall: OverallIngestStatus


def _ensure_operator(user: User):
    """Allow only admin and technician users for write operations."""
    if user.role not in {UserRole.ADMIN, UserRole.TECHNICIAN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for hazard operations",
        )


@router.get("", response_model=List[HazardLayer])
async def list_hazards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(default=True),
    event_type: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    district: Optional[str] = Query(default=None),
    ward: Optional[str] = Query(default=None),
    service: HazardLayerService = Depends(get_hazard_layer_service),
):
    """List hazards with optional filtering."""
    return await service.list_hazards(
        skip=skip,
        limit=limit,
        active_only=active_only,
        event_type=event_type,
        severity=severity,
        source=source,
        district=district,
        ward=ward,
    )


@router.get("/geo/near", response_model=List[HazardLayer])
async def list_hazards_nearby(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_m: int = Query(default=5000, ge=100, le=200000),
    limit: int = Query(default=100, ge=1, le=500),
    service: HazardLayerService = Depends(get_hazard_layer_service),
):
    """List active hazards near a coordinate."""
    return await service.list_hazards_nearby(
        latitude=lat,
        longitude=lng,
        radius_meters=radius_m,
        limit=limit,
    )


@router.post("/geo/in-polygon", response_model=List[HazardLayer])
async def list_hazards_in_polygon(
    payload: PolygonQuery,
    service: HazardLayerService = Depends(get_hazard_layer_service),
):
    """List active hazards inside a polygon geometry."""
    return await service.list_hazards_in_polygon(payload.polygon, payload.limit)


@router.get("/ingest/status", response_model=HazardIngestStatusResponse)
async def get_hazard_ingest_status(
    check_reachability: bool = Query(
        default=True,
        description="Run timeout-safe upstream reachability checks",
    ),
    timeout_seconds: Optional[float] = Query(
        default=None,
        ge=0.1,
        le=60,
        description="Optional timeout override for feed probe requests",
    ),
    allow_get_fallback: bool = Query(
        default=True,
        description="Fallback to GET when upstream does not support HEAD",
    ),
):
    """Get NCHMF/VNDMS ingest configuration and readiness status."""
    ingest_service = HazardIngestService()
    return await ingest_service.get_ingest_status(
        check_reachability=check_reachability,
        timeout_seconds=timeout_seconds,
        allow_get_fallback=allow_get_fallback,
    )


# ---------------------------------------------------------------------------
# VNDMS Live Hazard Map
# ---------------------------------------------------------------------------

_VNDMS_URLS: List[Dict[str, Any]] = [
    {"url": "https://vndms.dmptc.gov.vn/water_level?lv=1", "warning_type": "water_level", "warning_level": 1},
    {"url": "https://vndms.dmptc.gov.vn/water_level?lv=2", "warning_type": "water_level", "warning_level": 2},
    {"url": "https://vndms.dmptc.gov.vn/water_level?lv=3", "warning_type": "water_level", "warning_level": 3},
    {"url": "https://vndms.dmptc.gov.vn/warning_rain?lv1=50&lv2=100&types=1", "warning_type": "warning_rain", "warning_level": 1},
    {"url": "https://vndms.dmptc.gov.vn/warning_rain?lv1=100&lv2=200&types=1", "warning_type": "warning_rain", "warning_level": 2},
    {"url": "https://vndms.dmptc.gov.vn/warning_rain?lv1=200&lv2=300&types=1", "warning_type": "warning_rain", "warning_level": 3},
    {"url": "https://vndms.dmptc.gov.vn/warning_rain?lv1=300&lv2=1000&types=1", "warning_type": "warning_rain", "warning_level": 4},
    {"url": "https://vndms.dmptc.gov.vn/warning_wind?lv1=6&lv2=7&types=1", "warning_type": "warning_wind", "warning_level": 1},
    {"url": "https://vndms.dmptc.gov.vn/warning_wind?lv1=8&lv2=9&types=1", "warning_type": "warning_wind", "warning_level": 2},
]

_EVENT_DISASTER_URL = "https://vndms.dmptc.gov.vn/EventDisaster/List"

_DISASTER_TYPE_MAP: Dict[int, str] = {
    1: "warning_flood",
    2: "warning_earthquake",
    3: "warning_flood",
}


def _derive_severity(warning_type: str, warning_level: int) -> str:
    """Derive severity string from type and level."""
    if warning_type == "water_level":
        if warning_level == 1:
            return "low"
        elif warning_level == 2:
            return "medium"
        else:
            return "high"
    elif warning_type in ("warning_rain", "warning_wind"):
        return "high" if warning_level >= 3 else "medium"
    return "medium"


def _extract_value(popup_info: str) -> str:
    """Extract numeric value string from popupInfo text."""
    if not popup_info:
        return ""
    match = re.search(r"\(([0-9.]+)\s*\(?\s*m\)?", popup_info)
    if match:
        return f"{match.group(1)}m"
    match = re.search(r"([0-9.]+)\s*mm", popup_info, re.IGNORECASE)
    if match:
        return f"{match.group(1)}mm"
    match = re.search(r"([0-9.]+)\s*m/s", popup_info, re.IGNORECASE)
    if match:
        return f"{match.group(1)}m/s"
    match = re.search(r"([0-9.]+)", popup_info)
    if match:
        return match.group(1)
    return ""


async def _fetch_geojson(
    client: httpx.AsyncClient,
    meta: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Fetch one GeoJSON-style endpoint and return normalised items."""
    try:
        resp = await client.get(meta["url"], timeout=8.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    items: List[Dict[str, Any]] = []
    features = data.get("features") if isinstance(data, dict) else []
    if not features:
        return []

    for i, feat in enumerate(features):
        try:
            coords = feat["geometry"]["coordinates"]
            lon, lat = float(coords[0]), float(coords[1])
            props = feat.get("properties") or {}
            label = props.get("label") or props.get("name") or ""
            popup = props.get("popupInfo") or ""
            items.append(
                {
                    "id": f"{meta['warning_type']}_lv{meta['warning_level']}_{i}",
                    "lat": lat,
                    "lon": lon,
                    "label": label,
                    "warning_type": meta["warning_type"],
                    "warning_level": meta["warning_level"],
                    "severity": _derive_severity(meta["warning_type"], meta["warning_level"]),
                    "value": _extract_value(popup),
                    "popupInfo": popup,
                    "source": "vndms",
                }
            )
        except Exception:
            continue
    return items


async def _fetch_event_disasters(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """Fetch EventDisaster/List and return normalised items."""
    try:
        resp = await client.get(_EVENT_DISASTER_URL, timeout=8.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    if not isinstance(data, list):
        data = data.get("data") or data.get("features") or []

    items: List[Dict[str, Any]] = []
    for i, obj in enumerate(data):
        try:
            lat = float(obj.get("lat") or obj.get("latitude") or 0)
            lon = float(obj.get("lon") or obj.get("longitude") or 0)
            if lat == 0 and lon == 0:
                continue
            label = obj.get("label") or obj.get("name") or obj.get("kv_anhhuong") or ""
            disaster_id = (obj.get("disaster") or {}).get("id") or 0
            wtype = _DISASTER_TYPE_MAP.get(int(disaster_id), "warning_flood")
            items.append(
                {
                    "id": f"event_disaster_{i}",
                    "lat": lat,
                    "lon": lon,
                    "label": label,
                    "warning_type": wtype,
                    "warning_level": 1,
                    "severity": "high",
                    "value": "",
                    "popupInfo": obj.get("kv_anhhuong") or "",
                    "source": "vndms",
                }
            )
        except Exception:
            continue
    return items


@router.get("/vndms-live")
async def get_vndms_live_hazards() -> List[Dict[str, Any]]:
    """Crawl VNDMS APIs in parallel and return unified hazard list."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [_fetch_geojson(client, meta) for meta in _VNDMS_URLS]
        tasks.append(_fetch_event_disasters(client))  # type: ignore[arg-type]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_items: List[Dict[str, Any]] = []
    for result in results:
        if isinstance(result, list):
            all_items.extend(result)

    # Deduplicate by (label, warning_type) — keep first occurrence
    seen: set = set()
    deduped: List[Dict[str, Any]] = []
    for item in all_items:
        key = (item.get("label", ""), item.get("warning_type", ""))
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    return deduped


@router.get("/{hazard_db_id}", response_model=HazardLayer)
async def get_hazard_by_id(
    hazard_db_id: str,
    service: HazardLayerService = Depends(get_hazard_layer_service),
):
    """Get one hazard by database id."""
    return await service.get_hazard_by_id(hazard_db_id)


@router.post("", response_model=HazardLayer, status_code=status.HTTP_201_CREATED)
async def create_hazard(
    payload: HazardLayerCreate,
    current_user: User = Depends(get_current_user),
    service: HazardLayerService = Depends(get_hazard_layer_service),
):
    """Create hazard manually from command center."""
    _ensure_operator(current_user)
    return await service.create_hazard(payload)


@router.put("/{hazard_db_id}", response_model=HazardLayer)
async def update_hazard(
    hazard_db_id: str,
    payload: HazardLayerUpdate,
    current_user: User = Depends(get_current_user),
    service: HazardLayerService = Depends(get_hazard_layer_service),
):
    """Update hazard details."""
    _ensure_operator(current_user)
    return await service.update_hazard(hazard_db_id, payload)


@router.post("/expire-stale", response_model=ExpireResponse)
async def expire_stale_hazards(
    current_user: User = Depends(get_current_user),
    service: HazardLayerService = Depends(get_hazard_layer_service),
):
    """Deactivate expired hazards."""
    _ensure_operator(current_user)
    updated = await service.deactivate_expired()
    return ExpireResponse(updated=updated)
