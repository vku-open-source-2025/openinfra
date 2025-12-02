# API Endpoints Summary - Asset Lifecycle Management

This document summarizes all API endpoints that need to be implemented in the backend for the Asset Lifecycle & Maintenance History Management feature.

## Asset Lifecycle Endpoints

### 1. Get Asset with Lifecycle Data
- **Method**: `GET`
- **Path**: `/api/v1/assets/{id}/lifecycle`
- **Description**: Returns asset with full lifecycle information including health score, remaining lifespan, maintenance dates
- **Response**: `Asset` object with `lifecycle` field populated

### 2. Update Asset Lifecycle Status
- **Method**: `PUT`
- **Path**: `/api/v1/assets/{id}/lifecycle-status`
- **Body**: `{ lifecycle_status: "operational" | "under_repair" | "damaged" | "decommissioned" }`
- **Description**: Updates asset lifecycle status and triggers notifications if needed
- **Response**: Updated `Asset` object

### 3. Get Asset Health Score
- **Method**: `GET`
- **Path**: `/api/v1/assets/{id}/health-score`
- **Description**: Calculates and returns health score (0-100) with factor breakdown
- **Response**:
```json
{
  "health_score": 87,
  "factors": {
    "incident_frequency": 85,
    "incident_severity": 90,
    "maintenance_recency": 80,
    "maintenance_cost_trend": 75,
    "iot_sensor_alerts": 95
  }
}
```

## Document Management Endpoints

### 4. Get Asset Documents
- **Method**: `GET`
- **Path**: `/api/v1/assets/{id}/documents`
- **Description**: Returns list of all documents attached to asset
- **Response**: Array of `AssetAttachment` objects

### 5. Upload Asset Document
- **Method**: `POST`
- **Path**: `/api/v1/assets/{id}/documents`
- **Content-Type**: `multipart/form-data`
- **Body**:
  - `file`: File
  - `document_type`: string (optional)
  - `is_public`: boolean (optional)
- **Description**: Uploads a document to asset, stores in cloud storage
- **Response**: `AssetAttachment` object

### 6. Delete Asset Document
- **Method**: `DELETE`
- **Path**: `/api/v1/assets/{id}/attachments/{attachmentUrl}`
- **Description**: Deletes a document attachment
- **Response**: 204 No Content

## Report Generation Endpoints

### 7. Generate Asset Report
- **Method**: `POST`
- **Path**: `/api/v1/assets/{id}/reports`
- **Body**:
```json
{
  "report_type": "maintenance_summary" | "incident_summary" | "lifecycle_overview" | "end_of_life_forecast" | "custom",
  "format": "pdf" | "excel",
  "filters": {
    "date_from": "2024-01-01",
    "date_to": "2024-12-31",
    "severity": "high",
    "cost_min": 1000,
    "cost_max": 5000
  }
}
```
- **Description**: Generates a report for the asset
- **Response**:
```json
{
  "report_url": "https://storage.example.com/reports/report-123.pdf",
  "report_id": "report-123"
}
```

## Maintenance History Endpoints

### 8. Get Maintenance History (Filtered)
- **Method**: `GET`
- **Path**: `/api/v1/maintenance/asset/{assetId}/history`
- **Query Parameters**:
  - `date_from`: string (ISO date)
  - `date_to`: string (ISO date)
  - `technician`: string
  - `cost_min`: number
  - `cost_max`: number
  - `type`: "preventive" | "corrective" | "predictive" | "emergency"
  - `approval_status`: "pending" | "approved" | "rejected"
  - `skip`: number
  - `limit`: number
- **Description**: Returns filtered maintenance history for an asset
- **Response**: Array of `Maintenance` objects

### 9. Approve Maintenance Record
- **Method**: `POST`
- **Path**: `/api/v1/maintenance/{id}/approve`
- **Body**:
```json
{
  "approval_status": "approved",
  "rejection_reason": null
}
```
- **Description**: Approves a maintenance record (admin only)
- **Response**: Updated `Maintenance` object

### 10. Reject Maintenance Record
- **Method**: `POST`
- **Path**: `/api/v1/maintenance/{id}/reject`
- **Body**:
```json
{
  "rejection_reason": "Incomplete information"
}
```
- **Description**: Rejects a maintenance record with reason (admin only)
- **Response**: Updated `Maintenance` object

## Preventive Maintenance Endpoints

### 11. Get Preventive Maintenance Plan
- **Method**: `GET`
- **Path**: `/api/v1/assets/{assetId}/preventive-maintenance`
- **Description**: Returns preventive maintenance plan for asset (null if not configured)
- **Response**: `PreventiveMaintenancePlan` or `null`

### 12. Create Preventive Maintenance Plan
- **Method**: `POST`
- **Path**: `/api/v1/preventive-maintenance`
- **Body**:
```json
{
  "asset_id": "asset-123",
  "cycle_days": 180,
  "cycle_description": "Every 6 months",
  "warning_days": 7,
  "responsible_team": "Maintenance Team A",
  "assigned_technician": "tech-456"
}
```
- **Description**: Creates a new preventive maintenance plan
- **Response**: `PreventiveMaintenancePlan` object

### 13. Update Preventive Maintenance Plan
- **Method**: `PUT`
- **Path**: `/api/v1/preventive-maintenance/{planId}`
- **Body**: Partial `PreventiveMaintenancePlanUpdateRequest`
- **Description**: Updates an existing preventive maintenance plan
- **Response**: Updated `PreventiveMaintenancePlan` object

### 14. Get Upcoming Preventive Maintenance Tasks
- **Method**: `GET`
- **Path**: `/api/v1/assets/{assetId}/preventive-maintenance/tasks`
- **Description**: Returns upcoming scheduled maintenance tasks
- **Response**: Array of `PreventiveMaintenanceTask` objects

### 15. Get Overdue Preventive Maintenance Tasks
- **Method**: `GET`
- **Path**: `/api/v1/assets/{assetId}/preventive-maintenance/overdue`
- **Description**: Returns overdue maintenance tasks
- **Response**: Array of `PreventiveMaintenanceTask` objects

## Notes

- All endpoints should follow RESTful conventions
- Authentication required for all endpoints (JWT token)
- Admin-only endpoints: approve/reject maintenance, create/update preventive maintenance plans
- Health score calculation should happen server-side for accuracy
- Document storage should use cloud storage (S3/GCS)
- Report generation should be async (consider using background jobs)
- All dates should be in ISO 8601 format
- Pagination should be implemented for list endpoints
