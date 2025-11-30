"""E2E tests for budget endpoints."""

import pytest
import time
from datetime import datetime, timedelta
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_create_budget(test_client: AsyncClient):
    """Test creating a budget."""
    # Register and login first
    unique_username = f"budgetuser_{int(time.time() * 1000)}"
    unique_email = f"budget_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Budget User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Create budget
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=365)
    response = await test_client.post(
        "/api/v1/budgets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "fiscal_year": start_date.year,
            "period_type": "annual",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "name": f"Test Budget {int(time.time())}",
            "description": "Test budget for e2e testing",
            "category": "maintenance",
            "total_allocated": 1000000.0,
            "currency": "VND",
        },
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["total_allocated"] == 1000000.0
    assert data["status"] == "draft"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_list_budgets(test_client: AsyncClient):
    """Test listing budgets."""
    # Register and login first
    unique_username = f"listbudget_{int(time.time() * 1000)}"
    unique_email = f"listbudget_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "List Budget User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # List budgets
    response = await test_client.get(
        "/api/v1/budgets", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_budget_by_id(test_client: AsyncClient):
    """Test getting budget by ID."""
    # Register and login first
    unique_username = f"getbudget_{int(time.time() * 1000)}"
    unique_email = f"getbudget_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Get Budget User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Create budget first
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=365)
    create_response = await test_client.post(
        "/api/v1/budgets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "fiscal_year": start_date.year,
            "period_type": "annual",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "name": f"Get Test Budget {int(time.time())}",
            "description": "Test budget",
            "category": "maintenance",
            "total_allocated": 500000.0,
            "currency": "VND",
        },
    )
    assert create_response.status_code in [200, 201]
    budget_data = create_response.json()
    budget_id = budget_data.get("id") or budget_data.get("_id")

    # Get budget
    response = await test_client.get(
        f"/api/v1/budgets/{budget_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    response_id = data.get("id") or data.get("_id")
    assert response_id == budget_id


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_list_budget_transactions(test_client: AsyncClient):
    """Test listing budget transactions."""
    # Register and login first
    unique_username = f"listtransbudget_{int(time.time() * 1000)}"
    unique_email = f"listtransbudget_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "List Transaction Budget User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Create budget first
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=365)
    budget_response = await test_client.post(
        "/api/v1/budgets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "fiscal_year": start_date.year,
            "period_type": "annual",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "name": f"Transaction Budget {int(time.time())}",
            "description": "Budget for transaction test",
            "category": "maintenance",
            "total_allocated": 1000000.0,
            "currency": "VND",
        },
    )
    assert budget_response.status_code in [200, 201]
    budget_data = budget_response.json()
    budget_id = budget_data.get("id") or budget_data.get("_id")

    # List transactions (should be empty for new budget)
    response = await test_client.get(
        f"/api/v1/budgets/{budget_id}/transactions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
