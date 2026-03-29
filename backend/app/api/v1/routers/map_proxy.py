"""Map tile proxy — hides VietMap API key from frontend."""

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from app.core.config import settings

router = APIRouter()

_VIETMAP_TILE_URL = "https://maps.vietmap.vn/maps/tiles/tm/{z}/{x}/{y}@2x.png"


@router.get("/tiles/{z}/{x}/{y}")
async def proxy_tile(z: int, x: int, y: int):
    """Proxy VietMap tile requests so the API key stays server-side."""
    api_key = settings.VIETMAP_API_KEY
    if not api_key:
        raise HTTPException(status_code=503, detail="VietMap API key not configured")

    url = _VIETMAP_TILE_URL.format(z=z, x=x, y=y)
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params={"apikey": api_key})

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Upstream tile error")

    return Response(
        content=resp.content,
        media_type=resp.headers.get("content-type", "image/png"),
        headers={
            "Cache-Control": "public, max-age=86400",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/config")
async def map_config():
    """Return map tile URL template for the frontend (no key exposed)."""
    has_vietmap = bool(settings.VIETMAP_API_KEY)
    if has_vietmap:
        return {
            "tileUrl": "/api/v1/map/tiles/{z}/{x}/{y}",
            "attribution": '&copy; <a href="https://vietmap.vn">VietMap</a> | Hoang Sa and Truong Sa belong to Vietnam 🇻🇳',
            "maxZoom": 20,
            "provider": "vietmap",
        }
    return {
        "tileUrl": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attribution": '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        "maxZoom": 20,
        "maxNativeZoom": 16,
        "provider": "osm",
    }
