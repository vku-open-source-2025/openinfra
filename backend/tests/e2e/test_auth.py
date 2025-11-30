"""E2E tests for authentication endpoints."""
import pytest
import time
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_register_user(test_client: AsyncClient):
    """Test user registration."""
    # Use unique username to avoid conflicts
    unique_username = f"testuser_{int(time.time() * 1000)}"
    unique_email = f"test_{int(time.time() * 1000)}@example.com"
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test User",
            "role": "citizen"
        }
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert "access_token" in data or "id" in data


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_login(test_client: AsyncClient):
    """Test user login."""
    # First register a user with unique username
    unique_username = f"loginuser_{int(time.time() * 1000)}"
    unique_email = f"login_{int(time.time() * 1000)}@example.com"
    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Login User",
            "role": "citizen"
        }
    )

    # Then login
    response = await test_client.post(
        "/api/v1/auth/login",
        json={
            "username": unique_username,
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_login_invalid_credentials(test_client: AsyncClient):
    """Test login with invalid credentials."""
    response = await test_client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent",
            "password": "wrongpass"
        }
    )
    assert response.status_code == 401


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_current_user(test_client: AsyncClient):
    """Test getting current user info."""
    # Register and login first with unique username
    unique_username = f"currentuser_{int(time.time() * 1000)}"
    unique_email = f"current_{int(time.time() * 1000)}@example.com"
    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Current User",
            "role": "citizen"
        }
    )

    login_response = await test_client.post(
        "/api/v1/auth/login",
        json={
            "username": unique_username,
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]

    # Get current user
    response = await test_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == unique_username
