"""E2E tests for health check endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_root_endpoint(test_client: AsyncClient):
    """Test root endpoint."""
    response = await test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_health_check(test_client: AsyncClient):
    """Test health check endpoint."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
