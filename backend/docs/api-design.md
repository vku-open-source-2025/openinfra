# OpenInfra API Design

## Overview

The OpenInfra API follows RESTful principles with JSON-LD extensions for linked data and MCP (Model Context Protocol) support for AI integration. All APIs are versioned (`/api/v1/`) and documented using OpenAPI 3.0.

**Base URL**: `https://api.openinfra.example.com/api/v1`

**API Standards**:
- RESTful resource-based URLs
- JSON request/response bodies
- JWT bearer token authentication
- Pagination for list endpoints
- Error responses follow RFC 7807 (Problem Details)
- JSON-LD for semantic web integration

---

## Table of Contents

1. [Authentication](#authentication)
2. [Common Patterns](#common-patterns)
3. [Assets API](#assets-api)
4. [Maintenance API](#maintenance-api)
5. [Incidents API](#incidents-api)
6. [IoT Sensors API](#iot-sensors-api)
7. [Budgets API](#budgets-api)
8. [Users API](#users-api)
9. [Notifications API](#notifications-api)
10. [Reports API](#reports-api)
11. [Error Responses](#error-responses)

---

## Authentication

### POST /auth/login
Authenticate user and receive JWT token.

**Request**:
```json
{
  "username": "john.doe",
  "password": "secure_password"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "refresh_token_here",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "username": "john.doe",
    "full_name": "John Doe",
    "role": "technician",
    "permissions": ["view_assets", "create_maintenance"]
  }
}
```

### POST /auth/refresh
Refresh access token using refresh token.

**Request**:
```json
{
  "refresh_token": "refresh_token_here"
}
```

**Response** (200 OK):
```json
{
  "access_token": "new_access_token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST /auth/logout
Invalidate current session.

**Headers**: `Authorization: Bearer {access_token}`

**Response** (204 No Content)

---

## Common Patterns

### Pagination

All list endpoints support pagination using `skip` and `limit` query parameters.

**Request**: `GET /api/v1/assets?skip=0&limit=20`

**Response**:
```json
{
  "data": [...],
  "pagination": {
    "total": 1000,
    "skip": 0,
    "limit": 20,
    "has_more": true
  }
}
```

### Filtering

Use query parameters for filtering:
- `GET /api/v1/assets?status=operational&feature_type=Trạm điện`
- `GET /api/v1/maintenance?assigned_to=507f1f77bcf86cd799439011&status=in_progress`

### Sorting

Use `sort` and `order` query parameters:
- `GET /api/v1/assets?sort=created_at&order=desc`
- `GET /api/v1/incidents?sort=severity&order=asc`

### Field Selection (Sparse Fieldsets)

Select specific fields to reduce payload size:
- `GET /api/v1/assets?fields=id,name,status,geometry`

---

## Assets API

### GET /assets
List all infrastructure assets with filtering and geospatial queries.

**Query Parameters**:
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Results per page (default: 20, max: 100)
- `feature_type` (string): Filter by asset type
- `category` (string): Filter by category
- `status` (string): Filter by status
- `district` (string): Filter by district
- `ward` (string): Filter by ward
- `near_lng` (float): Longitude for nearby search
- `near_lat` (float): Latitude for nearby search
- `radius_meters` (int): Search radius in meters (default: 1000)
- `within_polygon` (geojson): Assets within polygon
- `sort` (string): Sort field (default: created_at)
- `order` (string): asc|desc (default: desc)

**Example Request**:
```
GET /api/v1/assets?feature_type=Trạm điện&status=operational&near_lng=108.254&near_lat=15.974&radius_meters=5000&limit=50
```

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "507f1f77bcf86cd799439011",
      "asset_code": "TDN-001",
      "name": "Trạm điện ABC",
      "feature_type": "Trạm điện",
      "feature_code": "tram_dien",
      "category": "electrical",
      "geometry": {
        "type": "Point",
        "coordinates": [108.2544869, 15.9748467]
      },
      "location": {
        "address": "123 Đường ABC",
        "ward": "Phường 1",
        "district": "Quận Hải Châu",
        "city": "Đà Nẵng"
      },
      "status": "operational",
      "condition": "good",
      "specifications": {
        "capacity": "500kW",
        "manufacturer": "ABB"
      },
      "iot_enabled": true,
      "sensor_count": 3,
      "qr_code": "QR_TDN001",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-11-20T14:25:00Z"
    }
  ],
  "pagination": {
    "total": 150,
    "skip": 0,
    "limit": 50,
    "has_more": true
  }
}
```

### POST /assets
Create a new infrastructure asset.

**Permissions**: `create_asset`

**Request**:
```json
{
  "asset_code": "TDN-002",
  "name": "Trạm điện XYZ",
  "feature_type": "Trạm điện",
  "feature_code": "tram_dien",
  "category": "electrical",
  "geometry": {
    "type": "Point",
    "coordinates": [108.2544869, 15.9748467]
  },
  "location": {
    "address": "456 Đường XYZ",
    "ward": "Phường 2",
    "district": "Quận Hải Châu",
    "city": "Đà Nẵng",
    "country": "Vietnam"
  },
  "specifications": {
    "manufacturer": "ABB",
    "model": "T500",
    "capacity": "500kW",
    "installation_date": "2024-01-15"
  },
  "status": "operational",
  "condition": "excellent",
  "owner": "Sở Công Thương Đà Nẵng",
  "iot_enabled": true,
  "public_info_visible": true,
  "tags": ["critical", "urban"]
}
```

**Response** (201 Created):
```json
{
  "id": "507f1f77bcf86cd799439012",
  "asset_code": "TDN-002",
  "name": "Trạm điện XYZ",
  "qr_code": "QR_TDN002",
  "nfc_tag_id": "NFC_TDN002",
  "created_at": "2024-11-28T10:30:00Z",
  ...
}
```

### GET /assets/{id}
Get detailed asset information.

**Response** (200 OK):
```json
{
  "id": "507f1f77bcf86cd799439011",
  "asset_code": "TDN-001",
  "name": "Trạm điện ABC",
  "feature_type": "Trạm điện",
  "geometry": {...},
  "location": {...},
  "specifications": {...},
  "status": "operational",
  "lifecycle_stage": "operational",
  "maintenance_count": 45,
  "incident_count": 3,
  "sensors": [
    {
      "id": "607f1f77bcf86cd799439021",
      "sensor_code": "SENS-001",
      "sensor_type": "temperature",
      "status": "online",
      "last_reading": {
        "value": 65.5,
        "unit": "°C",
        "timestamp": "2024-11-28T10:25:00Z"
      }
    }
  ],
  "recent_maintenance": [...],
  "active_incidents": [...],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-11-28T09:00:00Z"
}
```

### PUT /assets/{id}
Update asset information.

**Permissions**: `update_asset`

**Request**: Same as POST (all fields optional)

**Response** (200 OK): Updated asset object

### DELETE /assets/{id}
Soft delete asset (sets status to "retired").

**Permissions**: `delete_asset`

**Response** (204 No Content)

### GET /assets/{id}/qr-code
Get QR code image for asset.

**Response** (200 OK):
- Content-Type: `image/png`
- Binary QR code image

### GET /assets/{id}/history
Get asset change history (audit trail).

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "707f1f77bcf86cd799439031",
      "timestamp": "2024-11-28T09:00:00Z",
      "action": "update",
      "user": {
        "id": "507f1f77bcf86cd799439011",
        "full_name": "Admin User"
      },
      "changes": {
        "status": {
          "from": "maintenance",
          "to": "operational"
        }
      }
    }
  ]
}
```

### GET /assets/nearby
Find assets near coordinates (convenience endpoint).

**Query Parameters**:
- `lng` (float, required): Longitude
- `lat` (float, required): Latitude
- `radius_meters` (int): Search radius (default: 1000)
- `feature_type` (string): Filter by type

**Response**: Same as GET /assets

### GET /assets/within-bounds
Find assets within bounding box.

**Query Parameters**:
- `min_lng`, `min_lat`, `max_lng`, `max_lat` (float, required)

**Response**: Same as GET /assets

---

## Maintenance API

### GET /maintenance
List maintenance records.

**Query Parameters**:
- Standard pagination, filtering, sorting
- `asset_id` (string): Filter by asset
- `status` (string): Filter by status
- `assigned_to` (string): Filter by technician
- `priority` (string): Filter by priority
- `type` (string): Filter by maintenance type
- `scheduled_from` (date): Start date range
- `scheduled_to` (date): End date range

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "607f1f77bcf86cd799439021",
      "work_order_number": "WO-2024-001",
      "asset": {
        "id": "507f1f77bcf86cd799439011",
        "name": "Trạm điện ABC",
        "asset_code": "TDN-001"
      },
      "type": "preventive",
      "priority": "medium",
      "status": "in_progress",
      "title": "Quarterly inspection",
      "description": "Routine quarterly maintenance check",
      "scheduled_date": "2024-11-30T08:00:00Z",
      "assigned_to": {
        "id": "507f1f77bcf86cd799439015",
        "full_name": "Technician John"
      },
      "estimated_duration": 120,
      "total_cost": 500000,
      "created_at": "2024-11-20T10:00:00Z"
    }
  ],
  "pagination": {...}
}
```

### POST /maintenance
Create maintenance work order.

**Permissions**: `create_maintenance`

**Request**:
```json
{
  "asset_id": "507f1f77bcf86cd799439011",
  "type": "preventive",
  "priority": "medium",
  "title": "Quarterly inspection",
  "description": "Routine quarterly maintenance check for Trạm điện ABC",
  "scheduled_date": "2024-11-30T08:00:00Z",
  "scheduled_start_time": "2024-11-30T08:00:00Z",
  "scheduled_end_time": "2024-11-30T10:00:00Z",
  "estimated_duration": 120,
  "assigned_to": "507f1f77bcf86cd799439015",
  "budget_id": "707f1f77bcf86cd799439041",
  "parts_needed": [
    {
      "part_name": "Oil filter",
      "quantity": 2,
      "unit_cost": 50000
    }
  ]
}
```

**Response** (201 Created): Full maintenance record

### GET /maintenance/{id}
Get detailed maintenance record.

**Response** (200 OK):
```json
{
  "id": "607f1f77bcf86cd799439021",
  "work_order_number": "WO-2024-001",
  "asset": {...},
  "type": "preventive",
  "priority": "medium",
  "status": "completed",
  "title": "Quarterly inspection",
  "description": "Routine quarterly maintenance check",
  "scheduled_date": "2024-11-30T08:00:00Z",
  "actual_start_time": "2024-11-30T08:15:00Z",
  "actual_end_time": "2024-11-30T10:05:00Z",
  "actual_duration": 110,
  "assigned_to": {...},
  "supervisor": {...},
  "work_performed": "Inspected all components, replaced oil filter, lubricated moving parts",
  "parts_used": [
    {
      "part_name": "Oil filter",
      "part_code": "OF-500",
      "quantity": 2,
      "unit_cost": 50000,
      "total_cost": 100000
    }
  ],
  "labor_cost": 300000,
  "parts_cost": 100000,
  "total_cost": 400000,
  "quality_check": {
    "performed": true,
    "passed": true,
    "checked_by": {...},
    "checked_at": "2024-11-30T10:30:00Z"
  },
  "before_photos": ["https://storage.example.com/before1.jpg"],
  "after_photos": ["https://storage.example.com/after1.jpg"],
  "created_at": "2024-11-20T10:00:00Z",
  "updated_at": "2024-11-30T10:30:00Z",
  "completed_by": {...}
}
```

### PUT /maintenance/{id}
Update maintenance record.

**Permissions**: `update_maintenance`

**Request**: Partial update (any fields from POST)

**Response** (200 OK): Updated maintenance record

### POST /maintenance/{id}/start
Start work on maintenance task.

**Permissions**: `update_maintenance`

**Response** (200 OK):
```json
{
  "id": "607f1f77bcf86cd799439021",
  "status": "in_progress",
  "actual_start_time": "2024-11-30T08:15:00Z"
}
```

### POST /maintenance/{id}/complete
Mark maintenance as completed.

**Permissions**: `update_maintenance`

**Request**:
```json
{
  "work_performed": "Detailed description of work",
  "parts_used": [...],
  "labor_cost": 300000,
  "parts_cost": 100000,
  "notes": "All systems operating normally"
}
```

**Response** (200 OK): Updated maintenance record with status "completed"

### POST /maintenance/{id}/photos
Upload before/after photos.

**Permissions**: `update_maintenance`

**Request**: Multipart form data
- `type`: "before" | "after"
- `file`: Image file

**Response** (200 OK):
```json
{
  "photo_url": "https://storage.example.com/photo.jpg"
}
```

### GET /maintenance/calendar
Get maintenance schedule calendar view.

**Query Parameters**:
- `start_date` (date, required)
- `end_date` (date, required)
- `assigned_to` (string): Filter by technician

**Response** (200 OK):
```json
{
  "data": [
    {
      "date": "2024-11-30",
      "maintenance_count": 5,
      "items": [...]
    }
  ]
}
```

---

## Incidents API

### GET /incidents
List incident reports.

**Query Parameters**:
- Standard pagination, filtering, sorting
- `asset_id` (string): Filter by asset
- `status` (string): Filter by status
- `severity` (string): Filter by severity
- `reporter_type` (string): Filter by reporter type
- `reported_from` (date): Start date range
- `reported_to` (date): End date range

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "707f1f77bcf86cd799439031",
      "incident_number": "INC-2024-001",
      "asset": {
        "id": "507f1f77bcf86cd799439011",
        "name": "Trạm điện ABC"
      },
      "title": "Smoke detected",
      "description": "Unusual smoke coming from transformer",
      "category": "malfunction",
      "severity": "high",
      "status": "investigating",
      "reported_by": {
        "id": "507f1f77bcf86cd799439020",
        "full_name": "Citizen Nguyen Van A",
        "type": "citizen"
      },
      "reported_at": "2024-11-28T09:15:00Z",
      "location": {
        "geometry": {...},
        "address": "123 Đường ABC"
      },
      "photos": ["https://storage.example.com/incident1.jpg"],
      "upvotes": 12,
      "comment_count": 3
    }
  ],
  "pagination": {...}
}
```

### POST /incidents
Report new incident.

**Permissions**: Public endpoint (citizens can report)

**Request**:
```json
{
  "asset_id": "507f1f77bcf86cd799439011",
  "title": "Smoke detected",
  "description": "I noticed unusual smoke coming from the transformer at 9:15 AM",
  "category": "malfunction",
  "severity": "high",
  "location": {
    "geometry": {
      "type": "Point",
      "coordinates": [108.2544869, 15.9748467]
    },
    "address": "123 Đường ABC",
    "description": "Near the bus stop"
  },
  "reporter_contact": {
    "name": "Nguyen Van A",
    "email": "nguyenvana@example.com",
    "phone": "+84901234567"
  }
}
```

**Response** (201 Created): Full incident object with `incident_number`

### GET /incidents/{id}
Get detailed incident information.

**Response** (200 OK):
```json
{
  "id": "707f1f77bcf86cd799439031",
  "incident_number": "INC-2024-001",
  "asset": {...},
  "title": "Smoke detected",
  "description": "Unusual smoke coming from transformer",
  "category": "malfunction",
  "severity": "high",
  "status": "resolved",
  "reported_by": {...},
  "reported_at": "2024-11-28T09:15:00Z",
  "acknowledged_at": "2024-11-28T09:20:00Z",
  "acknowledged_by": {...},
  "assigned_to": {...},
  "resolved_at": "2024-11-28T14:30:00Z",
  "resolved_by": {...},
  "resolution_notes": "Transformer issue resolved, replaced faulty component",
  "resolution_type": "fixed",
  "maintenance_record": {
    "id": "607f1f77bcf86cd799439025",
    "work_order_number": "WO-2024-050"
  },
  "photos": [...],
  "upvotes": 12,
  "comments": [
    {
      "id": "807f1f77bcf86cd799439041",
      "user": {...},
      "comment": "I also noticed this issue yesterday",
      "posted_at": "2024-11-28T09:30:00Z",
      "is_internal": false
    }
  ],
  "response_time_minutes": 5,
  "resolution_time_minutes": 315
}
```

### PUT /incidents/{id}
Update incident (admin/technician only).

**Permissions**: `update_incidents`

**Response** (200 OK): Updated incident

### POST /incidents/{id}/acknowledge
Acknowledge receipt of incident report.

**Permissions**: `assign_incidents`

**Response** (200 OK):
```json
{
  "id": "707f1f77bcf86cd799439031",
  "status": "acknowledged",
  "acknowledged_at": "2024-11-28T09:20:00Z"
}
```

### POST /incidents/{id}/assign
Assign incident to technician.

**Permissions**: `assign_incidents`

**Request**:
```json
{
  "assigned_to": "507f1f77bcf86cd799439015"
}
```

**Response** (200 OK): Updated incident

### POST /incidents/{id}/resolve
Mark incident as resolved.

**Permissions**: `update_incidents`

**Request**:
```json
{
  "resolution_notes": "Issue fixed, replaced component",
  "resolution_type": "fixed",
  "maintenance_record_id": "607f1f77bcf86cd799439025"
}
```

**Response** (200 OK): Updated incident with status "resolved"

### POST /incidents/{id}/upvote
Citizen upvote (support) for incident.

**Permissions**: Authenticated users

**Response** (200 OK):
```json
{
  "upvotes": 13
}
```

### POST /incidents/{id}/comments
Add comment to incident.

**Request**:
```json
{
  "comment": "I also noticed this issue",
  "is_internal": false
}
```

**Response** (201 Created): Comment object

### GET /incidents/public
Public incidents map (for citizen view).

**Query Parameters**:
- Geospatial filtering (nearby, within bounds)
- `status`: Only show "reported", "acknowledged", "investigating"

**Response**: Same as GET /incidents (limited fields)

---

## IoT Sensors API

### GET /iot/sensors
List registered IoT sensors.

**Query Parameters**:
- `asset_id` (string): Filter by asset
- `sensor_type` (string): Filter by type
- `status` (string): Filter by status

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "807f1f77bcf86cd799439051",
      "sensor_code": "SENS-001",
      "asset": {
        "id": "507f1f77bcf86cd799439011",
        "name": "Trạm điện ABC"
      },
      "sensor_type": "temperature",
      "manufacturer": "Siemens",
      "model": "T-100",
      "measurement_unit": "°C",
      "sample_rate": 60,
      "thresholds": {
        "warning_min": 50,
        "warning_max": 80,
        "critical_min": 40,
        "critical_max": 90
      },
      "status": "online",
      "last_seen": "2024-11-28T10:25:00Z",
      "last_reading": {
        "value": 65.5,
        "timestamp": "2024-11-28T10:25:00Z",
        "status": "normal"
      }
    }
  ],
  "pagination": {...}
}
```

### POST /iot/sensors
Register new IoT sensor.

**Permissions**: `manage_iot`

**Request**:
```json
{
  "sensor_code": "SENS-002",
  "asset_id": "507f1f77bcf86cd799439011",
  "sensor_type": "temperature",
  "manufacturer": "Siemens",
  "model": "T-100",
  "measurement_unit": "°C",
  "sample_rate": 60,
  "thresholds": {
    "warning_min": 50,
    "warning_max": 80,
    "critical_min": 40,
    "critical_max": 90
  },
  "connection_type": "wifi",
  "ip_address": "192.168.1.100"
}
```

**Response** (201 Created): Full sensor object

### GET /iot/sensors/{id}
Get sensor details.

**Response** (200 OK): Full sensor object

### PUT /iot/sensors/{id}
Update sensor configuration.

**Permissions**: `manage_iot`

**Response** (200 OK): Updated sensor

### GET /iot/sensors/{id}/data
Get sensor readings (time-series data).

**Query Parameters**:
- `from` (datetime, required): Start time
- `to` (datetime, required): End time
- `granularity` (string): "raw" | "minute" | "hour" | "day" (default: "raw")
- `limit` (int): Max results (default: 1000)

**Response** (200 OK):
```json
{
  "sensor": {...},
  "data": [
    {
      "timestamp": "2024-11-28T10:25:00Z",
      "value": 65.5,
      "unit": "°C",
      "status": "normal",
      "quality": "good"
    }
  ],
  "statistics": {
    "min": 60.2,
    "max": 70.5,
    "avg": 65.3,
    "count": 1440
  }
}
```

### POST /iot/sensors/{id}/data
Ingest sensor reading (IoT device endpoint).

**Authentication**: API Key (not JWT)

**Request**:
```json
{
  "timestamp": "2024-11-28T10:25:00Z",
  "value": 65.5,
  "metadata": {
    "battery_level": 85,
    "signal_strength": -45
  }
}
```

**Response** (201 Created):
```json
{
  "status": "recorded",
  "alert_triggered": false
}
```

### POST /iot/sensors/batch-ingest
Batch ingest multiple sensor readings (MQTT gateway endpoint).

**Authentication**: API Key

**Request**:
```json
{
  "readings": [
    {
      "sensor_id": "807f1f77bcf86cd799439051",
      "timestamp": "2024-11-28T10:25:00Z",
      "value": 65.5
    }
  ]
}
```

**Response** (201 Created):
```json
{
  "processed": 1,
  "alerts_triggered": 0
}
```

---

## Budgets API

### GET /budgets
List budgets.

**Permissions**: `view_budgets`

**Query Parameters**:
- `fiscal_year` (int): Filter by year
- `status` (string): Filter by status
- `category` (string): Filter by category

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "907f1f77bcf86cd799439061",
      "budget_code": "BDG-2024-Q4",
      "name": "Q4 2024 Maintenance Budget",
      "fiscal_year": 2024,
      "category": "maintenance",
      "total_allocated": 500000000,
      "total_spent": 320000000,
      "total_remaining": 180000000,
      "utilization_rate": 64,
      "status": "active",
      "start_date": "2024-10-01",
      "end_date": "2024-12-31"
    }
  ],
  "pagination": {...}
}
```

### POST /budgets
Create new budget.

**Permissions**: `manage_budgets`

**Request**:
```json
{
  "budget_code": "BDG-2024-Q4",
  "name": "Q4 2024 Maintenance Budget",
  "fiscal_year": 2024,
  "period_type": "quarterly",
  "category": "maintenance",
  "start_date": "2024-10-01",
  "end_date": "2024-12-31",
  "total_allocated": 500000000,
  "breakdown": [
    {
      "category": "labor",
      "allocated": 300000000
    },
    {
      "category": "materials",
      "allocated": 200000000
    }
  ]
}
```

**Response** (201 Created): Full budget object

### GET /budgets/{id}
Get budget details.

**Response** (200 OK): Full budget with breakdown and transactions

### POST /budgets/{id}/transactions
Record budget transaction.

**Permissions**: `manage_budgets`

**Request**:
```json
{
  "type": "expense",
  "category": "labor",
  "description": "Maintenance work order WO-2024-001",
  "amount": 400000,
  "maintenance_record_id": "607f1f77bcf86cd799439021",
  "transaction_date": "2024-11-28",
  "invoice_number": "INV-2024-123"
}
```

**Response** (201 Created): Transaction object

### GET /budgets/{id}/reports
Generate budget report.

**Query Parameters**:
- `format` (string): "json" | "pdf" | "excel"

**Response**: Report data or file download

---

## Users API

### GET /users
List users.

**Permissions**: `manage_users`

**Query Parameters**:
- `role` (string): Filter by role
- `status` (string): Filter by status
- `department` (string): Filter by department

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "507f1f77bcf86cd799439015",
      "username": "john.tech",
      "full_name": "John Technician",
      "email": "john@example.com",
      "role": "technician",
      "department": "Maintenance",
      "status": "active",
      "created_at": "2024-01-10T08:00:00Z"
    }
  ],
  "pagination": {...}
}
```

### POST /users
Create new user.

**Permissions**: `manage_users`

**Request**:
```json
{
  "username": "john.tech",
  "email": "john@example.com",
  "password": "secure_password",
  "full_name": "John Technician",
  "role": "technician",
  "department": "Maintenance",
  "phone": "+84901234567",
  "permissions": ["view_assets", "create_maintenance", "update_incidents"]
}
```

**Response** (201 Created): User object (without password)

### GET /users/me
Get current user profile.

**Response** (200 OK): User object with preferences

### PUT /users/me
Update current user profile.

**Request**: Partial update (email, full_name, phone, notification_preferences)

**Response** (200 OK): Updated user object

### PUT /users/me/password
Change current user password.

**Request**:
```json
{
  "current_password": "old_password",
  "new_password": "new_secure_password"
}
```

**Response** (200 OK)

---

## Notifications API

### GET /notifications
List user notifications.

**Query Parameters**:
- `read` (boolean): Filter by read status
- `type` (string): Filter by notification type

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "a07f1f77bcf86cd799439071",
      "type": "maintenance_assigned",
      "title": "New work order assigned",
      "message": "You have been assigned work order WO-2024-001",
      "priority": "medium",
      "read": false,
      "action_url": "/maintenance/607f1f77bcf86cd799439021",
      "action_label": "View Work Order",
      "created_at": "2024-11-28T09:00:00Z"
    }
  ],
  "unread_count": 5,
  "pagination": {...}
}
```

### POST /notifications/{id}/mark-read
Mark notification as read.

**Response** (200 OK)

### POST /notifications/mark-all-read
Mark all notifications as read.

**Response** (200 OK)

---

## Reports API

### GET /reports
List generated reports.

**Permissions**: `view_reports`

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "b07f1f77bcf86cd799439081",
      "report_code": "REP-2024-001",
      "name": "November Maintenance Summary",
      "type": "maintenance_summary",
      "status": "completed",
      "format": "pdf",
      "file_url": "https://storage.example.com/reports/rep-2024-001.pdf",
      "created_at": "2024-11-28T10:00:00Z"
    }
  ]
}
```

