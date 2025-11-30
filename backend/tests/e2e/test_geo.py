"""E2E tests for geospatial endpoints."""

import pytest
import time
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_find_nearby_assets(test_client: AsyncClient):
    """Test finding assets nearby coordinates."""
    # Register and login first
    unique_username = f"geouser_{int(time.time() * 1000)}"
    unique_email = f"geo_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Geo User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Create an asset first
    unique_code = f"ASSET-{int(time.time() * 1000)}"
    asset_response = await test_client.post(
        "/api/v1/assets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_code": unique_code,
            "name": "Test Asset for Geo",
            "feature_type": "Trạm điện",
            "feature_code": "tram_dien",
            "geometry": {
                "type": "Point",
                "coordinates": [108.2544869184494, 15.974846711696628],
            },
        },
    )
    assert asset_response.status_code in [200, 201]

    # Find nearby assets
    response = await test_client.get(
        "/api/v1/geo/assets/nearby",
        params={
            "lng": 108.2544869184494,
            "lat": 15.974846711696628,
            "radius_meters": 1000,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_find_assets_in_bounds(test_client: AsyncClient):
    """Test finding assets within bounding box."""
    # Register and login first
    unique_username = f"boundsuser_{int(time.time() * 1000)}"
    unique_email = f"bounds_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Bounds User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Find assets in bounds
    response = await test_client.get(
        "/api/v1/geo/assets/within-bounds",
        params={
            "min_lng": 108.0,
            "min_lat": 15.0,
            "max_lng": 109.0,
            "max_lat": 16.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_calculate_distance_to_asset(test_client: AsyncClient):
    """Test calculating distance to an asset."""
    # Register and login first
    unique_username = f"distanceuser_{int(time.time() * 1000)}"
    unique_email = f"distance_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Distance User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Create an asset first
    unique_code = f"ASSET-{int(time.time() * 1000)}"
    asset_response = await test_client.post(
        "/api/v1/assets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_code": unique_code,
            "name": "Test Asset for Distance",
            "feature_type": "Trạm điện",
            "feature_code": "tram_dien",
            "geometry": {
                "type": "Point",
                "coordinates": [108.2544869184494, 15.974846711696628],
            },
        },
    )
    assert asset_response.status_code in [200, 201]
    asset_data = asset_response.json()
    asset_id = asset_data.get("id") or asset_data.get("_id")

    # Calculate distance
    response = await test_client.get(
        f"/api/v1/geo/assets/{asset_id}/distance-to",
        params={
            "lng": 108.255,
            "lat": 15.975,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "distance_meters" in data
    assert "distance_km" in data
