"""Unit tests for AG05 context retrieval parsing and normalization behavior."""

import httpx
import pytest

from app.infrastructure.external.ag05_context_service import AG05ContextService


@pytest.mark.parametrize(
    "raw_text, expected",
    [
        (
            '{"snippets":[{"source_id":"AG05-1","text":"Alpha"}]}',
            {"snippets": [{"source_id": "AG05-1", "text": "Alpha"}]},
        ),
        (
            "Result:\n```json\n{\"snippets\":[{\"source_id\":\"AG05-2\",\"text\":\"Beta\"}]}\n```",
            {"snippets": [{"source_id": "AG05-2", "text": "Beta"}]},
        ),
        ("Here are numbers: [1, 2, 3] done.", [1, 2, 3]),
        ("This is not json", None),
    ],
)
def test_extract_first_json_payload_handles_plain_embedded_and_invalid(raw_text, expected):
    """Extractor should parse plain or embedded JSON and ignore invalid text."""
    assert AG05ContextService._extract_first_json_payload(raw_text) == expected


def test_normalize_snippets_from_dict_trims_text_and_caps_by_max_snippets():
    """Dict payload should be normalized, trimmed, and capped."""
    payload = {
        "snippets": [
            {"source_id": "  SRC-1  ", "text": "  First snippet  "},
            {"id": "SRC-2", "snippet": "  Second snippet  "},
            {"source_id": "SRC-3", "text": "   "},
            {"source_id": "SRC-4", "content": "Fourth snippet"},
        ]
    }

    snippets = AG05ContextService._normalize_snippets(payload, max_snippets=2)

    assert snippets == [
        {"source_id": "SRC-1", "text": "First snippet"},
        {"source_id": "SRC-2", "text": "Second snippet"},
    ]


def test_normalize_snippets_from_list_supports_dict_and_plain_text_items():
    """List payload should support mixed dict/string snippet entries."""
    payload = [
        {"quote": "  Alpha quote  "},
        "  Beta plain text  ",
        {"text": "  Gamma text  "},
    ]

    snippets = AG05ContextService._normalize_snippets(payload, max_snippets=5)

    assert snippets == [
        {"source_id": "AG05-1", "text": "Alpha quote"},
        {"source_id": "AG05-2", "text": "Beta plain text"},
        {"source_id": "AG05-3", "text": "Gamma text"},
    ]


@pytest.mark.asyncio
async def test_retrieve_snippets_returns_empty_list_on_upstream_errors(monkeypatch):
    """Network/upstream failures should never bubble up to callers."""
    service = AG05ContextService(base_url="https://llm.example")

    class FailingAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            raise httpx.ConnectError("network down")

    monkeypatch.setattr(
        "app.infrastructure.external.ag05_context_service.httpx.AsyncClient",
        FailingAsyncClient,
    )

    snippets = await service.retrieve_snippets("Need AG05 context")

    assert snippets == []


@pytest.mark.asyncio
async def test_retrieve_snippets_falls_back_to_plain_text_for_non_json_response(monkeypatch):
    """When answer is non-empty plain text, service should emit one fallback snippet."""
    service = AG05ContextService(base_url="https://llm.example")

    class StubResponse:
        content = b'{"answer":"plain"}'

        def raise_for_status(self):
            return None

        def json(self):
            return {"answer": "  Useful AG05 plain text context  "}

    class StubAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            return StubResponse()

    monkeypatch.setattr(
        "app.infrastructure.external.ag05_context_service.httpx.AsyncClient",
        StubAsyncClient,
    )

    snippets = await service.retrieve_snippets("Need AG05 context", max_snippets=3)

    assert snippets == [{"source_id": "AG05-1", "text": "Useful AG05 plain text context"}]