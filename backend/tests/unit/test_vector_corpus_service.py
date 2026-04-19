"""Unit tests for vector corpus service retrieval and ingest behavior."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.rag.vector_corpus_service import VectorCorpusService


@pytest.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Shadow global DB fixture so unit tests stay DB-independent."""
    yield


class FakeAsyncCursor:
    """Minimal async cursor supporting sort/limit chaining."""

    def __init__(self, docs):
        self._docs = list(docs)
        self._index = 0

    def sort(self, field, direction):
        reverse = direction == -1
        self._docs.sort(key=lambda item: item.get(field), reverse=reverse)
        return self

    def limit(self, size):
        self._docs = self._docs[:size]
        return self

    def __aiter__(self):
        self._index = 0
        return self

    async def __anext__(self):
        if self._index >= len(self._docs):
            raise StopAsyncIteration

        doc = self._docs[self._index]
        self._index += 1
        return doc


class FakeUpdateResult:
    """Small replacement for Motor update result object."""

    def __init__(self, upserted_id=None, modified_count=0):
        self.upserted_id = upserted_id
        self.modified_count = modified_count


class FakeCollection:
    """Configurable fake Motor collection for deterministic tests."""

    def __init__(
        self,
        find_sequences=None,
        find_one_results=None,
        update_results=None,
    ):
        self._find_sequences = list(find_sequences or [])
        self._find_one_results = list(find_one_results or [])
        self._update_results = list(update_results or [])
        self.find_calls = []
        self.update_calls = []

    async def create_index(self, *_args, **_kwargs):
        return "ok"

    def find(self, query, projection):
        self.find_calls.append({"query": query, "projection": projection})
        docs = self._find_sequences.pop(0) if self._find_sequences else []
        return FakeAsyncCursor(docs)

    async def find_one(self, _query, _projection=None):
        return self._find_one_results.pop(0) if self._find_one_results else None

    async def update_one(self, query, update, upsert=False):
        self.update_calls.append(
            {
                "query": query,
                "update": update,
                "upsert": upsert,
            }
        )
        if self._update_results:
            return self._update_results.pop(0)
        return FakeUpdateResult()


class FakeDB:
    """Dict-like DB container that provides named fake collections."""

    def __init__(self, vector_collection: FakeCollection):
        self._collections = {
            "vector_corpus": vector_collection,
            "hazard_layers": FakeCollection(),
            "eop_plans": FakeCollection(),
            "emergency_events": FakeCollection(),
        }

    def __getitem__(self, name):
        return self._collections[name]


def make_service(vector_collection: FakeCollection) -> VectorCorpusService:
    """Build service with fake DB and stub Gemini dependency."""
    gemini_stub = SimpleNamespace(generate_text_embedding=AsyncMock(return_value=[0.0, 1.0]))
    return VectorCorpusService(FakeDB(vector_collection), gemini_service=gemini_stub)


