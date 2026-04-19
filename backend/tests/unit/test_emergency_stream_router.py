"""Unit tests for emergency SSE stream auth and payload compatibility."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.api.v1.routers import emergency_stream
from app.domain.models.user import User, UserRole, UserStatus


@pytest.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Override global DB fixture for pure unit tests."""
    yield


def _build_request(query: str = "") -> Request:
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/api/v1/emergency/stream/events",
            "raw_path": b"/api/v1/emergency/stream/events",
            "query_string": query.encode(),
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        }
    )


def _build_active_user(user_id: str = "user-1") -> User:
    return User(
        _id=user_id,
        username="operator",
        email="operator@example.com",
        password_hash="hashed",
        full_name="Emergency Operator",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )


@pytest.mark.asyncio
async def test_get_stream_current_user_accepts_bearer_header_token(monkeypatch):
    user_service = SimpleNamespace(get_user_by_id=AsyncMock(return_value=_build_active_user("u-1")))
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="header-access-token")

    monkeypatch.setattr(
        emergency_stream,
        "decode_token",
        lambda token: {"type": "access", "sub": "u-1"} if token == "header-access-token" else None,
    )

    user = await emergency_stream.get_stream_current_user(
        request=_build_request(),
        credentials=credentials,
        user_service=user_service,
    )

    assert user.id == "u-1"
    user_service.get_user_by_id.assert_awaited_once_with("u-1")


@pytest.mark.asyncio
async def test_get_stream_current_user_accepts_access_token_query_param_when_header_absent(monkeypatch):
    observed = {}
    user_service = SimpleNamespace(get_user_by_id=AsyncMock(return_value=_build_active_user("u-2")))

    def fake_decode_token(token: str):
        observed["token"] = token
        return {"type": "access", "sub": "u-2"}

    monkeypatch.setattr(emergency_stream, "decode_token", fake_decode_token)

    user = await emergency_stream.get_stream_current_user(
        request=_build_request(query="access_token=query-access-token"),
        credentials=None,
        user_service=user_service,
    )

    assert observed["token"] == "query-access-token"
    assert user.id == "u-2"
    user_service.get_user_by_id.assert_awaited_once_with("u-2")


@pytest.mark.asyncio
async def test_get_stream_current_user_rejects_missing_token():
    user_service = SimpleNamespace(get_user_by_id=AsyncMock())

    with pytest.raises(HTTPException) as exc_info:
        await emergency_stream.get_stream_current_user(
            request=_build_request(),
            credentials=None,
            user_service=user_service,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing authentication credentials"
    user_service.get_user_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_stream_current_user_rejects_invalid_token(monkeypatch):
    user_service = SimpleNamespace(get_user_by_id=AsyncMock())
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-token")
    monkeypatch.setattr(emergency_stream, "decode_token", lambda _token: None)

    with pytest.raises(HTTPException) as exc_info:
        await emergency_stream.get_stream_current_user(
            request=_build_request(),
            credentials=credentials,
            user_service=user_service,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authentication credentials"
    user_service.get_user_by_id.assert_not_awaited()


class _FakeCursor:
    def __init__(self, docs):
        self._docs = docs
        self._iter = iter(())

    def sort(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def __aiter__(self):
        self._iter = iter(self._docs)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class _FakeCollection:
    def __init__(self, *, latest_updated_at: datetime, changed_docs):
        self._latest_updated_at = latest_updated_at
        self._changed_docs = changed_docs

    async def find_one(self, *_args, **_kwargs):
        return {"updated_at": self._latest_updated_at}

    def find(self, *_args, **_kwargs):
        return _FakeCursor(self._changed_docs)


class _FakeRequest:
    def __init__(self):
        self._checks = 0

    async def is_disconnected(self):
        self._checks += 1
        return self._checks > 1


def _decode_sse_data(raw_event: str):
    payload_line = next(line for line in raw_event.splitlines() if line.startswith("data: "))
    return json.loads(payload_line[6:])


@pytest.mark.asyncio
async def test_stream_emits_changed_items_with_id_derived_from__id(monkeypatch):
    base_time = datetime.utcnow() - timedelta(seconds=10)
    changed_time = base_time + timedelta(seconds=5)
    collection = _FakeCollection(
        latest_updated_at=base_time,
        changed_docs=[{"_id": "haz-1", "updated_at": changed_time, "name": "Flood zone"}],
    )

    monkeypatch.setattr(emergency_stream, "POLL_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(emergency_stream, "HEARTBEAT_INTERVAL_SECONDS", 9999.0)
    monkeypatch.setattr(emergency_stream, "LOOP_SLEEP_SECONDS", 0.0)

    stream = emergency_stream._stream_collection_updates(
        request=_FakeRequest(),
        collection=collection,
        stream_name="hazards",
    )

    await anext(stream)  # connected event
    update_event = await anext(stream)
    payload = _decode_sse_data(update_event)

    assert payload["stream"] == "hazards"
    assert payload["count"] == 1
    assert payload["items"][0]["_id"] == "haz-1"
    assert payload["items"][0]["id"] == "haz-1"

    await stream.aclose()