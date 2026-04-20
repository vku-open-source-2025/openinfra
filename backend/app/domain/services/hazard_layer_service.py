"""Hazard layer service."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.core.exceptions import NotFoundError
from app.domain.models.hazard_layer import (
    HazardEventType,
    HazardLayer,
    HazardLayerCreate,
    HazardLayerUpdate,
    HazardSeverity,
    HazardSource,
)
from app.domain.repositories.hazard_layer_repository import HazardLayerRepository


class HazardLayerService:
    """Business logic for hazard layers."""

    def __init__(self, repository: HazardLayerRepository):
        self.repository = repository

    def _normalize_event_type(self, raw_value: object) -> HazardEventType:
        """Normalize event type values from external sources."""
        if isinstance(raw_value, HazardEventType):
            return raw_value

        value = str(raw_value or "other").strip().lower()
        mapping = {
            "flood": HazardEventType.FLOOD,
            "storm": HazardEventType.STORM,
            "landslide": HazardEventType.LANDSLIDE,
            "fire": HazardEventType.FIRE,
            "earthquake": HazardEventType.EARTHQUAKE,
            "outage": HazardEventType.OUTAGE,
            "pollution": HazardEventType.POLLUTION,
            "drought": HazardEventType.DROUGHT,
            "other": HazardEventType.OTHER,
        }
        return mapping.get(value, HazardEventType.OTHER)

    def _normalize_severity(self, raw_value: object) -> HazardSeverity:
        """Normalize severity values from external sources."""
        if isinstance(raw_value, HazardSeverity):
            return raw_value

        value = str(raw_value or "medium").strip().lower()
        mapping = {
            "low": HazardSeverity.LOW,
            "medium": HazardSeverity.MEDIUM,
            "high": HazardSeverity.HIGH,
            "critical": HazardSeverity.CRITICAL,
        }
        return mapping.get(value, HazardSeverity.MEDIUM)

    def _normalize_source(self, raw_value: object) -> HazardSource:
        """Normalize source values from ingest records."""
        if isinstance(raw_value, HazardSource):
            return raw_value

        value = str(raw_value or "other").strip().lower()
        mapping = {
            "nchmf": HazardSource.NCHMF,
            "vndms": HazardSource.VNDMS,
            "iot": HazardSource.IOT,
            "manual": HazardSource.MANUAL,
            "other": HazardSource.OTHER,
        }
        return mapping.get(value, HazardSource.OTHER)

    def _extract_geometry(self, raw_record: dict) -> Optional[dict]:
        """Extract GeoJSON geometry from normalized ingest record."""
        location = raw_record.get("location")
        if isinstance(location, dict) and location.get("type") and location.get("coordinates"):
            return location

        geometry = raw_record.get("geometry")
        if isinstance(geometry, dict) and geometry.get("type") and geometry.get("coordinates"):
            return geometry

        metadata = raw_record.get("metadata", {})
        if isinstance(metadata, dict):
            md_geometry = metadata.get("geometry")
            if (
                isinstance(md_geometry, dict)
                and md_geometry.get("type")
                and md_geometry.get("coordinates")
            ):
                return md_geometry

        return None

    async def create_hazard(self, payload: HazardLayerCreate) -> HazardLayer:
        """Create hazard layer manually."""
        data = payload.model_dump(exclude_unset=True)
        if data.get("detected_at") is None:
            data["detected_at"] = datetime.utcnow()
        return await self.repository.create(data)

    async def get_hazard_by_id(self, hazard_db_id: str) -> HazardLayer:
        """Get hazard by db id."""
        hazard = await self.repository.find_by_id(hazard_db_id)
        if not hazard:
            raise NotFoundError("HazardLayer", hazard_db_id)
        return hazard

    async def update_hazard(self, hazard_db_id: str, updates: HazardLayerUpdate) -> HazardLayer:
        """Update hazard fields."""
        _ = await self.get_hazard_by_id(hazard_db_id)
        updated = await self.repository.update(
            hazard_db_id,
            updates.model_dump(exclude_unset=True),
        )
        if not updated:
            raise NotFoundError("HazardLayer", hazard_db_id)
        return updated

    async def list_hazards(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        source: Optional[str] = None,
        district: Optional[str] = None,
        ward: Optional[str] = None,
    ) -> List[HazardLayer]:
        """List hazard layers with filters."""
        return await self.repository.list(
            skip=skip,
            limit=limit,
            active_only=active_only,
            event_type=event_type,
            severity=severity,
            source=source,
            district=district,
            ward=ward,
        )

    async def list_hazards_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int,
        limit: int = 100,
    ) -> List[HazardLayer]:
        """List active hazards near coordinate."""
        return await self.repository.list_nearby(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            limit=limit,
        )

    async def list_hazards_in_polygon(self, polygon: dict, limit: int = 500) -> List[HazardLayer]:
        """List active hazards inside polygon."""
        return await self.repository.list_in_polygon(polygon=polygon, limit=limit)

    async def list_recent_hazards(
        self,
        window_hours: int = 24,
        limit: int = 50,
        active_only: bool = True,
    ) -> List[HazardLayer]:
        """List hazards detected within a recent time window."""
        cutoff = datetime.utcnow() - timedelta(hours=max(window_hours, 1))
        return await self.repository.list_recent(
            window_start=cutoff,
            limit=limit,
            active_only=active_only,
        )

    async def deactivate_expired(self) -> int:
        """Deactivate expired hazards."""
        return await self.repository.deactivate_expired(datetime.utcnow())

    async def upsert_ingest_records(
        self,
        records: List[dict],
        source_override: Optional[str] = None,
        default_ttl_hours: int = 24,
    ) -> Dict[str, object]:
        """Transform and upsert normalized ingest records."""
        payloads: List[dict] = []
        now = datetime.utcnow()

        for record in records:
            source = self._normalize_source(source_override or record.get("source")).value
            hazard_id = str(record.get("source_id") or record.get("hazard_id") or "")
            if not hazard_id:
                continue

            detected_at_raw = record.get("detected_at")
            if isinstance(detected_at_raw, datetime):
                detected_at = detected_at_raw
            elif isinstance(detected_at_raw, str):
                try:
                    detected_at = datetime.fromisoformat(
                        detected_at_raw.replace("Z", "+00:00")
                    )
                except ValueError:
                    detected_at = now
            else:
                detected_at = now

            ttl_hours = int(record.get("ttl_hours") or default_ttl_hours)
            expires_at = detected_at + timedelta(hours=max(ttl_hours, 1))
            metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}

            payloads.append(
                {
                    "hazard_id": hazard_id,
                    "title": str(record.get("title") or "Hazard signal"),
                    "description": record.get("description"),
                    "event_type": self._normalize_event_type(record.get("event_type")).value,
                    "severity": self._normalize_severity(record.get("severity")).value,
                    "source": source,
                    "geometry": self._extract_geometry(record),
                    "affected_polygon": record.get("affected_polygon"),
                    "intensity_level": record.get("intensity_level"),
                    "forecast_confidence": record.get("forecast_confidence"),
                    "affected_population": record.get("affected_population"),
                    "district": record.get("district") or metadata.get("district"),
                    "ward": record.get("ward") or metadata.get("ward"),
                    "detected_at": detected_at,
                    "ingest_timestamp": now,
                    "expires_at": expires_at,
                    "is_active": True,
                    "metadata": {
                        **metadata,
                        "source_record": {
                            "source": source,
                            "source_id": hazard_id,
                        },
                    },
                }
            )

        if not payloads:
            return {"total": 0, "inserted": 0, "updated": 0}

        return await self.repository.bulk_upsert(payloads)
