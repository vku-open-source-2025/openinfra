"""E2E tests for incident endpoints."""

import pytest
import time
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_create_incident(test_client: AsyncClient):
    """Test creating an incident."""
    # Register and login first
    unique_username = f"incidentuser_{int(time.time() * 1000)}"
    unique_email = f"incident_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Incident User",
            "role": "citizen",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Create incident
    response = await test_client.post(
        "/api/v1/incidents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Broken Street Light",
            "description": "Street light is not working on Main Street",
            "category": "malfunction",
            "severity": "medium",
            "location": {
                "geometry": {
                    "type": "Point",
                    "coordinates": [108.2544869184494, 15.974846711696628],
                },
                "address": "123 Main Street",
            },
            "reported_via": "web",
        },
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["title"] == "Broken Street Light"
    assert data["status"] == "reported"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_list_incidents(test_client: AsyncClient):
    """Test listing incidents."""
    # Register and login first
    unique_username = f"listincident_{int(time.time() * 1000)}"
    unique_email = f"listincident_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "List Incident User",
            "role": "citizen",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # List incidents
    response = await test_client.get(
        "/api/v1/incidents", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_incident_by_id(test_client: AsyncClient):
    """Test getting incident by ID."""
    # Register and login first
    unique_username = f"getincident_{int(time.time() * 1000)}"
    unique_email = f"getincident_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Get Incident User",
            "role": "citizen",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Create incident first
    create_response = await test_client.post(
        "/api/v1/incidents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Get Test Incident",
            "description": "Test incident for get by id",
            "category": "damage",
            "severity": "low",
            "location": {
                "geometry": {
                    "type": "Point",
                    "coordinates": [108.2544869184494, 15.974846711696628],
                },
            },
        },
    )
    assert create_response.status_code in [200, 201]
    incident_data = create_response.json()
    incident_id = incident_data.get("id") or incident_data.get("_id")

    # Get incident
    response = await test_client.get(
        f"/api/v1/incidents/{incident_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    response_id = data.get("id") or data.get("_id")
    assert response_id == incident_id


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_acknowledge_incident(test_client: AsyncClient):
    """Test acknowledging an incident."""
    # Register and login as citizen first
    unique_username = f"ackincident_{int(time.time() * 1000)}"
    unique_email = f"ackincident_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Ack Incident User",
            "role": "citizen",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Create incident
    create_response = await test_client.post(
        "/api/v1/incidents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Incident to Acknowledge",
            "description": "Test incident for acknowledgment",
            "category": "safety_hazard",
            "severity": "high",
            "location": {
                "geometry": {
                    "type": "Point",
                    "coordinates": [108.2544869184494, 15.974846711696628],
                },
            },
        },
    )
    assert create_response.status_code in [200, 201]
    incident_data = create_response.json()
    incident_id = incident_data.get("id") or incident_data.get("_id")

    # Register admin user to acknowledge
    admin_username = f"admin_{int(time.time() * 1000)}"
    admin_email = f"admin_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": admin_username,
            "email": admin_email,
            "password": "testpass123",
            "full_name": "Admin User",
            "role": "admin",
        },
    )

    admin_login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": admin_username, "password": "testpass123"}
    )
    admin_token = admin_login_response.json()["access_token"]

    # Acknowledge incident
    response = await test_client.post(
        f"/api/v1/incidents/{incident_id}/acknowledge",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "acknowledged"
