"""Vector corpus service for disaster-response RAG retrieval."""

from __future__ import annotations

import hashlib
import logging
import math
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.infrastructure.external.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class VectorCorpusService:
    """Build and query vector corpus from hazard, EOP, and emergency summaries."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        gemini_service: Optional[GeminiService] = None,
    ):
        self.db = db
        self.collection = db["vector_corpus"]
        self.hazard_collection = db["hazard_layers"]
        self.eop_collection = db["eop_plans"]
        self.emergency_collection = db["emergency_events"]
        self.gemini_service = gemini_service or GeminiService()
        self.embedding_enabled = bool((settings.GEMINI_API_KEY or "").strip())

    async def ensure_indexes(self) -> None:
        """Ensure indexes for idempotent upsert and retrieval ordering."""
        await self.collection.create_index(
            [("source_type", 1), ("source_id", 1)],
            unique=True,
            name="uq_vector_corpus_source",
        )
        await self.collection.create_index(
            [("updated_at", -1)],
            name="idx_vector_corpus_updated",
        )
        await self.collection.create_index(
            [("content_hash", 1)],
            name="idx_vector_corpus_content_hash",
        )

    async def upsert_corpus_documents(self, limit_per_source: int = 500) -> Dict[str, Any]:
        """Build and upsert corpus entries from hazard/EOP/emergency collections."""
        await self.ensure_indexes()
        entries, source_counts = await self._collect_corpus_entries(
            limit_per_source=limit_per_source
        )

        now = datetime.utcnow()
        stats: Dict[str, Any] = {
            "scanned": len(entries),
            "inserted": 0,
            "updated": 0,
            "unchanged": 0,
            "embedded": 0,
            "embedding_skipped": 0,
            "embedding_enabled": self.embedding_enabled,
            "source_counts": source_counts,
        }

        if not self.embedding_enabled:
            logger.warning(
                "Vector corpus ingest running without GEMINI_API_KEY; "
                "documents will be upserted without new embeddings"
            )

        for entry in entries:
            query = {
                "source_type": entry["source_type"],
                "source_id": entry["source_id"],
            }
            existing = await self.collection.find_one(
                query,
                {"content_hash": 1, "embedding": 1},
            )

            needs_embedding = self.embedding_enabled and (
                existing is None
                or existing.get("content_hash") != entry["content_hash"]
                or not existing.get("embedding")
            )

            embedding: Optional[List[float]] = None
            if needs_embedding:
                embedding = await self._generate_embedding(entry["summary_text"])
                if embedding is not None:
                    stats["embedded"] += 1
                else:
                    stats["embedding_skipped"] += 1

            update_doc: Dict[str, Any] = {
                "summary_text": entry["summary_text"],
                "metadata": entry["metadata"],
                "content_hash": entry["content_hash"],
                "updated_at": now,
            }

            if embedding is not None:
                update_doc["embedding"] = embedding
                update_doc["embedding_dims"] = len(embedding)
                update_doc["embedding_model"] = settings.GEMINI_TEXT_MODEL
                update_doc["embedding_updated_at"] = now
            elif existing is None:
                update_doc["embedding"] = None
                update_doc["embedding_dims"] = 0
                update_doc["embedding_model"] = (
                    settings.GEMINI_TEXT_MODEL if self.embedding_enabled else None
                )

            result = await self.collection.update_one(
                query,
                {
                    "$set": update_doc,
                    "$setOnInsert": {
                        "source_type": entry["source_type"],
                        "source_id": entry["source_id"],
                        "created_at": now,
                    },
                },
                upsert=True,
            )

            if result.upserted_id is not None:
                stats["inserted"] += 1
            elif result.modified_count > 0:
                stats["updated"] += 1
            else:
                stats["unchanged"] += 1

        return stats

    async def retrieve_similar(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve similar corpus docs using cosine similarity on text embeddings."""
        if not query_text or not query_text.strip():
            return []

        k = max(1, min(int(top_k), 50))
        cleaned_query = query_text.strip()

        query_embedding = await self._generate_embedding(cleaned_query)
        if query_embedding is not None:
            cosine_results = await self._retrieve_by_cosine(query_embedding, k)
            if cosine_results:
                return cosine_results

        return await self._retrieve_by_text_fallback(cleaned_query, k)

    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding only when Gemini embedding is configured."""
        if not self.embedding_enabled:
            return None

        try:
            return await self.gemini_service.generate_text_embedding(text)
        except Exception as exc:
            logger.warning("Vector embedding generation failed: %s", exc)
            return None

    async def _collect_corpus_entries(
        self,
        limit_per_source: int,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        hazards = await self._collect_hazard_entries(limit_per_source)
        eops = await self._collect_eop_entries(limit_per_source)
        emergencies = await self._collect_emergency_entries(limit_per_source)

        entries = hazards + eops + emergencies
        source_counts = {
            "hazard": len(hazards),
            "eop": len(eops),
            "emergency": len(emergencies),
        }
        return entries, source_counts

    async def _collect_hazard_entries(self, limit: int) -> List[Dict[str, Any]]:
        cursor = (
            self.hazard_collection.find(
                {},
                {
                    "_id": 1,
                    "hazard_id": 1,
                    "title": 1,
                    "description": 1,
                    "event_type": 1,
                    "severity": 1,
                    "source": 1,
                    "district": 1,
                    "ward": 1,
                    "is_active": 1,
                    "detected_at": 1,
                    "updated_at": 1,
                },
            )
            .sort("updated_at", -1)
            .limit(limit)
        )

        entries: List[Dict[str, Any]] = []
        async for doc in cursor:
            source_id = self._doc_id(doc)
            if not source_id:
                continue

            summary_parts = [
                f"Hazard title: {self._stringify(doc.get('title') or doc.get('hazard_id'))}",
                f"Description: {self._stringify(doc.get('description'))}",
                f"Type: {self._stringify(doc.get('event_type'))}",
                f"Severity: {self._stringify(doc.get('severity'))}",
                f"Source: {self._stringify(doc.get('source'))}",
                f"Location: {self._stringify(doc.get('ward'))}, {self._stringify(doc.get('district'))}",
                f"Active: {self._stringify(doc.get('is_active'))}",
            ]

            metadata = {
                "source_collection": "hazard_layers",
                "hazard_id": doc.get("hazard_id"),
                "event_type": doc.get("event_type"),
                "severity": doc.get("severity"),
                "source": doc.get("source"),
                "district": doc.get("district"),
                "ward": doc.get("ward"),
                "is_active": doc.get("is_active", True),
                "detected_at": doc.get("detected_at"),
                "updated_at": doc.get("updated_at"),
            }

            entries.append(
                self._build_entry(
                    source_type="hazard",
                    source_id=source_id,
                    summary_text=self._join_parts(summary_parts),
                    metadata=metadata,
                )
            )

        return entries

    async def _collect_eop_entries(self, limit: int) -> List[Dict[str, Any]]:
        cursor = (
            self.eop_collection.find(
                {},
                {
                    "_id": 1,
                    "emergency_event_id": 1,
                    "title": 1,
                    "summary": 1,
                    "objectives": 1,
                    "operational_phases": 1,
                    "actions": 1,
                    "status": 1,
                    "updated_at": 1,
                },
            )
            .sort("updated_at", -1)
            .limit(limit)
        )

        entries: List[Dict[str, Any]] = []
        async for doc in cursor:
            source_id = self._doc_id(doc)
            if not source_id:
                continue

            objectives = self._stringify(doc.get("objectives"))
            phases = self._stringify(doc.get("operational_phases"))
            action_summaries = self._summarize_eop_actions(doc.get("actions") or [])

            summary_parts = [
                f"EOP title: {self._stringify(doc.get('title'))}",
                f"Summary: {self._stringify(doc.get('summary'))}",
                f"Objectives: {objectives}",
                f"Operational phases: {phases}",
                f"Actions: {action_summaries}",
                f"Status: {self._stringify(doc.get('status'))}",
            ]

            metadata = {
                "source_collection": "eop_plans",
                "emergency_event_id": doc.get("emergency_event_id"),
                "status": doc.get("status"),
                "updated_at": doc.get("updated_at"),
            }

            entries.append(
                self._build_entry(
                    source_type="eop",
                    source_id=source_id,
                    summary_text=self._join_parts(summary_parts),
                    metadata=metadata,
                )
            )

        return entries

    async def _collect_emergency_entries(self, limit: int) -> List[Dict[str, Any]]:
        cursor = (
            self.emergency_collection.find(
                {},
                {
                    "_id": 1,
                    "event_code": 1,
                    "title": 1,
                    "description": 1,
                    "event_type": 1,
                    "severity": 1,
                    "status": 1,
                    "location": 1,
                    "instructions": 1,
                    "tags": 1,
                    "started_at": 1,
                    "updated_at": 1,
                },
            )
            .sort("updated_at", -1)
            .limit(limit)
        )

        entries: List[Dict[str, Any]] = []
        async for doc in cursor:
            source_id = self._doc_id(doc)
            if not source_id:
                continue

            location = doc.get("location") or {}
            location_summary = self._stringify(
                [
                    location.get("address"),
                    location.get("ward"),
                    location.get("district"),
                    location.get("city"),
                ]
            )

            summary_parts = [
                f"Emergency title: {self._stringify(doc.get('title'))}",
                f"Description: {self._stringify(doc.get('description'))}",
                f"Event code: {self._stringify(doc.get('event_code'))}",
                f"Type: {self._stringify(doc.get('event_type'))}",
                f"Severity: {self._stringify(doc.get('severity'))}",
                f"Status: {self._stringify(doc.get('status'))}",
                f"Location: {location_summary}",
                f"Instructions: {self._stringify(doc.get('instructions'))}",
                f"Tags: {self._stringify(doc.get('tags'))}",
            ]

            metadata = {
                "source_collection": "emergency_events",
                "event_code": doc.get("event_code"),
                "event_type": doc.get("event_type"),
                "severity": doc.get("severity"),
                "status": doc.get("status"),
                "started_at": doc.get("started_at"),
                "updated_at": doc.get("updated_at"),
            }

            entries.append(
                self._build_entry(
                    source_type="emergency",
                    source_id=source_id,
                    summary_text=self._join_parts(summary_parts),
                    metadata=metadata,
                )
            )

        return entries

    async def _retrieve_by_cosine(
        self,
        query_embedding: List[float],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        cursor = self.collection.find(
            {"embedding": {"$type": "array"}},
            {
                "_id": 0,
                "source_type": 1,
                "source_id": 1,
                "summary_text": 1,
                "metadata": 1,
                "embedding": 1,
            },
        )

        scored: List[Dict[str, Any]] = []
        async for doc in cursor:
            embedding = doc.get("embedding")
            if not isinstance(embedding, list) or not embedding:
                continue

            score = self._cosine_similarity(query_embedding, embedding)
            scored.append(
                {
                    "source_type": doc.get("source_type"),
                    "source_id": doc.get("source_id"),
                    "summary_text": doc.get("summary_text"),
                    "metadata": doc.get("metadata", {}),
                    "similarity_score": score,
                    "retrieval_method": "cosine",
                }
            )

        scored.sort(key=lambda item: item["similarity_score"], reverse=True)
        return scored[:top_k]

    async def _retrieve_by_text_fallback(
        self,
        query_text: str,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        tokens = self._tokenize(query_text)
        if not tokens:
            return []

        pattern = "|".join(re.escape(token) for token in tokens[:8])
        cursor = self.collection.find(
            {"summary_text": {"$regex": pattern, "$options": "i"}},
            {
                "_id": 0,
                "source_type": 1,
                "source_id": 1,
                "summary_text": 1,
                "metadata": 1,
            },
        ).limit(max(top_k * 4, top_k))

        candidates: List[Dict[str, Any]] = []
        async for doc in cursor:
            summary_text = doc.get("summary_text") or ""
            overlap = self._token_overlap(tokens, self._tokenize(summary_text))
            candidates.append(
                {
                    "source_type": doc.get("source_type"),
                    "source_id": doc.get("source_id"),
                    "summary_text": summary_text,
                    "metadata": doc.get("metadata", {}),
                    "similarity_score": overlap,
                    "retrieval_method": "text_fallback",
                }
            )

        if not candidates:
            recent_cursor = self.collection.find(
                {},
                {
                    "_id": 0,
                    "source_type": 1,
                    "source_id": 1,
                    "summary_text": 1,
                    "metadata": 1,
                },
            ).sort("updated_at", -1).limit(top_k)

            async for doc in recent_cursor:
                candidates.append(
                    {
                        "source_type": doc.get("source_type"),
                        "source_id": doc.get("source_id"),
                        "summary_text": doc.get("summary_text"),
                        "metadata": doc.get("metadata", {}),
                        "similarity_score": 0.0,
                        "retrieval_method": "text_fallback",
                    }
                )

        candidates.sort(key=lambda item: item["similarity_score"], reverse=True)
        return candidates[:top_k]

    def _build_entry(
        self,
        source_type: str,
        source_id: str,
        summary_text: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        cleaned_summary = summary_text.strip()
        return {
            "source_type": source_type,
            "source_id": source_id,
            "summary_text": cleaned_summary,
            "content_hash": self._content_hash(cleaned_summary),
            "metadata": self._serialize_value(metadata),
        }

    @staticmethod
    def _doc_id(doc: Dict[str, Any]) -> str:
        raw_id = doc.get("_id")
        return str(raw_id) if raw_id is not None else ""

    @staticmethod
    def _join_parts(parts: List[str]) -> str:
        return "\n".join(part for part in parts if part and part.strip())

    @staticmethod
    def _stringify(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            items = [str(item).strip() for item in value if str(item).strip()]
            return ", ".join(items)
        if isinstance(value, dict):
            items = [
                f"{key}: {val}"
                for key, val in value.items()
                if val not in (None, "", [], {})
            ]
            return ", ".join(items)
        return str(value).strip()

    @staticmethod
    def _summarize_eop_actions(actions: List[Any], max_actions: int = 5) -> str:
        summaries: List[str] = []
        for action in actions[:max_actions]:
            if not isinstance(action, dict):
                continue

            title = str(action.get("title") or action.get("action_id") or "").strip()
            description = str(action.get("description") or "").strip()

            if title and description:
                summaries.append(f"{title}: {description}")
            elif title:
                summaries.append(title)
            elif description:
                summaries.append(description)

        return "; ".join(summaries)

    @staticmethod
    def _content_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    def _serialize_value(cls, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, list):
            return [cls._serialize_value(item) for item in value]
        if isinstance(value, dict):
            return {key: cls._serialize_value(val) for key, val in value.items()}
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [token for token in re.split(r"\W+", text.lower()) if len(token) > 2]

    @staticmethod
    def _token_overlap(query_tokens: List[str], document_tokens: List[str]) -> float:
        if not query_tokens:
            return 0.0
        query_set = set(query_tokens)
        document_set = set(document_tokens)
        overlap_count = len(query_set.intersection(document_set))
        return overlap_count / max(len(query_set), 1)

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_vec1 = math.sqrt(sum(a * a for a in vec1))
        norm_vec2 = math.sqrt(sum(b * b for b in vec2))

        if norm_vec1 == 0.0 or norm_vec2 == 0.0:
            return 0.0

        score = dot_product / (norm_vec1 * norm_vec2)
        return float(max(-1.0, min(1.0, score)))