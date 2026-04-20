"""Hazard feed ingestion service for SOSCONN integration."""

import logging
import math
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


class HazardIngestService:
    """Collect and normalize hazard feeds from external providers."""

    _last_feed_checks: Dict[str, Dict[str, Any]] = {}

    def __init__(self):
        self.nchmf_feed_url = os.getenv("NCHMF_FEED_URL", "").strip()
        self.vndms_feed_url = os.getenv("VNDMS_FEED_URL", "").strip()

        timeout_raw = os.getenv("HAZARD_FEED_TIMEOUT", "20")
        try:
            self.feed_timeout_seconds = float(timeout_raw)
            if not math.isfinite(self.feed_timeout_seconds) or self.feed_timeout_seconds <= 0:
                raise ValueError("timeout must be a positive finite number")
        except (TypeError, ValueError):
            logger.warning(
                "Invalid HAZARD_FEED_TIMEOUT=%r; falling back to 20 seconds",
                timeout_raw,
            )
            self.feed_timeout_seconds = 20.0

    def _resolve_timeout_seconds(self, timeout_seconds: Optional[float]) -> float:
        """Resolve an optional timeout override to a valid positive timeout."""
        if timeout_seconds is None:
            return self.feed_timeout_seconds

        try:
            parsed_timeout = float(timeout_seconds)
        except (TypeError, ValueError):
            logger.warning(
                "Invalid timeout override %r; using configured timeout %.2f seconds",
                timeout_seconds,
                self.feed_timeout_seconds,
            )
            return self.feed_timeout_seconds

        if not math.isfinite(parsed_timeout) or parsed_timeout <= 0:
            logger.warning(
                "Non-positive timeout override %r; using configured timeout %.2f seconds",
                timeout_seconds,
                self.feed_timeout_seconds,
            )
            return self.feed_timeout_seconds

        return parsed_timeout

    async def _fetch_json(self, url: str) -> Optional[Any]:
        """Fetch JSON payload from a remote URL."""
        if not url:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.feed_timeout_seconds) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.error("Failed to fetch hazard feed %s: %s", url, exc)
            return None

    def _normalize_record(self, source: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize provider-specific payloads to a common structure."""
        title = item.get("title") or item.get("name") or "Hazard signal"
        description = item.get("description") or item.get("summary") or ""
        severity = str(item.get("severity") or item.get("level") or "medium").lower()
        event_type = str(item.get("event_type") or item.get("type") or "other").lower()

        normalized = {
            "source": source,
            "source_id": str(item.get("id") or item.get("code") or ""),
            "title": title,
            "description": description,
            "severity": severity,
            "event_type": event_type,
            "location": item.get("location") or item.get("geometry"),
            "detected_at": item.get("detected_at") or item.get("timestamp") or datetime.utcnow().isoformat(),
            "metadata": item,
        }
        return normalized

    async def ingest_source(self, source: str, url: str) -> List[Dict[str, Any]]:
        """Fetch and normalize hazard data from one source."""
        if not url:
            logger.warning(
                "%s feed URL is not configured; skipping ingest",
                source.upper(),
            )
            return []

        payload = await self._fetch_json(url)
        if payload is None:
            logger.warning(
                "%s feed returned no payload; upstream may be unavailable",
                source.upper(),
            )
            return []

        if isinstance(payload, dict):
            if isinstance(payload.get("data"), list):
                items = payload.get("data", [])
            elif isinstance(payload.get("items"), list):
                items = payload.get("items", [])
            else:
                items = [payload]
        elif isinstance(payload, list):
            items = payload
        else:
            items = []

        normalized = [
            self._normalize_record(source, item)
            for item in items
            if isinstance(item, dict)
        ]

        logger.info("Ingested %s records from %s", len(normalized), source)
        return normalized

    async def ingest_nchmf(self) -> List[Dict[str, Any]]:
        """Ingest NCHMF weather hazard feed."""
        return await self.ingest_source("nchmf", self.nchmf_feed_url)

    async def ingest_vndms(self) -> List[Dict[str, Any]]:
        """Ingest VNDMS disaster management feed."""
        return await self.ingest_source("vndms", self.vndms_feed_url)

    async def ingest_all(self) -> List[Dict[str, Any]]:
        """Ingest all configured hazard feeds."""
        nchmf_records = await self.ingest_nchmf()
        vndms_records = await self.ingest_vndms()
        return nchmf_records + vndms_records

    @staticmethod
    def _is_valid_feed_url(url: str) -> bool:
        """Validate feed URL format for readiness checks."""
        if not isinstance(url, str):
            return False

        candidate = url.strip()
        if not candidate:
            return False

        parsed = urlparse(candidate)
        if parsed.scheme.lower() not in {"http", "https"}:
            return False

        # Require a resolvable host. Values like "http://:80/path" expose a netloc
        # but do not contain a usable hostname for outbound checks.
        if not parsed.netloc or not parsed.hostname:
            return False

        try:
            _ = parsed.port
        except ValueError:
            return False

        return True

    async def _check_feed_reachability(
        self,
        source: str,
        url: str,
        *,
        check_reachability: bool,
        timeout_seconds: Optional[float],
        allow_get_fallback: bool,
    ) -> Dict[str, Any]:
        """Run timeout-safe reachability check with HEAD and optional GET fallback."""
        timeout = self._resolve_timeout_seconds(timeout_seconds)
        url = (url or "").strip()

        if not url:
            result = {
                "checked": False,
                "checked_at": None,
                "status": "missing_url",
                "reachable": False,
                "method": None,
                "status_code": None,
                "timeout_seconds": timeout,
                "error": None,
            }
            self._last_feed_checks[source] = result
            return result

        if not self._is_valid_feed_url(url):
            result = {
                "checked": False,
                "checked_at": None,
                "status": "invalid_url",
                "reachable": False,
                "method": None,
                "status_code": None,
                "timeout_seconds": timeout,
                "error": "URL must include http/https scheme and host",
            }
            self._last_feed_checks[source] = result
            return result

        if not check_reachability:
            cached = self._last_feed_checks.get(source)
            if cached:
                return cached

            result = {
                "checked": False,
                "checked_at": None,
                "status": "not_checked",
                "reachable": None,
                "method": None,
                "status_code": None,
                "timeout_seconds": timeout,
                "error": None,
            }
            self._last_feed_checks[source] = result
            return result

        checked_at = datetime.utcnow().isoformat() + "Z"
        method: Optional[str] = None

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                method = "HEAD"
                response = await client.head(url)

                if allow_get_fallback and response.status_code in {405, 501}:
                    method = "GET"
                    response = await client.get(url)

            reachable = 200 <= response.status_code < 400
            result = {
                "checked": True,
                "checked_at": checked_at,
                "status": "reachable" if reachable else "http_error",
                "reachable": reachable,
                "method": method,
                "status_code": response.status_code,
                "timeout_seconds": timeout,
                "error": (
                    None
                    if reachable
                    else f"Unexpected HTTP status {response.status_code}"
                ),
            }
        except httpx.TimeoutException:
            result = {
                "checked": True,
                "checked_at": checked_at,
                "status": "timeout",
                "reachable": False,
                "method": method,
                "status_code": None,
                "timeout_seconds": timeout,
                "error": f"Request timed out after {timeout} seconds",
            }
        except httpx.HTTPError as exc:
            result = {
                "checked": True,
                "checked_at": checked_at,
                "status": "request_error",
                "reachable": False,
                "method": method,
                "status_code": None,
                "timeout_seconds": timeout,
                "error": str(exc),
            }
        except Exception as exc:  # pragma: no cover - defensive stability guard
            result = {
                "checked": True,
                "checked_at": checked_at,
                "status": "unexpected_error",
                "reachable": False,
                "method": method,
                "status_code": None,
                "timeout_seconds": timeout,
                "error": str(exc) or exc.__class__.__name__,
            }

        self._last_feed_checks[source] = result
        return result

    async def get_ingest_status(
        self,
        *,
        check_reachability: bool = True,
        timeout_seconds: Optional[float] = None,
        allow_get_fallback: bool = True,
    ) -> Dict[str, Any]:
        """Return feed configuration and readiness status for hazard ingestion."""
        feed_urls = {
            "nchmf": self.nchmf_feed_url,
            "vndms": self.vndms_feed_url,
        }

        feeds: Dict[str, Dict[str, Any]] = {}
        for source, url in feed_urls.items():
            last_check = await self._check_feed_reachability(
                source,
                url,
                check_reachability=check_reachability,
                timeout_seconds=timeout_seconds,
                allow_get_fallback=allow_get_fallback,
            )

            url_present = bool(url)
            configured = url_present and self._is_valid_feed_url(url)

            feeds[source] = {
                "configured": configured,
                "url_present": url_present,
                "last_check": last_check,
            }

        total_feeds = len(feeds)
        configured_feeds = sum(1 for feed in feeds.values() if feed["configured"])
        all_configured = configured_feeds == total_feeds

        if check_reachability:
            all_reachable = all(
                feed["last_check"].get("reachable") is True
                for feed in feeds.values()
                if feed["configured"]
            )
            ready = all_configured and all_reachable
        else:
            # Readiness requires an explicit live reachability check in this call.
            ready = False

        if ready:
            overall_status = "ready"
        elif configured_feeds == 0:
            overall_status = "not_configured"
        elif all_configured and not check_reachability:
            overall_status = "configured"
        else:
            overall_status = "degraded"

        return {
            "feeds": feeds,
            "overall": {
                "status": overall_status,
                "ready": ready,
                "configured_feeds": configured_feeds,
                "total_feeds": total_feeds,
                "reachability_checked": check_reachability,
                "checked_at": datetime.utcnow().isoformat() + "Z",
            },
        }
