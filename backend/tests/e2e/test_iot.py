"""E2E tests for IoT endpoints."""

import pytest
import time
from datetime import datetime, timedelta
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_list_sensors(test_client: AsyncClient):
    """Test listing IoT sensors."""
    # Register and login first
    unique_username = f"iotuser_{int(time.time() * 1000)}"
    unique_email = f"iot_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "IoT User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # List sensors
    response = await test_client.get(
        "/api/v1/iot/sensors", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_create_sensor(test_client: AsyncClient):
    """Test creating an IoT sensor."""
    # Register and login first
    unique_username = f"createsensor_{int(time.time() * 1000)}"
    unique_email = f"createsensor_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Create Sensor User",
            "role": "admin",
        },
    )

    login_response = await test_client.post(
        "/api/v1/auth/login", json={"username": unique_username, "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    # Create an asset first (required for sensor)
    unique_code = f"ASSET-{int(time.time() * 1000)}"
    asset_response = await test_client.post(
        "/api/v1/assets/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_code": unique_code,
            "name": "Test Asset for Sensor",
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

    # Create sensor
    unique_sensor_code = f"SENSOR-{int(time.time() * 1000)}"
    response = await test_client.post(
        "/api/v1/iot/sensors",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sensor_code": unique_sensor_code,
            "asset_id": asset_id,
            "sensor_type": "temperature",
            "measurement_unit": "celsius",
            "sample_rate": 60,
        },
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["sensor_code"] == unique_sensor_code
    assert data["asset_id"] == asset_id


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_sensor_by_id(test_client: AsyncClient):
    """Test getting sensor by ID."""
    # Register and login first
    unique_username = f"getsensor_{int(time.time() * 1000)}"
    unique_email = f"getsensor_{int(time.time() * 1000)}@example.com"

    await test_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Get Sensor User",
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

    # Create sensor first
    unique_sensor_code = f"SENSOR-{int(time.time() * 1000)}"
    create_response = await test_client.post(
        "/api/v1/iot/sensors",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sensor_code": unique_sensor_code,
            "asset_id": asset_id,
            "sensor_type": "humidity",
            "measurement_unit": "percent",
            "sample_rate": 120,
        },
    )
    assert create_response.status_code in [200, 201]
    sensor_data = create_response.json()
    sensor_id = sensor_data.get("id") or sensor_data.get("_id")

    # Get sensor
    response = await test_client.get(
        f"/api/v1/iot/sensors/{sensor_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    response_id = data.get("id") or data.get("_id")
    assert response_id == sensor_id
