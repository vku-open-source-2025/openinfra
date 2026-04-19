"""Unit tests for request context middleware request-id propagation."""

from uuid import UUID

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware.request_context_middleware import RequestContextMiddleware
from app.middleware.request_id import REQUEST_ID_HEADER


@pytest.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Override global test DB fixture for pure middleware unit tests."""
    yield


def _build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/ping")
    async def ping(request: Request):
        return {"request_id": getattr(request.state, "request_id", None)}

    return app


def test_request_id_header_is_propagated_when_provided():
    app = _build_test_app()
    client = TestClient(app)

    response = client.get("/ping", headers={REQUEST_ID_HEADER: "req-test-123"})

    assert response.status_code == 200
    assert response.headers.get(REQUEST_ID_HEADER) == "req-test-123"
    assert response.json()["request_id"] == "req-test-123"


def test_request_id_is_generated_when_header_missing():
    app = _build_test_app()
    client = TestClient(app)

    response = client.get("/ping")

    assert response.status_code == 200
    request_id = response.headers.get(REQUEST_ID_HEADER)
    assert request_id
    assert response.json()["request_id"] == request_id

    parsed_uuid = UUID(request_id)
    assert str(parsed_uuid) == request_id
