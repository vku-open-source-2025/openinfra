"""E2E tests for maintenance endpoints."""

import pytest
import time
from datetime import datetime, timedelta
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_create_maintenance(test_client: AsyncClient):
    """Test creating a maintenance work order."""
    # Register and login first
    unique_username = f"maintuser_{int(time.time() * 1000)}"
    unique_email = f"maint_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Maintenance User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Create an asset first (required for maintenance)
    unique_code = f"ASSET-{int(time.time() * 1000)}"
    asset_response = await test_client.post(
        "/api/v1/assets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_code": unique_code,
            "name": "Test Asset for Maintenance",
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

    # Create maintenance
    scheduled_date = datetime.utcnow() + timedelta(days=7)
    response = await test_client.post(
        "/api/v1/maintenance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_id": asset_id,
            "type": "preventive",
            "priority": "medium",
            "title": "Routine Inspection",
            "description": "Monthly preventive maintenance check",
            "scheduled_date": scheduled_date.isoformat(),
            "estimated_duration": 120,
        },
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["title"] == "Routine Inspection"
    assert data["asset_id"] == asset_id
    assert data["status"] == "scheduled"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_list_maintenance(test_client: AsyncClient):
    """Test listing maintenance records."""
    # Register and login first
    unique_username = f"listmaint_{int(time.time() * 1000)}"
    unique_email = f"listmaint_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "List Maintenance User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # List maintenance
    response = await test_client.get(
        "/api/v1/maintenance", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_maintenance_by_id(test_client: AsyncClient):
    """Test getting maintenance by ID."""
    # Register and login first
    unique_username = f"getmaint_{int(time.time() * 1000)}"
    unique_email = f"getmaint_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Get Maintenance User",
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
            "name": "Test Asset",
            "feature_type": "Trạm điện",
            "feature_code": "tram_dien",
            "geometry": {
                "type": "Point",
                "coordinates": [108.2544869184494, 15.974846711696628],
            },
        },
    )
    asset_data = asset_response.json()
    asset_id = asset_data.get("id") or asset_data.get("_id")

    # Create maintenance first
    scheduled_date = datetime.utcnow() + timedelta(days=7)
    create_response = await test_client.post(
        "/api/v1/maintenance",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_id": asset_id,
            "type": "preventive",
            "priority": "high",
            "title": "Get Test Maintenance",
            "description": "Test maintenance record",
            "scheduled_date": scheduled_date.isoformat(),
            "estimated_duration": 60,
        },
    )
    assert create_response.status_code in [200, 201]
    maintenance_data = create_response.json()
    maintenance_id = maintenance_data.get("id") or maintenance_data.get("_id")

    # Get maintenance
    response = await test_client.get(
        f"/api/v1/maintenance/{maintenance_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    response_id = data.get("id") or data.get("_id")
    assert response_id == maintenance_id


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_upcoming_maintenance(test_client: AsyncClient):
    """Test getting upcoming maintenance."""
    # Register and login first
    unique_username = f"upcomingmaint_{int(time.time() * 1000)}"
    unique_email = f"upcomingmaint_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Upcoming Maintenance User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Get upcoming maintenance
    response = await test_client.get(
        "/api/v1/maintenance/upcoming?days=7", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