### POST /reports
Generate new report.

**Permissions**: `generate_reports`

**Request**:
```json
{
  "type": "maintenance_summary",
  "name": "November Maintenance Summary",
  "parameters": {
    "date_from": "2024-11-01",
    "date_to": "2024-11-30",
    "asset_types": ["Trạm điện", "Đèn đường"]
  },
  "format": "pdf"
}
```

**Response** (202 Accepted):
```json
{
  "id": "b07f1f77bcf86cd799439081",
  "status": "generating",
  "estimated_completion": "2024-11-28T10:05:00Z"
}
```

### GET /reports/{id}/download
Download generated report file.

**Response**: File download (PDF/Excel/CSV)

---

## Error Responses

All errors follow RFC 7807 Problem Details format.

### 400 Bad Request
```json
{
  "type": "https://api.openinfra.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Invalid request parameters",
  "errors": {
    "asset_code": ["Asset code must be unique"],
    "geometry.coordinates": ["Invalid longitude value"]
  }
}
```

### 401 Unauthorized
```json
{
  "type": "https://api.openinfra.example.com/errors/unauthorized",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Missing or invalid authentication token"
}
```

### 403 Forbidden
```json
{
  "type": "https://api.openinfra.example.com/errors/forbidden",
  "title": "Forbidden",
  "status": 403,
  "detail": "Insufficient permissions to perform this action",
  "required_permission": "create_asset"
}
```

