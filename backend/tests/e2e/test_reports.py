"""E2E tests for report endpoints."""

import pytest
import time
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_list_reports(test_client: AsyncClient):
    """Test listing reports."""
    # Register and login first
    unique_username = f"reportuser_{int(time.time() * 1000)}"
    unique_email = f"report_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Report User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login",
        json={"username": unique_username, "password": "testpass123"},
    )
    token = login_response.json()["access_token"]

    # List reports
    response = await test_client.get(
        "/api/v1/reports", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_create_report(test_client: AsyncClient):
    """Test creating a report."""
    # Register and login first
    unique_username = f"createreport_{int(time.time() * 1000)}"
    unique_email = f"createreport_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Create Report User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login",
        json={"username": unique_username, "password": "testpass123"},
    )
    token = login_response.json()["access_token"]

    # Create report
    response = await test_client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "type": "asset_inventory",
            "name": f"Test Report {int(time.time())}",
            "description": "Test report for e2e testing",
            "format": "pdf",
            "parameters": {
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
            },
        },
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["type"] == "asset_inventory"
    assert data["status"] in ["pending", "completed"]  # Report may be auto-generated


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_report_by_id(test_client: AsyncClient):
    """Test getting report by ID."""
    # Register and login first
    unique_username = f"getreport_{int(time.time() * 1000)}"
    unique_email = f"getreport_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Get Report User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login",
        json={"username": unique_username, "password": "testpass123"},
    )
    token = login_response.json()["access_token"]

    # Create report first
    create_response = await test_client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "type": "maintenance_summary",
            "name": f"Get Test Report {int(time.time())}",
            "description": "Test report",
            "format": "pdf",
        },
    )
    assert create_response.status_code in [200, 201]
    report_data = create_response.json()
    report_id = report_data.get("id") or report_data.get("_id")

    # Get report
    response = await test_client.get(
        f"/api/v1/reports/{report_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    response_id = data.get("id") or data.get("_id")
    assert response_id == report_id
