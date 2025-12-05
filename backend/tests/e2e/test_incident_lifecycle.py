import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from app.domain.models.maintenance import MaintenanceStatus
from app.domain.models.incident import IncidentStatus, ResolutionType

@pytest.mark.asyncio
async def test_incident_lifecycle(
    client: AsyncClient,
    test_user_token: str,
    test_admin_token: str
):
    """
    Test the complete incident lifecycle:
    1. Public: Report incident -> Incident Created (REPORTED)
    2. Admin: Assign technician -> Maintenance Created, Incident Updated (INVESTIGATING)
    3. Technician: Start maintenance -> Maintenance (IN_PROGRESS)
    4. Technician: Complete maintenance (with cost) -> Maintenance (WAITING_APPROVAL)
    5. Admin: Approve cost -> Maintenance (COMPLETED), Incident (RESOLVED)
    """

    # 1. Report Incident (Public)
    incident_data = {
        "title": "Broken Street Light",
        "description": "Light is flickering and then goes off",
        "category": "malfunction",
        "severity": "medium",
        "photos": ["http://example.com/photo1.jpg"],
        # Assuming we have a valid asset_id from setup or we create one.
        # For E2E we might mock or rely on seed data.
        # If no asset, maintenance creation fails. 
        # Let's assume we can create an asset first or use a fake ID if the system mocks DB.
        # But this is E2E, so we need real DB interaction usually.
        # For this test, I will create an asset first to ensure success.
        "asset_id": "test_asset_id_placeholder" 
    }
    
    # Create Asset First (Admin)
    asset_data = {
        "feature_type": "Street Light",
        "feature_code": "SL-TEST-001",
        "geometry": {"type": "Point", "coordinates": [108.0, 16.0]}
    }
    response = await client.post(
        "/api/v1/assets", 
        json=asset_data, 
        headers={"Authorization": f"Bearer {test_admin_token}"}
    )
    # If this fails (e.g. 404 router), we might need to adjust. Assuming /api/v1/assets exists.
    # If not, we skip asset creation and hope for the best or mock.
    # Based on file listing, `assets.py` router exists.
    assert response.status_code == 201
    asset_id = response.json()["id"]
    incident_data["asset_id"] = asset_id

    # Report Incident
    response = await client.post("/api/v1/public/incidents", json=incident_data)
    assert response.status_code == 201
    incident = response.json()
    incident_id = incident["id"]
    assert incident["status"] == IncidentStatus.REPORTED.value

    # 2. Assign Technician (Admin)
    # Get a technician user ID. For test, we use admin ID as technician for simplicity or fetch one.
    # Assuming test_admin_token belongs to a user who can be assigned.
    # We need the user ID of the admin.
    reader = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {test_admin_token}"})
    admin_user_id = reader.json()["id"]

    response = await client.post(
        f"/api/v1/incidents/{incident_id}/assign",
        params={"assigned_to": admin_user_id},
        headers={"Authorization": f"Bearer {test_admin_token}"}
    )
    assert response.status_code == 200
    incident = response.json()
    assert incident["status"] == IncidentStatus.INVESTIGATING.value
    assert incident["maintenance_record_id"] is not None
    maintenance_id = incident["maintenance_record_id"]

    # 3. Start Maintenance (Technician)
    response = await client.post(
        f"/api/v1/maintenance/{maintenance_id}/start",
        json={"notes": "Starting work"},
        headers={"Authorization": f"Bearer {test_admin_token}"}
    )
    assert response.status_code == 200
    maintenance = response.json()
    assert maintenance["status"] == MaintenanceStatus.IN_PROGRESS.value

    # 4. Complete Maintenance (Technician)
    complete_data = {
        "work_performed": "Replaced bulb and ballast",
        "labor_cost": 200000,
        "parts_used": [
            {"part_name": "LED Bulb", "quantity": 1, "unit_cost": 150000}
        ],
        "parts_cost": 150000,  # This might be calculated by backend, but let's see logic.
        # Logic sums parts_cost from list.
    }
    response = await client.post(
        f"/api/v1/maintenance/{maintenance_id}/complete",
        json=complete_data,
        headers={"Authorization": f"Bearer {test_admin_token}"}
    )
    assert response.status_code == 200
    maintenance = response.json()
    # Cost > 0, so should be WAITING_APPROVAL
    assert maintenance["status"] == MaintenanceStatus.WAITING_APPROVAL.value
    assert maintenance["total_cost"] == 350000

    # 5. Approve Cost (Admin)
    response = await client.post(
        f"/api/v1/incidents/{incident_id}/approve-cost",
        headers={"Authorization": f"Bearer {test_admin_token}"}
    )
    assert response.status_code == 200
    incident = response.json()
    assert incident["status"] == IncidentStatus.RESOLVED.value
    assert incident["resolution_type"] == ResolutionType.FIXED.value

    # Verify Maintenance Status
    response = await client.get(
        f"/api/v1/maintenance/{maintenance_id}",
        headers={"Authorization": f"Bearer {test_admin_token}"}
    )
    assert response.status_code == 200
    maintenance = response.json()
    assert maintenance["status"] == MaintenanceStatus.COMPLETED.value
