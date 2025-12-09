# API Documentation for Frontend

This document provides a comprehensive overview of all APIs available for frontend integration, including endpoints, request/response formats, authentication, and data flow.

## Table of Contents

1. [Base Configuration](#base-configuration)
2. [Authentication](#authentication)
3. [Users](#users)
4. [Assets](#assets)
5. [Maintenance](#maintenance)
6. [Incidents](#incidents)
7. [Alerts](#alerts)
8. [Budgets](#budgets)
9. [IoT Sensors](#iot-sensors)
10. [IoT NGSI-LD API](#iot-ngsi-ld-api)
11. [Notifications](#notifications)
12. [Reports](#reports)
13. [Geospatial](#geospatial)
14. [Public APIs](#public-apis)
15. [Data Ingestion](#data-ingestion)
16. [Data Flow Diagrams](#data-flow-diagrams)

---

## Base Configuration

### Base URL
- **Development**: `/api/v1` (relative) or `http://localhost:8000/api/v1`
- **Production**: Configure via `VITE_BASE_API_URL` environment variable

### Authentication
- **Type**: Bearer Token (JWT)
- **Header**: `Authorization: Bearer <access_token>`
- **Token Storage**: Frontend stores tokens in auth store (Zustand)
- **Auto-refresh**: Implemented via axios interceptors

### HTTP Client Setup
The frontend uses axios with interceptors for:
- Automatic token injection
- 401 error handling (logout and redirect)
- Error logging

```typescript
// Base client configuration
baseURL: "/api/v1"
headers: {
  "Content-Type": "application/json",
  "Authorization": "Bearer <token>" // Auto-injected
}
```

---

## Authentication

**Base Path**: `/api/v1/auth`

### 1. Register User
**POST** `/auth/register`

**Request Body**:
```json
{
  "username": "string",
  "email": "string (email format)",
  "password": "string",
  "full_name": "string",
  "phone": "string (optional)"
}
```

**Response** (201 Created):
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "string",
    "username": "string",
    "email": "string",
    "full_name": "string",
    "role": "citizen",
    "status": "active"
  }
}
```

**Data Flow**:
1. Frontend sends registration data
2. Backend creates user with role "citizen" (default)
3. Backend generates JWT tokens
4. Frontend stores tokens and user info in auth store

---

### 2. Login
**POST** `/auth/login`

**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Response** (200 OK):
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": { /* UserResponse object */ }
}
```

**Data Flow**:
1. Frontend sends credentials
2. Backend validates credentials
3. Backend generates tokens
4. Frontend stores tokens and redirects to dashboard

---

### 3. Refresh Token
**POST** `/auth/refresh`

**Request Body**:
```json
{
  "refresh_token": "string"
}
```

**Response** (200 OK):
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": { /* UserResponse object */ }
}
```

**Usage**: Called automatically when access token expires

---

### 4. Logout
**POST** `/auth/logout`

**Headers**: `Authorization: Bearer <token>` (required)

**Response** (200 OK):
```json
{
  "message": "Logged out successfully"
}
```

**Frontend Action**: Clear tokens from auth store

---

### 5. Change Password
**POST** `/auth/change-password`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**:
```json
{
  "current_password": "string",
  "new_password": "string"
}
```

**Response** (200 OK):
```json
{
  "message": "Password changed successfully"
}
```

---

## Users

**Base Path**: `/api/v1/users`

### 1. Get Current User Profile
**GET** `/users/me`

**Headers**: `Authorization: Bearer <token>` (required)

**Response** (200 OK):
```json
{
  "id": "string",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "phone": "string | null",
  "role": "citizen | technician | admin | manager",
  "status": "active | inactive",
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime"
}
```

---

### 2. Update Current User Profile
**PUT** `/users/me`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body** (all fields optional):
```json
{
  "email": "string",
  "full_name": "string",
  "phone": "string"
}
```

**Response** (200 OK): UserResponse object

---

### 3. List Users (Admin Only)
**GET** `/users?skip=0&limit=100&role=technician&status=active`

**Headers**: `Authorization: Bearer <token>` (required, admin permission)

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100, max: 100)
- `role`: string (optional)
- `status`: string (optional)

**Response** (200 OK): Array of UserResponse objects

---

### 4. Create User (Admin Only)
**POST** `/users`

**Headers**: `Authorization: Bearer <token>` (required, admin permission)

**Request Body**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string",
  "phone": "string",
  "role": "citizen | technician | admin | manager"
}
```

**Response** (201 Created): UserResponse object

---

### 5. Get User by ID (Admin Only)
**GET** `/users/{user_id}`

**Headers**: `Authorization: Bearer <token>` (required, admin permission)

**Response** (200 OK): UserResponse object

---

### 6. Update User (Admin Only)
**PUT** `/users/{user_id}`

**Headers**: `Authorization: Bearer <token>` (required, admin permission)

**Request Body**: UserUpdateRequest (all fields optional)

**Response** (200 OK): UserResponse object

---

### 7. Delete User (Admin Only)
**DELETE** `/users/{user_id}`

**Headers**: `Authorization: Bearer <token>` (required, admin permission)

**Response** (200 OK):
```json
{
  "message": "User deactivated successfully"
}
```

**Note**: Soft delete (deactivation)

---

## Assets

**Base Path**: `/api/v1/assets`

### 1. List Assets
**GET** `/assets?skip=0&limit=100&feature_type=road&status=active&category=highway`

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100, max: 100)
- `feature_type`: string (optional)
- `status`: string (optional)
- `category`: string (optional)

**Response** (200 OK): Array of Asset objects

**Asset Object**:
```json
{
  "id": "string",
  "asset_code": "string",
  "name": "string",
  "feature_type": "string",
  "feature_code": "string",
  "geometry": {
    "type": "Point | LineString | Polygon | MultiPoint | MultiLineString | MultiPolygon",
    "coordinates": [/* GeoJSON coordinates */]
  },
  "category": "string",
  "status": "active | inactive | maintenance | decommissioned",
  "location": {
    "address": "string",
    "coordinates": {
      "longitude": "float",
      "latitude": "float"
    }
  },
  "properties": {},
  "attachments": [],
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime"
}
```

**Data Flow**:
1. Frontend requests assets with filters
2. Backend queries MongoDB with geospatial indexes
3. Returns paginated results
4. Frontend displays on map/table

---

### 2. Get Asset by ID
**GET** `/assets/{id}`

**Response** (200 OK): Asset object

---

### 3. Create Asset
**POST** `/assets`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**:
```json
{
  "asset_code": "string",
  "name": "string",
  "feature_type": "string",
  "feature_code": "string",
  "geometry": {
    "type": "Point",
    "coordinates": [longitude, latitude]
  },
  "category": "string",
  "status": "active",
  "location": {
    "address": "string",
    "coordinates": {
      "longitude": "float",
      "latitude": "float"
    }
  },
  "properties": {}
}
```

**Response** (200 OK): Asset object

**Data Flow**:
1. Frontend sends asset data (from map click or form)
2. Backend validates geometry
3. Backend creates asset with audit log
4. Returns created asset
5. Frontend updates map/table

---

### 4. Update Asset
**PUT** `/assets/{id}`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**: AssetUpdate (partial fields)

**Response** (200 OK): Asset object

---

### 5. Delete Asset
**DELETE** `/assets/{id}`

**Headers**: `Authorization: Bearer <token>` (required)

**Response** (200 OK):
```json
{
  "message": "Asset deleted successfully"
}
```

**Note**: Soft delete

---

### 6. Get Asset History
**GET** `/assets/{id}/history?limit=100`

**Query Parameters**:
- `limit`: int (default: 100, max: 500)

**Response** (200 OK):
```json
{
  "data": [/* Array of audit log entries */],
  "count": 10
}
```

---

### 7. Upload Asset Photo
**POST** `/assets/{id}/photos`

**Headers**: `Authorization: Bearer <token>` (required)

**Request**: `multipart/form-data`
- `file`: File (image)

**Response** (200 OK): Asset object (with updated attachments)

**Data Flow**:
1. Frontend uploads image file
2. Backend stores file in storage service
3. Backend adds attachment URL to asset
4. Returns updated asset

---

### 8. Upload Asset Attachment
**POST** `/assets/{id}/attachments`

**Headers**: `Authorization: Bearer <token>` (required)

**Request**: `multipart/form-data`
- `file`: File (any document type)

**Response** (200 OK): Asset object

---

### 9. Delete Asset Attachment
**DELETE** `/assets/{id}/attachments/{attachment_url}`

**Headers**: `Authorization: Bearer <token>` (required)

**Response** (200 OK):
```json
{
  "message": "Attachment deleted successfully"
}
```

---

## Maintenance

**Base Path**: `/api/v1/maintenance`

### 1. List Maintenance Records
**GET** `/maintenance?skip=0&limit=100&asset_id=xxx&status=scheduled&assigned_to=yyy&priority=high`

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100, max: 100)
- `asset_id`: string (optional)
- `status`: string (optional)
- `assigned_to`: string (optional)
- `priority`: string (optional)

**Response** (200 OK): Array of Maintenance objects

**Maintenance Object**:
```json
{
  "id": "string",
  "work_order_number": "string",
  "asset_id": "string",
  "title": "string",
  "description": "string",
  "priority": "low | medium | high | urgent",
  "status": "scheduled | in_progress | completed | cancelled",
  "scheduled_date": "ISO datetime",
  "started_at": "ISO datetime | null",
  "completed_at": "ISO datetime | null",
  "assigned_to": "string | null",
  "technician": "string",
  "estimated_cost": "float | null",
  "actual_cost": "float | null",
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime"
}
```

---

### 2. Get Upcoming Maintenance
**GET** `/maintenance/upcoming?days=7`

**Query Parameters**:
- `days`: int (default: 7, max: 30)

**Response** (200 OK): Array of Maintenance objects

---

### 3. Create Maintenance
**POST** `/maintenance`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**:
```json
{
  "asset_id": "string",
  "title": "string",
  "description": "string",
  "priority": "low | medium | high | urgent",
  "scheduled_date": "ISO datetime",
  "estimated_cost": "float",
  "technician": "string"
}
```

**Response** (201 Created): Maintenance object

**Data Flow**:
1. Frontend creates maintenance request
2. Backend creates work order
3. Backend may trigger notifications
4. Returns created maintenance record

---

### 4. Get Maintenance by ID
**GET** `/maintenance/{maintenance_id}`

**Response** (200 OK): Maintenance object

---

### 5. Update Maintenance
**PUT** `/maintenance/{maintenance_id}`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**: MaintenanceUpdate (partial fields)

**Response** (200 OK): Maintenance object

---

### 6. Assign Maintenance
**POST** `/maintenance/{maintenance_id}/assign?assigned_to={user_id}`

**Headers**: `Authorization: Bearer <token>` (required)

**Query Parameters**:
- `assigned_to`: string (required)

**Response** (200 OK): Maintenance object

---

### 7. Start Maintenance
**POST** `/maintenance/{maintenance_id}/start`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**:
```json
{
  "actual_start_time": "ISO datetime"
}
```

**Response** (200 OK): Maintenance object

---

### 8. Complete Maintenance
**POST** `/maintenance/{maintenance_id}/complete`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**:
```json
{
  "completion_notes": "string",
  "actual_cost": "float",
  "quality_checks": []
}
```

**Response** (200 OK): Maintenance object

---

### 9. Cancel Maintenance
**POST** `/maintenance/{maintenance_id}/cancel?cancellation_reason=string`

**Headers**: `Authorization: Bearer <token>` (required)

**Query Parameters**:
- `cancellation_reason`: string (required)

**Response** (200 OK): Maintenance object

---

### 10. Upload Maintenance Photos
**POST** `/maintenance/{maintenance_id}/photos?photo_type=before`

**Headers**: `Authorization: Bearer <token>` (required)

**Query Parameters**:
- `photo_type`: "before" | "after" (default: "after")

**Request**: `multipart/form-data`
- `files`: File[] (multiple images)

**Response** (200 OK): Maintenance object

---

### 11. Get Asset Maintenance
**GET** `/maintenance/asset/{asset_id}?skip=0&limit=100`

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100, max: 100)

**Response** (200 OK): Array of Maintenance objects

**Note**: This endpoint is used by the frontend to display maintenance logs for a specific asset.

---

## Incidents

**Base Path**: `/api/v1/incidents`

### 1. List Incidents
**GET** `/incidents?skip=0&limit=100&status=open&severity=high&asset_id=xxx`

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100, max: 100)
- `status`: string (optional)
- `severity`: string (optional)
- `asset_id`: string (optional)

**Response** (200 OK): Array of Incident objects

**Incident Object**:
```json
{
  "id": "string",
  "incident_code": "string",
  "title": "string",
  "description": "string",
  "severity": "low | medium | high | critical",
  "status": "reported | acknowledged | assigned | in_progress | resolved | closed",
  "asset_id": "string | null",
  "location": {
    "address": "string",
    "coordinates": {
      "longitude": "float",
      "latitude": "float"
    }
  },
  "reported_by": "string | null",
  "reporter_type": "citizen | technician | admin | manager",
  "assigned_to": "string | null",
  "upvotes": 0,
  "comments": [],
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime"
}
```

---

### 2. Create Incident
**POST** `/incidents`

**Headers**: `Authorization: Bearer <token>` (optional - can be anonymous)

**Request Body**:
```json
{
  "title": "string",
  "description": "string",
  "severity": "low | medium | high | critical",
  "asset_id": "string | null",
  "location": {
    "address": "string",
    "coordinates": {
      "longitude": "float",
      "latitude": "float"
    }
  }
}
```

**Response** (201 Created): Incident object

**Data Flow**:
1. Frontend submits incident (can be anonymous)
2. Backend creates incident with status "reported"
3. Backend may trigger alerts/notifications
4. Returns created incident

---

### 3. Get Incident by ID
**GET** `/incidents/{incident_id}`

**Response** (200 OK): Incident object

---

### 4. Update Incident
**PUT** `/incidents/{incident_id}`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**: IncidentUpdate (partial fields)

**Response** (200 OK): Incident object

---

### 5. Acknowledge Incident
**POST** `/incidents/{incident_id}/acknowledge`

**Headers**: `Authorization: Bearer <token>` (required)

**Response** (200 OK): Incident object

---

### 6. Assign Incident
**POST** `/incidents/{incident_id}/assign?assigned_to={user_id}`

**Headers**: `Authorization: Bearer <token>` (required)

**Query Parameters**:
- `assigned_to`: string (required)

**Response** (200 OK): Incident object

---

### 7. Resolve Incident
**POST** `/incidents/{incident_id}/resolve?resolution_notes=string&resolution_type=fixed`

**Headers**: `Authorization: Bearer <token>` (required)

**Query Parameters**:
- `resolution_notes`: string (required)
- `resolution_type`: "fixed" | "duplicate" | "invalid" | "deferred" (required)

**Response** (200 OK): Incident object

---

### 8. Add Comment
**POST** `/incidents/{incident_id}/comments`

**Headers**: `Authorization: Bearer <token>` (optional - can be anonymous)

**Request Body**:
```json
{
  "comment": "string",
  "is_internal": false
}
```

**Response** (200 OK): Incident object

---

### 9. Upvote Incident
**POST** `/incidents/{incident_id}/upvote`

**Headers**: `Authorization: Bearer <token>` (required)

**Response** (200 OK): Incident object

**Note**: Toggle behavior - upvotes if not upvoted, removes upvote if already upvoted

---

### 10. Create Maintenance from Incident
**POST** `/incidents/{incident_id}/create-maintenance`

**Headers**: `Authorization: Bearer <token>` (required)

**Response** (200 OK):
```json
{
  "incident_id": "string",
  "maintenance_id": "string",
  "message": "Maintenance work order created successfully"
}
```

**Data Flow**:
1. Frontend triggers maintenance creation from incident
2. Backend creates maintenance work order linked to incident
3. Returns both IDs

---

## Alerts

**Base Path**: `/api/v1/alerts`

### 1. List Alerts
**GET** `/alerts?skip=0&limit=100&status=active&severity=high&asset_id=xxx`

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100, max: 100)
- `status`: string (optional)
- `severity`: string (optional)
- `asset_id`: string (optional)

**Response** (200 OK): Array of Alert objects

**Alert Object**:
```json
{
  "id": "string",
  "alert_type": "string",
  "severity": "low | medium | high | critical",
  "status": "active | acknowledged | resolved | dismissed",
  "asset_id": "string | null",
  "message": "string",
  "metadata": {},
  "acknowledged_at": "ISO datetime | null",
  "resolved_at": "ISO datetime | null",
  "created_at": "ISO datetime"
}
```

---

### 2. Get Alert by ID
**GET** `/alerts/{alert_id}`

**Response** (200 OK): Alert object

---

### 3. Acknowledge Alert
**POST** `/alerts/{alert_id}/acknowledge`

**Headers**: `Authorization: Bearer <token>` (required)

**Response** (200 OK): Alert object

---

### 4. Resolve Alert
**POST** `/alerts/{alert_id}/resolve`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**:
```json
{
  "resolution_notes": "string"
}
```

**Response** (200 OK): Alert object

---

### 5. Dismiss Alert
**POST** `/alerts/{alert_id}/dismiss`

**Headers**: `Authorization: Bearer <token>` (required)

**Response** (200 OK): Alert object

---

## Budgets

**Base Path**: `/api/v1/budgets`

### 1. List Budgets
**GET** `/budgets?skip=0&limit=100&fiscal_year=2024&status=approved&category=maintenance`

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100, max: 100)
- `fiscal_year`: int (optional)
- `status`: string (optional)
- `category`: string (optional)

**Response** (200 OK): Array of Budget objects

**Budget Object**:
```json
{
  "id": "string",
  "budget_code": "string",
  "fiscal_year": 2024,
  "category": "string",
  "total_amount": 1000000.0,
  "allocated_amount": 500000.0,
  "spent_amount": 200000.0,
  "status": "draft | submitted | approved | rejected",
  "breakdown": {},
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime"
}
```

---

### 2. Create Budget
**POST** `/budgets`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**:
```json
{
  "fiscal_year": 2024,
  "category": "string",
  "total_amount": 1000000.0,
  "breakdown": {}
}
```

**Response** (201 Created): Budget object

---

### 3. Get Budget by ID
**GET** `/budgets/{budget_id}`

**Response** (200 OK): Budget object

---

### 4. Update Budget
**PUT** `/budgets/{budget_id}`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**: BudgetUpdate (partial fields)

**Response** (200 OK): Budget object

---

### 5. Submit Budget for Approval
**POST** `/budgets/{budget_id}/submit`

**Headers**: `Authorization: Bearer <token>` (required)

**Response** (200 OK): Budget object

---

### 6. Approve Budget
**POST** `/budgets/{budget_id}/approve`

**Headers**: `Authorization: Bearer <token>` (required, manager/admin)

**Response** (200 OK): Budget object

---

### 7. List Budget Transactions
**GET** `/budgets/{budget_id}/transactions?skip=0&limit=100`

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100, max: 100)

**Response** (200 OK): Array of BudgetTransaction objects

---

### 8. Create Budget Transaction
**POST** `/budgets/{budget_id}/transactions`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**:
```json
{
  "amount": 5000.0,
  "description": "string",
  "transaction_type": "expense | allocation"
}
```

**Response** (201 Created): BudgetTransaction object

---

### 9. Approve Transaction
**POST** `/budgets/transactions/{transaction_id}/approve`

**Headers**: `Authorization: Bearer <token>` (required)

**Response** (200 OK): BudgetTransaction object

---

## IoT Sensors

**Base Path**: `/api/v1/iot`

### 1. List Sensors
**GET** `/iot/sensors?skip=0&limit=100&asset_id=xxx&sensor_type=temperature&status=active`

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100, max: 100)
- `asset_id`: string (optional)
- `sensor_type`: string (optional)
- `status`: string (optional)

**Response** (200 OK): Array of IoTSensor objects

**IoTSensor Object**:
```json
{
  "id": "string",
  "sensor_code": "string",
  "asset_id": "string",
  "sensor_type": "string",
  "status": "active | inactive | maintenance",
  "location": {
    "longitude": "float",
    "latitude": "float"
  },
  "last_seen": "ISO datetime | null",
  "last_reading": "float | null",
  "created_at": "ISO datetime"
}
```

---

### 2. Register Sensor
**POST** `/iot/sensors`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**:
```json
{
  "sensor_code": "string",
  "asset_id": "string",
  "sensor_type": "string",
  "location": {
    "longitude": "float",
    "latitude": "float"
  }
}
```

**Response** (201 Created): IoTSensor object

---

### 3. Get Sensor by ID
**GET** `/iot/sensors/{sensor_id}`

**Response** (200 OK): IoTSensor object

---

### 4. Update Sensor
**PUT** `/iot/sensors/{sensor_id}`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**: IoTSensorUpdate (partial fields)

**Response** (200 OK): IoTSensor object

---

### 5. Get Sensor Data
**GET** `/iot/sensors/{sensor_id}/data?from_time=2024-01-01T00:00:00Z&to_time=2024-01-31T23:59:59Z&limit=1000`

**Query Parameters**:
- `from_time`: string (ISO datetime, required)
- `to_time`: string (ISO datetime, required)
- `limit`: int (default: 1000, max: 10000)

**Response** (200 OK): Array of SensorReading objects

**SensorReading Object**:
```json
{
  "sensor_id": "string",
  "timestamp": "ISO datetime",
  "value": 25.5,
  "metadata": {}
}
```

---

### 6. Ingest Sensor Reading
**POST** `/iot/sensors/{sensor_id}/data`

**Request Body**:
```json
{
  "timestamp": "ISO datetime (optional)",
  "value": 25.5,
  "metadata": {}
}
```

**Response** (201 Created): SensorReading object

**Note**: Can use API key authentication for IoT devices

---

### 7. Batch Ingest Readings
**POST** `/iot/sensors/batch-ingest`

**Request Body**:
```json
{
  "readings": [
    {
      "sensor_id": "string",
      "timestamp": "ISO datetime",
      "value": 25.5,
      "metadata": {}
    }
  ]
}
```

**Response** (200 OK):
```json
{
  "ingested": 10,
  "failed": 0
}
```

**Note**: Used by MQTT gateway for bulk ingestion

---

### 8. Get Sensor Status
**GET** `/iot/sensors/{sensor_id}/status`

**Response** (200 OK):
```json
{
  "sensor_id": "string",
  "status": "active | inactive | maintenance",
  "last_seen": "ISO datetime | null",
  "last_reading": "float | null"
}
```

---

### 9. Get Sensor Statistics
**GET** `/iot/sensors/{sensor_id}/statistics?from_time=2024-01-01T00:00:00Z&to_time=2024-01-31T23:59:59Z&granularity=hour`

**Query Parameters**:
- `from_time`: string (ISO datetime, required)
- `to_time`: string (ISO datetime, required)
- `granularity`: "minute" | "hour" | "day" (default: "hour")

**Response** (200 OK):
```json
{
  "sensor_id": "string",
  "granularity": "hour",
  "data": [
    {
      "timestamp": "ISO datetime",
      "avg": 25.5,
      "min": 20.0,
      "max": 30.0,
      "count": 60
    }
  ]
}
```

---

## IoT NGSI-LD API

**Base Path**: `/api/v1/ld`

This API provides IoT sensor data in **NGSI-LD format**, which is the ETSI standard for context information management. NGSI-LD enables semantic interoperability for smart city and IoT applications.

### Key Concepts

**NGSI-LD Format**: Each entity has:
- `id`: URN format (e.g., `urn:ngsi-ld:Sensor:sensor-001`)
- `type`: Entity type (e.g., `Sensor`, `Observation`)
- **Properties**: `{"type": "Property", "value": ...}`
- **Relationships**: `{"type": "Relationship", "object": "urn:..."}`
- `@context`: Link to NGSI-LD core context

**Note**: For simple JSON responses, use the standard IoT API at `/api/v1/iot`. NGSI-LD is for semantic web integration and smart city platforms.

### 1. Get NGSI-LD Context
**GET** `/ld/context`

Returns the NGSI-LD context document with vocabulary mappings.

**Response** (200 OK):
```json
{
  "@context": [
    "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld",
    {
      "schema": "https://schema.org/",
      "sensorCode": "schema:identifier",
      ...
    }
  ]
}
```

---

### 2. List Sensors (NGSI-LD)
**GET** `/ld/sensors?skip=0&limit=100&asset_id=xxx&sensor_type=temperature&status=active`

**Query Parameters**: Same as standard IoT API

**Response** (200 OK): Array of NGSI-LD Sensor entities

**NGSI-LD Sensor Example**:
```json
{
  "@context": [...],
  "id": "urn:ngsi-ld:Sensor:sensor-001",
  "type": "Sensor",
  "sensorCode": {
    "type": "Property",
    "value": "TEMP-001"
  },
  "sensorType": {
    "type": "Property",
    "value": "temperature"
  },
  "status": {
    "type": "Property",
    "value": "active"
  },
  "refAsset": {
    "type": "Relationship",
    "object": "urn:ngsi-ld:Asset:asset-123"
  }
}
```

---

### 3. Get Sensor (NGSI-LD)
**GET** `/ld/sensors/{sensor_id}`

Returns a single sensor in NGSI-LD format.

---

### 4. Get Sensor Observations (NGSI-LD)
**GET** `/ld/sensors/{sensor_id}/observations?from_time=2024-01-01T00:00:00Z&to_time=2024-01-31T23:59:59Z&limit=1000`

**Query Parameters**:
- `from_time`: ISO 8601 datetime (required)
- `to_time`: ISO 8601 datetime (required)
- `limit`: int (default: 1000, max: 10000)

**Response** (200 OK): Array of NGSI-LD Observation entities

**NGSI-LD Observation Example**:
```json
{
  "@context": [...],
  "id": "urn:ngsi-ld:Observation:obs-12345",
  "type": "Observation",
  "observedAt": "2024-01-15T10:30:00Z",
  "value": {
    "type": "Property",
    "value": 25.5,
    "unitCode": "°C",
    "observedAt": "2024-01-15T10:30:00Z"
  },
  "refSensor": {
    "type": "Relationship",
    "object": "urn:ngsi-ld:Sensor:sensor-001"
  },
  "refAsset": {
    "type": "Relationship",
    "object": "urn:ngsi-ld:Asset:asset-123"
  }
}
```

---

### 5. List All Observations (NGSI-LD)
**GET** `/ld/observations?hours=1&asset_id=xxx&sensor_type=temperature&limit=500`

**Query Parameters**:
- `hours`: int (default: 1, max: 24) - how far back to retrieve
- `asset_id`: string (optional)
- `sensor_type`: string (optional)
- `limit`: int (default: 500, max: 5000)

Returns recent observations from all sensors in NGSI-LD format.

---

### 6. Get Asset with IoT Data (NGSI-LD)
**GET** `/ld/assets/{asset_id}?hours=24`

Returns an infrastructure asset with associated sensor data in NGSI-LD format.

---

## Notifications

**Base Path**: `/api/v1/notifications`

### 1. List Notifications
**GET** `/notifications?skip=0&limit=100&unread_only=false`

**Headers**: `Authorization: Bearer <token>` (required)

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100, max: 100)
- `unread_only`: boolean (default: false)

**Response** (200 OK): Array of Notification objects

**Notification Object**:
```json
{
  "id": "string",
  "user_id": "string",
  "title": "string",
  "message": "string",
  "type": "alert | maintenance | incident | budget | system",
  "read": false,
  "read_at": "ISO datetime | null",
  "created_at": "ISO datetime",
  "metadata": {}
}
```

**Data Flow**:
1. Frontend requests user notifications
2. Backend filters by user_id from token
3. Returns paginated notifications
4. Frontend displays in notification center

---

### 2. Get Unread Count
**GET** `/notifications/unread-count`

**Headers**: `Authorization: Bearer <token>` (required)

**Response** (200 OK):
```json
{
  "unread_count": 5
}
```

**Usage**: Display badge count in UI

---

### 3. Mark Notification as Read
**POST** `/notifications/{notification_id}/read`

**Headers**: `Authorization: Bearer <token>` (required)

**Response** (200 OK): Notification object

---

### 4. Mark All as Read
**POST** `/notifications/mark-all-read`

**Headers**: `Authorization: Bearer <token>` (required)

**Response** (200 OK):
```json
{
  "message": "All notifications marked as read"
}
```

---

## Reports

**Base Path**: `/api/v1/reports`

### 1. List Reports
**GET** `/reports?skip=0&limit=100&type=maintenance&status=completed`

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100, max: 100)
- `type`: string (optional)
- `status`: string (optional)

**Response** (200 OK): Array of Report objects

**Report Object**:
```json
{
  "id": "string",
  "report_code": "string",
  "type": "maintenance | budget | incident | asset",
  "format": "pdf | excel | csv",
  "status": "pending | generating | completed | failed",
  "parameters": {},
  "file_url": "string | null",
  "created_at": "ISO datetime",
  "completed_at": "ISO datetime | null"
}
```

---

### 2. Create Report
**POST** `/reports`

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**:
```json
{
  "type": "maintenance | budget | incident | asset",
  "format": "pdf | excel | csv",
  "parameters": {}
}
```

**Response** (201 Created): Report object

**Data Flow**:
1. Frontend creates report request
2. Backend queues report generation (Celery)
3. Returns report with status "pending"
4. Frontend polls for completion

---

### 3. Get Report by ID
**GET** `/reports/{report_id}`

**Response** (200 OK): Report object

---

### 4. Generate Report
**POST** `/reports/{report_id}/generate`

**Headers**: `Authorization: Bearer <token>` (required)

**Response** (200 OK): Report object

**Note**: Triggers report generation if not already started

---

### 5. Download Report
**GET** `/reports/{report_id}/download`

**Response** (200 OK):
```json
{
  "file_url": "string",
  "report_code": "string",
  "format": "pdf"
}
```

**Note**: Returns download URL if report is completed

---

## Geospatial

**Base Path**: `/api/v1/geo`

### 1. Find Nearby Assets
**GET** `/geo/assets/nearby?lng=105.8342&lat=21.0278&radius_meters=1000&feature_type=road&limit=100`

**Query Parameters**:
- `lng`: float (required)
- `lat`: float (required)
- `radius_meters`: int (default: 1000, max: 50000)
- `feature_type`: string (optional)
- `limit`: int (default: 100, max: 1000)

**Response** (200 OK): Array of Asset objects

**Data Flow**:
1. Frontend sends user location or map center
2. Backend performs geospatial query (MongoDB $near)
3. Returns assets within radius
4. Frontend displays on map

---

### 2. Find Assets in Bounds
**GET** `/geo/assets/within-bounds?min_lng=105.0&min_lat=20.0&max_lng=106.0&max_lat=22.0&feature_type=road&limit=1000`

**Query Parameters**:
- `min_lng`: float (required)
- `min_lat`: float (required)
- `max_lng`: float (required)
- `max_lat`: float (required)
- `feature_type`: string (optional)
- `limit`: int (default: 1000, max: 10000)

**Response** (200 OK): Array of Asset objects

**Usage**: Load assets for map viewport

---

### 3. Find Assets in Polygon
**POST** `/geo/assets/within-polygon?limit=1000`

**Request Body**:
```json
{
  "coordinates": [[lng, lat], [lng, lat], ...],
  "feature_type": "string (optional)"
}
```

**Response** (200 OK): Array of Asset objects

**Usage**: Custom area selection on map

---

### 4. Geocode Address
**POST** `/geo/geocode`

**Request Body**:
```json
{
  "address": "string",
  "country": "Vietnam (default)"
}
```

**Response** (200 OK):
```json
{
  "coordinates": {
    "longitude": 105.8342,
    "latitude": 21.0278
  },
  "geojson": {
    "type": "Point",
    "coordinates": [105.8342, 21.0278]
  }
}
```

**Usage**: Convert address to coordinates for map

---

### 5. Reverse Geocode
**POST** `/geo/reverse-geocode`

**Request Body**:
```json
{
  "longitude": 105.8342,
  "latitude": 21.0278
}
```

**Response** (200 OK):
```json
{
  "address": "string",
  "city": "string",
  "country": "string"
}
```

**Usage**: Convert coordinates to address

---

### 6. Search Address
**GET** `/geo/search-address?q=Hanoi&limit=5`

**Query Parameters**:
- `q`: string (required)
- `limit`: int (default: 5, max: 20)

**Response** (200 OK): Array of address suggestions

**Usage**: Address autocomplete

---

### 7. Calculate Distance to Asset
**GET** `/geo/assets/{asset_id}/distance-to?lng=105.8342&lat=21.0278`

**Query Parameters**:
- `lng`: float (required)
- `lat`: float (required)

**Response** (200 OK):
```json
{
  "asset_id": "string",
  "distance_meters": 1500.5,
  "distance_km": 1.5
}
```

---

## Public APIs

**Base Path**: `/api/v1/public`

**Note**: These endpoints do not require authentication

### 1. Get Public Asset Info
**GET** `/public/assets/{code}`

**Response** (200 OK):
```json
{
  "asset_code": "string",
  "name": "string",
  "feature_type": "string",
  "category": "string",
  "status": "active",
  "location": {
    "address": "string",
    "coordinates": {
      "longitude": "float",
      "latitude": "float"
    }
  },
  "qr_code": "string"
}
```

**Usage**: QR code/NFC scanning

---

### 2. Create Anonymous Incident
**POST** `/public/incidents`

**Request Body**: Same as `/incidents` POST

**Response** (201 Created): Incident object

**Note**: No authentication required

---

### 3. Get Public Incident
**GET** `/public/incidents/{incident_id}`

**Response** (200 OK): Incident object

**Note**: Only if incident.public_visible is true

---

### 4. Get Asset QR Code
**GET** `/public/assets/{code}/qr-code`

**Response** (200 OK):
```json
{
  "asset_code": "string",
  "qr_code": "string (base64 or URL)",
  "url": "string"
}
```

---

## Data Ingestion

**Base Path**: `/api/v1/ingest`

### 1. Upload CSV
**POST** `/ingest/csv`

**Request**: `multipart/form-data`
- `file`: File (CSV format)

**Response** (200 OK):
```json
{
  "message": "Successfully ingested 150 assets."
}
```

**Data Flow**:
1. Frontend uploads CSV file
2. Backend validates CSV format
3. Backend processes CSV (async via Celery)
4. Returns count of ingested assets

---

## Data Flow Diagrams

### Authentication Flow

```
┌─────────┐                    ┌─────────┐                    ┌─────────┐
│Frontend │                    │ Backend │                    │ MongoDB │
└────┬────┘                    └────┬────┘                    └────┬────┘
     │                              │                              │
     │ POST /auth/login             │                              │
     ├─────────────────────────────>│                              │
     │                              │                              │
     │                              │ Query user by username      │
     │                              ├─────────────────────────────>│
     │                              │                              │
     │                              │<─────────────────────────────┤
     │                              │                              │
     │                              │ Verify password              │
     │                              │ Generate JWT tokens           │
     │                              │                              │
     │<─────────────────────────────┤                              │
     │ {access_token, refresh_token}│                              │
     │                              │                              │
     │ Store tokens in auth store   │                              │
     │                              │                              │
```

### Asset Creation Flow

```
┌─────────┐                    ┌─────────┐                    ┌─────────┐
│Frontend │                    │ Backend │                    │ MongoDB │
└────┬────┘                    └────┬────┘                    └────┬────┘
     │                              │                              │
     │ POST /assets (with token)    │                              │
     ├─────────────────────────────>│                              │
     │                              │                              │
     │                              │ Validate geometry            │
     │                              │ Create asset document        │
     │                              ├─────────────────────────────>│
     │                              │                              │
     │                              │<─────────────────────────────┤
     │                              │                              │
     │                              │ Create audit log             │
     │                              ├─────────────────────────────>│
     │                              │                              │
     │<─────────────────────────────┤                              │
     │ Asset object                 │                              │
     │                              │                              │
     │ Update map/table UI          │                              │
     │                              │                              │
```

### Notification Flow

```
┌─────────┐                    ┌─────────┐                    ┌─────────┐
│ Backend │                    │ MongoDB │                    │Frontend │
│ Service │                    │         │                    │         │
└────┬────┘                    └────┬────┘                    └────┬────┘
     │                              │                              │
     │ Event occurs (e.g., alert)  │                              │
     │                              │                              │
     │ Create notification          │                              │
     ├─────────────────────────────>│                              │
     │                              │                              │
     │                              │                              │
     │                              │                              │
     │                              │                              │ GET /notifications
     │                              │                              │<───────────────────
     │                              │                              │
     │                              │ Query notifications          │
     │                              │<─────────────────────────────┤
     │                              │                              │
     │                              ├─────────────────────────────>│
     │                              │                              │
     │                              │                              │ Display in UI
     │                              │                              │
```

### Report Generation Flow

```
┌─────────┐                    ┌─────────┐                    ┌─────────┐
│Frontend │                    │ Backend │                    │ Celery  │
└────┬────┘                    └────┬────┘                    └────┬────┘
     │                              │                              │
     │ POST /reports                │                              │
     ├─────────────────────────────>│                              │
     │                              │                              │
     │                              │ Create report record         │
     │                              │ Queue generation task        │
     │                              ├─────────────────────────────>│
     │                              │                              │
     │<─────────────────────────────┤                              │
     │ Report (status: pending)     │                              │
     │                              │                              │
     │                              │                              │ Process report
     │                              │                              │ Generate file
     │                              │                              │
     │                              │<─────────────────────────────┤
     │                              │ Update report status         │
     │                              │                              │
     │ GET /reports/{id} (polling)  │                              │
     ├─────────────────────────────>│                              │
     │                              │                              │
     │<─────────────────────────────┤                              │
     │ Report (status: completed)   │                              │
     │                              │                              │
     │ GET /reports/{id}/download   │                              │
     ├─────────────────────────────>│                              │
     │                              │                              │
     │<─────────────────────────────┤                              │
     │ File URL                     │                              │
     │                              │                              │
```

### IoT Sensor Data Flow

```
┌─────────┐                    ┌─────────┐                    ┌─────────┐
│  IoT    │                    │ Backend │                    │ MongoDB │
│ Device  │                    │         │                    │         │
└────┬────┘                    └────┬────┘                    └────┬────┘
     │                              │                              │
     │ POST /iot/sensors/{id}/data  │                              │
     ├─────────────────────────────>│                              │
     │                              │                              │
     │                              │ Validate sensor exists       │
     │                              ├─────────────────────────────>│
     │                              │                              │
     │                              │<─────────────────────────────┤
     │                              │                              │
     │                              │ Store reading                 │
     │                              ├─────────────────────────────>│
     │                              │                              │
     │                              │ Check thresholds              │
     │                              │ Create alert if needed        │
     │                              ├─────────────────────────────>│
     │                              │                              │
     │<─────────────────────────────┤                              │
     │ SensorReading                │                              │
     │                              │                              │
     │                              │                              │
     │                              │                              │ Frontend polls
     │                              │                              │ GET /iot/sensors/{id}/data
     │                              │                              │<───────────────────
     │                              │                              │
     │                              │ Query readings                │
     │                              │<─────────────────────────────┤
     │                              │                              │
     │                              ├─────────────────────────────>│
     │                              │                              │
     │                              │                              │ Display chart
     │                              │                              │
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "detail": "Error message string"
}
```

### HTTP Status Codes

- **200 OK**: Success
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Missing or invalid token
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### Frontend Error Handling

The axios interceptor automatically handles:
- **401**: Logs out user and redirects to login
- **403**: Logs error (can show permission denied message)
- **404**: Logs error (can show not found message)
- **500**: Logs error (can show server error message)

---

## Pagination

Most list endpoints support pagination:

**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100, max varies by endpoint)

**Response Format**:
- Returns array of items directly
- For endpoints with count, response includes `count` field

**Example**:
```
GET /assets?skip=20&limit=10
```

---

## File Uploads

### Supported Endpoints

1. **Asset Photos**: `POST /assets/{id}/photos`
2. **Asset Attachments**: `POST /assets/{id}/attachments`
3. **Maintenance Photos**: `POST /maintenance/{id}/photos`
4. **CSV Import**: `POST /ingest/csv`

### Request Format

```typescript
const formData = new FormData();
formData.append('file', file);

// For multiple files (maintenance photos)
files.forEach(file => {
  formData.append('files', file);
});

await httpClient.post('/assets/{id}/photos', formData, {
  headers: {
    'Content-Type': 'multipart/form-data'
  }
});
```

---

## Real-time Updates

### Polling Strategy

For real-time data, frontend should poll:
- **Notifications**: Every 30-60 seconds
- **Alerts**: Every 10-30 seconds
- **Sensor Data**: Every 5-10 seconds (if displaying live charts)
- **Report Status**: Every 2-5 seconds (when generating)

### WebSocket (Future)

Consider implementing WebSocket for:
- Real-time notifications
- Live sensor data
- Alert updates

---

## Best Practices

1. **Token Management**: Always include token in Authorization header
2. **Error Handling**: Use axios interceptors for consistent error handling
3. **Loading States**: Show loading indicators during API calls
4. **Pagination**: Implement infinite scroll or pagination controls
5. **Caching**: Cache static data (asset types, categories) locally
6. **Optimistic Updates**: Update UI immediately, rollback on error
7. **Debouncing**: Debounce search/autocomplete requests
8. **Request Cancellation**: Cancel pending requests when component unmounts

---

## Environment Variables

### Frontend (.env)

```bash
VITE_BASE_API_URL=http://localhost:8000/api/v1
VITE_LEADERBOARD_URL=https://contribapi.openinfra.space/api
```

---

## Additional Notes

1. **Geospatial Queries**: Use MongoDB geospatial indexes for efficient location-based queries
2. **Audit Logging**: All create/update/delete operations are logged automatically
3. **Soft Deletes**: Assets and users are soft-deleted (status changed, not removed)
4. **Role-Based Access**: Check user role/permissions before showing UI elements
5. **Rate Limiting**: Public endpoints may have rate limiting (not yet implemented)
6. **File Storage**: Files are stored via StorageService (local or S3-compatible)

---

## API Versioning

Current version: **v1**

Base path: `/api/v1`

Future versions will use `/api/v2`, etc.

---

## Support

For API issues or questions:
1. Check FastAPI docs at `/docs` (Swagger UI)
2. Check ReDoc at `/redoc`
3. Review backend router files in `backend/app/api/v1/routers/`
