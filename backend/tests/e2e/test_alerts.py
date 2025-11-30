"""E2E tests for alert endpoints."""

import pytest
import time
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_list_alerts(test_client: AsyncClient):
    """Test listing alerts."""
    # Register and login first
    unique_username = f"alertuser_{int(time.time() * 1000)}"
    unique_email = f"alert_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Alert User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # List alerts
    response = await test_client.get(
        "/api/v1/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_alert_by_id(test_client: AsyncClient):
    """Test getting alert by ID - alerts are typically created by the system."""
    # Register and login first
    unique_username = f"getalert_{int(time.time() * 1000)}"
    unique_email = f"getalert_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Get Alert User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # List alerts first to get an ID if any exist
    list_response = await test_client.get(
        "/api/v1/alerts", headers={"Authorization": f"Bearer {token}"}
    )
    assert list_response.status_code == 200
    alerts = list_response.json()

    # If alerts exist, test getting one by ID
    if alerts:
        alert_id = alerts[0].get("id") or alerts[0].get("_id")
        response = await test_client.get(
            f"/api/v1/alerts/{alert_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        response_id = data.get("id") or data.get("_id")
        assert response_id == alert_id