@pytest.mark.asyncio
async def test_retrieve_similar_prefers_cosine_results_when_embedding_available():
    collection = FakeCollection(
        find_sequences=[
            [
                {
                    "source_type": "hazard",
                    "source_id": "haz-1",
                    "summary_text": "Flood warning in district A",
                    "metadata": {"severity": "high"},
                    "embedding": [1.0, 0.0],
                },
                {
                    "source_type": "hazard",
                    "source_id": "haz-2",
                    "summary_text": "Flood warning in district B",
                    "metadata": {"severity": "medium"},
                    "embedding": [0.5, 0.5],
                },
            ]
        ]
    )
    service = make_service(collection)
    service._generate_embedding = AsyncMock(return_value=[1.0, 0.0])
    fallback_mock = AsyncMock(return_value=[])
    service._retrieve_by_text_fallback = fallback_mock

    results = await service.retrieve_similar("flood warning", top_k=2)

    assert [item["source_id"] for item in results] == ["haz-1", "haz-2"]
    assert all(item["retrieval_method"] == "cosine" for item in results)
    fallback_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_retrieve_similar_falls_back_to_text_when_embedding_unavailable():
    service = make_service(FakeCollection())
    service._generate_embedding = AsyncMock(return_value=None)
    cosine_mock = AsyncMock(return_value=[])
    fallback_payload = [
        {
            "source_type": "eop",
            "source_id": "eop-1",
            "summary_text": "Evacuation playbook",
            "metadata": {},
            "similarity_score": 0.4,
            "retrieval_method": "text_fallback",
        }
    ]
    fallback_mock = AsyncMock(return_value=fallback_payload)
    service._retrieve_by_cosine = cosine_mock
    service._retrieve_by_text_fallback = fallback_mock

    results = await service.retrieve_similar("  evacuation plan  ", top_k=3)

    assert results == fallback_payload
    fallback_mock.assert_awaited_once_with("evacuation plan", 3)
    cosine_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_text_fallback_returns_recent_docs_when_no_token_overlap():
    now = datetime.utcnow()
    collection = FakeCollection(
        find_sequences=[
            [],
            [
                {
                    "source_type": "emergency",
                    "source_id": "older-doc",
                    "summary_text": "Historic maintenance report",
                    "metadata": {},
                    "updated_at": now - timedelta(hours=2),
                },
                {
                    "source_type": "emergency",
                    "source_id": "recent-doc",
                    "summary_text": "Latest dispatch timeline",
                    "metadata": {},
                    "updated_at": now,
                },
            ],
        ]
    )
    service = make_service(collection)

    results = await service._retrieve_by_text_fallback("coastal tsunami response", top_k=2)

    assert [item["source_id"] for item in results] == ["recent-doc", "older-doc"]
    assert all(item["similarity_score"] == 0.0 for item in results)
    assert all(item["retrieval_method"] == "text_fallback" for item in results)
    assert len(collection.find_calls) == 2


@pytest.mark.asyncio
async def test_upsert_corpus_documents_stats_accounting_for_insert_update_unchanged():
    collection = FakeCollection(
        find_one_results=[
            None,
            {"content_hash": "hash-2", "embedding": [0.2, 0.3]},
            {"content_hash": "hash-3", "embedding": [0.4, 0.5]},
        ],
        update_results=[
            FakeUpdateResult(upserted_id="new-doc"),
            FakeUpdateResult(modified_count=1),
            FakeUpdateResult(modified_count=0),
        ],
    )
    service = make_service(collection)
    service.embedding_enabled = False
    service.ensure_indexes = AsyncMock()

    entries = [
        {
            "source_type": "hazard",
            "source_id": "hz-1",
            "summary_text": "Hazard summary 1",
            "content_hash": "hash-1",
            "metadata": {"severity": "high"},
        },
        {
            "source_type": "eop",
            "source_id": "eop-2",
            "summary_text": "EOP summary 2",
            "content_hash": "hash-2",
            "metadata": {"status": "published"},
        },
        {
            "source_type": "emergency",
            "source_id": "em-3",
            "summary_text": "Emergency summary 3",
            "content_hash": "hash-3",
            "metadata": {"status": "active"},
        },
    ]
    source_counts = {"hazard": 1, "eop": 1, "emergency": 1}
    service._collect_corpus_entries = AsyncMock(return_value=(entries, source_counts))

    stats = await service.upsert_corpus_documents(limit_per_source=99)

    assert stats["scanned"] == 3
    assert stats["inserted"] == 1
    assert stats["updated"] == 1
    assert stats["unchanged"] == 1
    assert stats["embedded"] == 0
    assert stats["embedding_skipped"] == 0
    assert stats["embedding_enabled"] is False
    assert stats["source_counts"] == source_counts

    service.ensure_indexes.assert_awaited_once()
    service._collect_corpus_entries.assert_awaited_once_with(limit_per_source=99)
    assert len(collection.update_calls) == 3
    assert all(call["upsert"] is True for call in collection.update_calls)