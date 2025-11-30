"""E2E tests for notification endpoints."""

import pytest
import time
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_list_notifications(test_client: AsyncClient):
    """Test listing user notifications."""
    # Register and login first
    unique_username = f"notifuser_{int(time.time() * 1000)}"
    unique_email = f"notif_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Notification User",
            "role": "citizen",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # List notifications
    response = await test_client.get(
        "/api/v1/notifications", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_unread_count(test_client: AsyncClient):
    """Test getting unread notification count."""
    # Register and login first
    unique_username = f"unreadcount_{int(time.time() * 1000)}"
    unique_email = f"unreadcount_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Unread Count User",
            "role": "citizen",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Get unread count
    response = await test_client.get(
        "/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "unread_count" in data
    assert isinstance(data["unread_count"], int)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_mark_all_read(test_client: AsyncClient):
    """Test marking all notifications as read."""
    # Register and login first
    unique_username = f"markallread_{int(time.time() * 1000)}"
    unique_email = f"markallread_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Mark All Read User",
            "role": "citizen",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Mark all as read
    response = await test_client.post(
        "/api/v1/notifications/mark-all-read", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
