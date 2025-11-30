"""OpenStreetMap Nominatim API integration."""
import httpx
from typing import Optional, Dict, Any, List
from app.domain.value_objects.coordinates import Coordinates
from app.core.config import settings
from app.infrastructure.cache.redis_cache import cache
import logging
import json

logger = logging.getLogger(__name__)


class OSMService:
    """OpenStreetMap Nominatim service."""

    def __init__(self):
        self.base_url = settings.OSM_NOMINATIM_URL
        self.timeout = 10.0

    async def geocode(
        self,
        address: str,
        country: str = "Vietnam"
    ) -> Optional[Coordinates]:
        """Convert address to coordinates."""
        # Check cache first
        cache_key = f"geocode:{address}:{country}"
        try:
            cached = await cache.get(cache_key)
            if cached:
                if isinstance(cached, dict):
                    return Coordinates(**cached)
                import json
                cached_data = json.loads(cached) if isinstance(cached, str) else cached
                return Coordinates(**cached_data)
        except Exception:
            pass  # Cache miss, continue

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "q": address,
                    "format": "json",
                    "limit": 1,
                    "countrycodes": "vn" if country == "Vietnam" else None
                }
                response = await client.get(f"{self.base_url}/search", params=params)
                response.raise_for_status()

                data = response.json()
                if data and len(data) > 0:
                    result = data[0]
                    coords = Coordinates(
                        longitude=float(result["lon"]),
                        latitude=float(result["lat"])
                    )
                    # Cache for 24 hours
                    await cache.set(cache_key, coords.dict(), ttl=86400)
                    return coords
        except Exception as e:
            logger.error(f"Geocoding error for '{address}': {e}")
            return None

    async def reverse_geocode(
        self,
        coordinates: Coordinates
    ) -> Optional[Dict[str, Any]]:
        """Convert coordinates to address."""
        # Check cache first
        cache_key = f"reverse_geocode:{coordinates.latitude}:{coordinates.longitude}"
        try:
            cached = await cache.get(cache_key)
            if cached:
                return cached if isinstance(cached, dict) else cached
        except Exception:
            pass  # Cache miss, continue

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "lat": coordinates.latitude,
                    "lon": coordinates.longitude,
                    "format": "json",
                    "addressdetails": 1
                }
                response = await client.get(f"{self.base_url}/reverse", params=params)
                response.raise_for_status()

                data = response.json()
                if data and "address" in data:
                    address_info = {
                        "display_name": data.get("display_name", ""),
                        "address": data.get("address", {})
                    }
                    # Cache for 24 hours
                    await cache.set(cache_key, address_info, ttl=86400)
                    return address_info
        except Exception as e:
            logger.error(f"Reverse geocoding error for {coordinates}: {e}")
            return None

    async def search_address(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for addresses (autocomplete)."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "q": query,
                    "format": "json",
                    "limit": limit,
                    "countrycodes": "vn",
                    "addressdetails": 1
                }
                response = await client.get(f"{self.base_url}/search", params=params)
                response.raise_for_status()

                results = response.json()
                return [
                    {
                        "display_name": r.get("display_name", ""),
                        "coordinates": {
                            "longitude": float(r["lon"]),
                            "latitude": float(r["lat"])
                        },
                        "address": r.get("address", {})
                    }
                    for r in results
                ]
        except Exception as e:
            logger.error(f"Address search error for '{query}': {e}")
            return []