### 404 Not Found
```json
{
  "type": "https://api.openinfra.example.com/errors/not-found",
  "title": "Not Found",
  "status": 404,
  "detail": "Asset with ID '507f1f77bcf86cd799439011' not found"
}
```

### 429 Too Many Requests
```json
{
  "type": "https://api.openinfra.example.com/errors/rate-limit",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

### 500 Internal Server Error
```json
{
  "type": "https://api.openinfra.example.com/errors/internal-error",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "An unexpected error occurred. Please contact support.",
  "trace_id": "abc123xyz"
}
```

---

## Rate Limiting

All API endpoints are rate-limited to prevent abuse.

**Limits**:
- **Authenticated users**: 1000 requests/hour
- **Anonymous users**: 100 requests/hour
- **IoT data ingestion**: 10,000 requests/hour (with API key)

**Headers**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1735686000
```

---

## Webhooks (Future)

Webhook support for external integrations (future phase).

**Events**:
- `asset.created`, `asset.updated`, `asset.deleted`
- `maintenance.scheduled`, `maintenance.completed`
- `incident.reported`, `incident.resolved`
- `alert.triggered`

---

## JSON-LD Context

All API responses include JSON-LD context for semantic web integration.

**Example**:
```json
{
  "@context": "https://schema.org",
  "@type": "Place",
  "id": "507f1f77bcf86cd799439011",
  "name": "Trạm điện ABC",
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 15.9748467,
    "longitude": 108.2544869
  }
}
```

---

## Conclusion

This API design provides a comprehensive, RESTful interface for the OpenInfra system with:
- ✅ Clear resource-based URLs
- ✅ Consistent request/response patterns
- ✅ Comprehensive filtering and pagination
- ✅ Geospatial query support
- ✅ Role-based access control
- ✅ Error handling following standards
- ✅ Rate limiting for stability
- ✅ JSON-LD for semantic web integration

**Next**: See `project-plan.md` for phased implementation strategy.
