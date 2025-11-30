"""E2E tests for asset endpoints."""

import pytest
import time
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_create_asset(test_client: AsyncClient):
    """Test creating an asset."""
    # Register and login first
    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": "assetuser",
            "email": "asset@example.com",
            "password": "testpass123",
            "full_name": "Asset User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": "assetuser", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Create asset with unique code
    unique_code = f"TEST-{int(time.time() * 1000)}"
    response = await test_client.post(
        "/api/v1/assets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_code": unique_code,
            "name": "Test Asset",
            "feature_type": "Trạm điện",
            "feature_code": "tram_dien",
            "geometry": {
                "type": "Point",
                "coordinates": [108.2544869184494, 15.974846711696628],
            },
        },
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["asset_code"] == unique_code
    assert data["name"] == "Test Asset"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_list_assets(test_client: AsyncClient):
    """Test listing assets."""
    # Register and login first
    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": "listuser",
            "email": "list@example.com",
            "password": "testpass123",
            "full_name": "List User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": "listuser", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # List assets
    response = await test_client.get(
        "/api/v1/assets/", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_asset_by_id(test_client: AsyncClient):
    """Test getting asset by ID."""
    # Register and login first
    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": "getuser",
            "email": "get@example.com",
            "password": "testpass123",
            "full_name": "Get User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": "getuser", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Create asset first with unique code
    unique_code = f"GET-{int(time.time() * 1000)}"
    create_response = await test_client.post(
        "/api/v1/assets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_code": unique_code,
            "name": "Get Test Asset",
            "feature_type": "Trạm điện",
            "feature_code": "tram_dien",
            "geometry": {
                "type": "Point",
                "coordinates": [108.2544869184494, 15.974846711696628],
            },
        },
    )
    assert create_response.status_code in [200, 201]
    response_data = create_response.json()
    # Handle both 'id' and '_id' field names
    asset_id = response_data.get("id") or response_data.get("_id")
    assert asset_id is not None, f"Response missing id field: {response_data}"

    # Get asset
    response = await test_client.get(
        f"/api/v1/assets/{asset_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    # Handle both 'id' and '_id' field names
    response_id = data.get("id") or data.get("_id")
    assert response_id == asset_id
