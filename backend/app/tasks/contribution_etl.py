"""
ETL Task: Sync approved features from contribution DB → main assets DB.

Runs periodically via Celery Beat.
Reads from the datacollector MongoDB (openinfra_gis.features),
transforms to main asset schema, inserts into the main MongoDB (assets collection),
and skips duplicates already synced.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, List

import pymongo
from celery import Task
from app.celery_app import app

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection helpers (synchronous pymongo – Celery compatible)
# ---------------------------------------------------------------------------

CONTRIB_MONGO_URL = os.getenv(
    "CONTRIB_MONGO_URL",
    "mongodb://localhost:27018/openinfra_gis",
)

MAIN_MONGO_URL = os.getenv("MONGODB_URL", "mongodb://mongo:27017")
MAIN_DB_NAME = os.getenv("DATABASE_NAME", "openinfra")

# Vietnamese → ASCII normalised feature_code mapping
_CODE_MAP = {
    "trạm_điện": "tram_dien",
    "cột_điện": "cot_dien",
    "đường_ống_điện": "duong_ong_dien",
    "đèn_đường": "den_duong",
    "đèn_giao_thông": "den_giao_thong",
    "cống_thoát_nước": "cong_thoat_nuoc",
    "ống_dẫn_nước": "ong_dan_nuoc",
    "trụ_chữa_cháy": "tru_chua_chay",
    "trạm_sạc": "tram_sac",
}


def _normalise_code(code: str) -> str:
    """Normalize Vietnamese feature_code to ASCII."""
    return _CODE_MAP.get(code, code)


def _transform_feature(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Map a contribution feature document → main asset document."""
    props = doc.get("properties", {})
    created_str = props.get("created_at")
    try:
        created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00")) if created_str else datetime.utcnow()
    except Exception:
        created_at = datetime.utcnow()

    return {
        "feature_type": props.get("feature_type", doc.get("feature_type", "Unknown")),
        "feature_code": _normalise_code(doc.get("feature_code", "UNKNOWN")),
        "geometry": doc.get("geometry", {}),
        "created_at": created_at,
        "_contrib_id": str(doc["_id"]),  # track origin to skip duplicates
    }


class DatabaseTask(Task):
    """Base task that lazily opens DB connections."""
    _contrib_client = None
    _main_client = None

    @property
    def contrib_db(self):
        if self._contrib_client is None:
            self._contrib_client = pymongo.MongoClient(CONTRIB_MONGO_URL)
        return self._contrib_client.get_default_database()

    @property
    def main_db(self):
        if self._main_client is None:
            self._main_client = pymongo.MongoClient(MAIN_MONGO_URL)
        return self._main_client[MAIN_DB_NAME]


@app.task(base=DatabaseTask, bind=True, name="app.tasks.contribution_etl.sync_contributions")
def sync_contributions(self):
    """
    Pull all features from contribution database and upsert into the main
    assets collection.  Duplicates are detected via `_contrib_id`.
    """
    try:
        contrib_features = self.contrib_db["features"]
        main_assets = self.main_db["assets"]

        # Ensure index for dedup
        main_assets.create_index("_contrib_id", sparse=True)

        # Fetch already-synced ids
        existing_ids = set(
            doc["_contrib_id"]
            for doc in main_assets.find({"_contrib_id": {"$exists": True}}, {"_contrib_id": 1})
        )

        cursor = contrib_features.find({})
        inserted = 0
        skipped = 0
        errors = 0

        for doc in cursor:
            cid = str(doc["_id"])
            if cid in existing_ids:
                skipped += 1
                continue

            try:
                asset = _transform_feature(doc)
                main_assets.insert_one(asset)
                inserted += 1
            except Exception as exc:
                logger.warning("ETL transform/insert error for %s: %s", cid, exc)
                errors += 1

        total = inserted + skipped + errors
        logger.info("ETL sync done: total=%d inserted=%d skipped=%d errors=%d", total, inserted, skipped, errors)
        return {
            "status": "success",
            "total": total,
            "inserted": inserted,
            "skipped": skipped,
            "errors": errors,
        }

    except Exception as exc:
        logger.exception("ETL sync_contributions failed")
        return {"status": "error", "error": str(exc)}
