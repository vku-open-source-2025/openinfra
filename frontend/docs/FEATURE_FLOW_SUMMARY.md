# Asset Lifecycle & Maintenance History Management - Flow & Data Flow Summary

## Overview

This document describes the complete flow and data flow of the Asset Lifecycle & Maintenance History Management feature, including user interactions, component communication, API calls, and state management.

## Feature Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  AssetList → AssetDetail → [7 Tabs]                            │
│    ↓              ↓                                              │
│  Navigation    Tab Components                                    │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STATE MANAGEMENT LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  TanStack Query (React Query)                                   │
│    - Query Cache                                                │
│    - Mutations                                                  │
│    - Cache Invalidation                                         │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER                                  │
├─────────────────────────────────────────────────────────────────┤
│  assetsApi | maintenanceApi | preventiveMaintenanceApi         │
│    ↓              ↓                    ↓                         │
│  HTTP Client → Backend API (or Mock Data)                       │
└─────────────────────────────────────────────────────────────────┘
```

## 1. Asset List Page Flow

### User Flow
1. User navigates to `/admin/assets`
2. Page loads and displays asset list
3. User can search/filter assets
4. User clicks on an asset → navigates to detail page

### Data Flow
```
User Action: Navigate to /admin/assets
    ↓
AssetList Component mounts
    ↓
useQuery(['assets', 'list', statusFilter])
    ↓
assetsApi.list({ status: statusFilter })
    ↓
HTTP GET /api/v1/assets?status=operational
    ↓
Response: Asset[]
    ↓
TanStack Query caches data
    ↓
Component renders asset cards with:
  - Asset name, type, code
  - Lifecycle status badge
  - Health score indicator
  - Location info
    ↓
User clicks asset card
    ↓
navigate({ to: `/admin/assets/${asset.id}` })
```

## 2. Asset Detail Page Flow

### User Flow
1. User lands on `/admin/assets/{id}`
2. Page loads asset with lifecycle data
3. Header displays key metrics (health score, maintenance dates)
4. User navigates between 7 tabs
5. Each tab loads relevant data

### Data Flow - Initial Load
```
User Action: Navigate to /admin/assets/{id}
    ↓
AssetDetail Component mounts
    ↓
useQuery(['asset', id, 'lifecycle'])
    ↓
assetsApi.getAssetWithLifecycle(id)
    ↓
HTTP GET /api/v1/assets/{id}/lifecycle
    ↓
Response: Asset {
  id, name, feature_type, location,
  lifecycle: {
    lifecycle_status,
    health_score,
    remaining_lifespan_years,
    last_maintenance_date,
    next_maintenance_date
  }
}
    ↓
Component renders:
  - Breadcrumb navigation
  - Asset header with status badge
  - 4 metric cards (Last/Next Maintenance, Health Score, Remaining Life)
  - Quick action buttons
  - Tab navigation (7 tabs)
```

## 3. Tab Component Flows

### 3.1 Overview Tab Flow

```
Tab: Overview
    ↓
AssetOverviewTab Component mounts
    ↓
Parallel Queries:
  ├─ useQuery(['maintenance', assetId, 'recent'])
  │   └─ maintenanceApi.getByAsset(assetId, { limit: 5 })
  │       └─ GET /api/v1/maintenance/asset/{assetId}?limit=5
  │
  └─ useQuery(['incidents', assetId, 'recent'])
      └─ incidentsApi.list({ asset_id: assetId, limit: 5 })
          └─ GET /api/v1/incidents?asset_id={assetId}&limit=5
    ↓
Renders:
  - Basic Information (name, type, managing unit, manufacturer, dates)
  - Status Summary (3 cards: Status, Health Score, Remaining Life)
  - Last 5 Maintenance Records (compact table)
  - Active/Recent Incidents (list with severity indicators)
```

### 3.2 Maintenance History Tab Flow

```
Tab: Maintenance History
    ↓
MaintenanceHistoryTab Component mounts
    ↓
User sets filters (date range, technician, cost)
    ↓
User clicks "Search"
    ↓
setFilters({ date_from, date_to, technician, cost_min, cost_max })
    ↓
useQuery(['maintenance', 'history', assetId, filters])
    ↓
maintenanceApi.getHistory(assetId, filters)
    ↓
GET /api/v1/maintenance/asset/{assetId}/history?
    date_from=2024-01-01&date_to=2024-12-31&technician=John
    ↓
Response: Maintenance[]
    ↓
Renders Timeline View:
  - Vertical timeline with maintenance cards
  - Each card shows: date, status, description, technician, cost, approval status
    ↓
User clicks a maintenance record
    ↓
setSelectedRecord(record)
setShowDetails(true)
    ↓
Dialog opens showing:
  - Full description and notes
  - Parts replaced list
  - Attachments (download links)
  - Approve/Reject buttons (if pending)
    ↓
User clicks "Approve" or "Reject"
    ↓
useMutation → maintenanceApi.approve(id) or reject(id)
    ↓
POST /api/v1/maintenance/{id}/approve or /reject
    ↓
onSuccess: invalidateQueries(['maintenance'])
    ↓
Timeline refreshes with updated approval status
```

### 3.3 Incidents Tab Flow

```
Tab: Incidents
    ↓
AssetIncidentsTab Component mounts
    ↓
User sets filters (status, severity, date range)
    ↓
useQuery(['incidents', assetId, statusFilter, severityFilter])
    ↓
incidentsApi.list({ asset_id: assetId, status, severity })
    ↓
GET /api/v1/incidents?asset_id={assetId}&status=in_progress&severity=high
    ↓
Response: Incident[]
    ↓
Client-side filtering by date range
    ↓
Renders Incident List:
  - Severity color-coded indicators
  - Status badges
  - Incident cards with title, description, reporter, dates
    ↓
User clicks incident card
    ↓
setSelectedIncident(incident)
setShowDetails(true)
    ↓
Dialog opens showing:
  - Full description
  - Status workflow bar (visual progress)
  - Assigned technician
  - Activity log/comments
  - Action buttons (Change Status, Create Maintenance)
```

### 3.4 Preventive Maintenance Tab Flow

```
Tab: Preventive Maintenance
    ↓
PreventiveMaintenanceTab Component mounts
    ↓
Parallel Queries:
  ├─ useQuery(['preventive-maintenance', assetId])
  │   └─ preventiveMaintenanceApi.getPlan(assetId)
  │       └─ GET /api/v1/assets/{assetId}/preventive-maintenance
  │
  ├─ useQuery(['preventive-maintenance', 'tasks', assetId])
  │   └─ preventiveMaintenanceApi.getUpcomingTasks(assetId)
  │       └─ GET /api/v1/assets/{assetId}/preventive-maintenance/tasks
  │
  └─ useQuery(['preventive-maintenance', 'overdue', assetId])
      └─ preventiveMaintenanceApi.getOverdueTasks(assetId)
          └─ GET /api/v1/assets/{assetId}/preventive-maintenance/overdue
    ↓
Renders:
  - Current Plan Summary (cycle, dates, responsible team)
  - Upcoming Tasks (with due soon/overdue highlighting)
  - Overdue Tasks (red alert section)
  - Calendar View (visual schedule)
    ↓
User clicks "Edit Plan"
    ↓
setShowEditModal(true)
    ↓
Modal opens with form:
  - Cycle days input
  - Cycle description
  - Warning days
  - Responsible team
    ↓
User updates and clicks "Save"
    ↓
useMutation → preventiveMaintenanceApi.updatePlan(planId, data)
    ↓
PUT /api/v1/preventive-maintenance/{planId}
    ↓
onSuccess: invalidateQueries(['preventive-maintenance', assetId])
    ↓
Plan summary and tasks refresh
```

### 3.5 Lifecycle & Condition Tab Flow

```
Tab: Lifecycle & Condition
    ↓
LifecycleConditionTab Component mounts
    ↓
useQuery(['asset', 'health-score', assetId])
    ↓
assetsApi.getHealthScore(assetId)
    ↓
GET /api/v1/assets/{assetId}/health-score
    ↓
Response: {
  health_score: 87,
  factors: {
    incident_frequency: 85,
    incident_severity: 90,
    maintenance_recency: 80,
    maintenance_cost_trend: 75,
    iot_sensor_alerts: 95
  }
}
    ↓
Renders:
  - Health Score Gauge (circular visualization)
  - Remaining Lifespan Bar (percentage visualization)
  - Current Age vs Designed Lifespan Chart
  - Factors Affecting Condition (list with progress bars)
  - Health Score Trend Graph (placeholder for chart)
```

### 3.6 Documents Tab Flow

```
Tab: Documents
    ↓
AssetDocumentsTab Component mounts
    ↓
useQuery(['asset', 'documents', assetId])
    ↓
assetsApi.getDocuments(assetId)
    ↓
GET /api/v1/assets/{assetId}/documents
    ↓
Response: AssetAttachment[]
    ↓
Renders Document Table:
  - Type icon, name, version, uploaded by, date
  - Actions: Preview, Download, Delete
    ↓
User clicks "Upload Document"
    ↓
DocumentUpload Component:
  - Drag & drop area
  - File selection
  - Document type input
  - Public/private checkbox
    ↓
User selects file and clicks "Upload"
    ↓
useMutation → assetsApi.uploadDocument(assetId, file, type, isPublic)
    ↓
POST /api/v1/assets/{assetId}/documents
  Content-Type: multipart/form-data
  Body: { file, document_type, is_public }
    ↓
onSuccess: invalidateQueries(['asset', 'documents', assetId])
    ↓
Document list refreshes
    ↓
User clicks "Preview" or "Download"
    ↓
Opens document in new tab or downloads file
```

### 3.7 Reports Tab Flow

```
Tab: Reports
    ↓
AssetReportsTab Component mounts
    ↓
User selects:
  - Report Type (Maintenance Summary, Incident Summary, etc.)
  - Filters (if Custom Report)
  - Output Format (PDF/Excel)
    ↓
User clicks "Generate Report"
    ↓
useMutation → assetsApi.generateReport(assetId, reportType, format, filters)
    ↓
POST /api/v1/assets/{assetId}/reports
  Body: {
    report_type: "maintenance_summary",
    format: "pdf",
    filters: { date_from, date_to, severity, cost_min, cost_max }
  }
    ↓
Response: { report_url: "...", report_id: "..." }
    ↓
Renders Success Message with Download Button
    ↓
User clicks "Download PDF/Excel"
    ↓
Opens report URL in new tab (downloads file)
```

## 4. Quick Actions Flow

### Add Maintenance Record
```
User clicks "Add Maintenance Record" button
    ↓
Navigate to maintenance create page (TODO: implement route)
    ↓
Pre-fill asset_id in form
    ↓
User fills form and submits
    ↓
POST /api/v1/maintenance
    ↓
onSuccess: invalidateQueries(['maintenance', assetId])
    ↓
Navigate back to asset detail page
    ↓
Maintenance History tab shows new record
```

### Report Incident
```
User clicks "Report Incident" button
    ↓
Navigate to /admin/incidents/create?asset_id={id}
    ↓
Incident form pre-filled with asset_id
    ↓
User fills form and submits
    ↓
POST /api/v1/incidents
    ↓
onSuccess: invalidateQueries(['incidents', assetId])
    ↓
Navigate back to asset detail page
    ↓
Incidents tab shows new incident
```

### Edit Asset
```
User clicks "Edit Asset" button
    ↓
Navigate to asset edit page (TODO: implement route)
    ↓
Form pre-filled with current asset data
    ↓
User updates fields and submits
    ↓
PUT /api/v1/assets/{id}
    ↓
onSuccess: invalidateQueries(['asset', id, 'lifecycle'])
    ↓
Navigate back to asset detail page
    ↓
Page refreshes with updated data
```

## 5. Health Score Calculation Flow

### Backend Calculation (Recommended)
```
Health Score Request
    ↓
GET /api/v1/assets/{id}/health-score
    ↓
Backend Service:
  1. Fetch incident data (last 12 months)
  2. Calculate incident frequency factor (0-100)
  3. Calculate incident severity factor (weighted average)
  4. Fetch maintenance records
  5. Calculate maintenance recency factor (days since last)
  6. Calculate maintenance cost trend factor
  7. Fetch IoT sensor alerts (if available)
  8. Calculate IoT factor
  9. Apply weights and calculate final score
    ↓
Response: { health_score: 87, factors: {...} }
    ↓
Frontend displays gauge and factors
```

### Frontend Calculation (Fallback/Mock)
```
Frontend receives factors from API
    ↓
calculateHealthScore(factors) utility function
    ↓
Weights applied:
  - Incident frequency: 25%
  - Incident severity: 25%
  - Maintenance recency: 20%
  - Cost trend: 15%
  - IoT alerts: 15%
    ↓
Score calculated: 0-100
    ↓
getHealthScoreColor(score) → "green" | "yellow" | "orange" | "red"
    ↓
getHealthScoreLabel(score) → "Excellent" | "Good" | "Fair" | "Poor" | "Critical"
    ↓
Component renders with color-coded display
```

## 6. Preventive Maintenance Scheduling Flow

### Plan Creation/Update
```
User creates/updates preventive maintenance plan
    ↓
POST /api/v1/preventive-maintenance or PUT /api/v1/preventive-maintenance/{id}
    ↓
Backend:
  1. Validate cycle_days > 0
  2. Calculate next_maintenance_date:
     - If last_maintenance_date exists:
       next = last + cycle_days
     - Else:
       next = today + cycle_days
  3. Store plan in database
  4. Generate initial tasks
    ↓
Response: PreventiveMaintenancePlan
    ↓
Frontend refreshes plan display
```

### Task Generation Flow
```
Scheduled Job (Backend - Daily at midnight)
    ↓
For each active preventive maintenance plan:
  1. Check if next_maintenance_date <= today
     - If yes: Create overdue task
  2. Check if next_maintenance_date <= today + warning_days
     - If yes: Create "due soon" task
  3. Generate future tasks (next 3 cycles)
    ↓
Tasks stored in database
    ↓
Frontend queries tasks:
  - GET /api/v1/assets/{id}/preventive-maintenance/tasks (upcoming)
  - GET /api/v1/assets/{id}/preventive-maintenance/overdue (overdue)
    ↓
Tasks displayed with status indicators
```

### Maintenance Completion Flow
```
Technician completes maintenance
    ↓
POST /api/v1/maintenance/{id}/complete
    ↓
Backend:
  1. Update maintenance record status to "completed"
  2. Update asset.last_maintenance_date
  3. Find preventive maintenance plan for asset
  4. Recalculate next_maintenance_date:
     next = completed_date + cycle_days
  5. Update plan.last_maintenance_date
  6. Update plan.next_maintenance_date
  7. Mark related tasks as completed
    ↓
Response: Updated Maintenance and Plan
    ↓
Frontend invalidates queries:
  - ['maintenance', assetId]
  - ['preventive-maintenance', assetId]
  - ['asset', assetId, 'lifecycle']
    ↓
All tabs refresh with updated data
```

## 7. Maintenance Approval Workflow Flow

```
Technician submits maintenance record
    ↓
POST /api/v1/maintenance
  Body: { asset_id, title, description, ... }
    ↓
Backend creates record with approval_status: "pending"
    ↓
Response: Maintenance { approval_status: "pending" }
    ↓
Admin views Maintenance History tab
    ↓
Sees pending records with "Approve/Reject" buttons
    ↓
Admin clicks "Approve"
    ↓
POST /api/v1/maintenance/{id}/approve
  Body: { approval_status: "approved" }
    ↓
Backend:
  1. Update approval_status to "approved"
  2. Update asset.last_maintenance_date
  3. Recalculate preventive maintenance next date
  4. Update health score factors
  5. Trigger notifications (if configured)
    ↓
Response: Updated Maintenance
    ↓
Frontend invalidates queries
    ↓
Timeline refreshes showing approved status
```

## 8. Document Management Flow

### Upload Flow
```
User selects file in Documents tab
    ↓
DocumentUpload component:
  - Validates file type
  - Shows file preview
  - User sets document type and public/private
    ↓
User clicks "Upload"
    ↓
POST /api/v1/assets/{id}/documents
  Content-Type: multipart/form-data
  Body: FormData { file, document_type, is_public }
    ↓
Backend:
  1. Validate file (size, type, virus scan)
  2. Upload to cloud storage (S3/GCS)
  3. Generate file URL
  4. Store metadata in database:
     - file_name, file_url, file_type
     - uploaded_by (from JWT token)
     - uploaded_at (timestamp)
     - version (1 for new, increment for updates)
     - is_public flag
  5. If version update: Archive previous version
    ↓
Response: AssetAttachment
    ↓
Frontend adds to document list
```

### Access Control Flow
```
User requests document
    ↓
Check user role:
  - Admin: Full access (view, download, delete)
  - Technician: View + upload (restricted types)
  - Public (via QR/NFC): Only is_public=true documents
    ↓
GET /api/v1/assets/{id}/documents
    ↓
Backend filters documents by:
  - User role
  - is_public flag
    ↓
Response: Filtered AssetAttachment[]
    ↓
Frontend displays accessible documents
```

## 9. Report Generation Flow

```
User configures report in Reports tab
    ↓
User clicks "Generate Report"
    ↓
POST /api/v1/assets/{id}/reports
  Body: {
    report_type: "maintenance_summary",
    format: "pdf",
    filters: {...}
  }
    ↓
Backend (Async Processing):
  1. Validate report type and filters
  2. Queue background job (Celery)
  3. Return immediately: { report_id, status: "processing" }
    ↓
Background Worker:
  1. Fetch data based on report_type and filters
  2. Compile data into report structure
  3. Generate PDF/Excel file
  4. Upload to cloud storage
  5. Update report status: "completed"
  6. Send notification (optional)
    ↓
Frontend polls or receives webhook:
  GET /api/v1/reports/{report_id}/status
    ↓
When status = "completed":
  Response: { report_url: "https://...", status: "completed" }
    ↓
Frontend shows download button
    ↓
User clicks download
    ↓
Opens report_url in new tab
```

## 10. State Management & Cache Flow

### Query Cache Structure
```
TanStack Query Cache:
  ├─ ['assets', 'list', statusFilter] → Asset[]
  ├─ ['asset', id, 'lifecycle'] → Asset
  ├─ ['asset', 'health-score', id] → HealthScoreData
  ├─ ['asset', 'documents', id] → AssetAttachment[]
  ├─ ['maintenance', assetId] → Maintenance[]
  ├─ ['maintenance', 'history', assetId, filters] → Maintenance[]
  ├─ ['preventive-maintenance', assetId] → PreventiveMaintenancePlan
  ├─ ['preventive-maintenance', 'tasks', assetId] → PreventiveMaintenanceTask[]
  ├─ ['preventive-maintenance', 'overdue', assetId] → PreventiveMaintenanceTask[]
  └─ ['incidents', assetId, status, severity] → Incident[]
```

### Cache Invalidation Flow
```
User action triggers mutation
    ↓
Mutation succeeds
    ↓
onSuccess callback:
  queryClient.invalidateQueries(['maintenance', assetId])
    ↓
TanStack Query:
  1. Marks queries as stale
  2. Refetches on next component mount
  3. Updates UI with fresh data
    ↓
Components automatically re-render with new data
```

## 11. Error Handling Flow

```
API Request fails
    ↓
HTTP Error Response (4xx/5xx)
    ↓
httpClient interceptor catches error
    ↓
Error thrown to component
    ↓
TanStack Query:
  - Sets error state
  - Retries based on retry policy
    ↓
Component displays error UI:
  - Error message
  - Retry button
  - Fallback content
    ↓
User clicks retry
    ↓
Query refetches
```

## 12. Mock Data Flow (Development)

```
Component requests data
    ↓
API function checks USE_MOCK_DATA flag
    ↓
If true:
  - Call mock function
  - Simulate delay (300-500ms)
  - Return mock data
    ↓
If false:
  - Make real HTTP request
  - Return API response
    ↓
Component receives data (same interface)
    ↓
Renders normally
```

## Key Data Transformations

### Asset ID Mapping
- Frontend uses `asset.id` (from new API)
- Legacy code may use `asset._id` (from old API)
- Components handle both: `asset._id || asset.id`

### Date Formatting
- API returns ISO 8601 strings: `"2024-01-15T00:00:00Z"`
- Frontend displays: `"15/01/2024"` using `date-fns` format()
- Calculations use Date objects

### Status Mapping
- API: `"under_repair"` (snake_case)
- Display: `"Under Repair"` (title case with space)
- Badge colors mapped via `getStatusBadgeColor()`

## Performance Optimizations

1. **Lazy Loading**: Tab components loaded on demand
2. **Query Caching**: TanStack Query caches responses
3. **Parallel Queries**: Multiple queries run simultaneously
4. **Filtered Queries**: Only fetch needed data
5. **Debounced Search**: Search input debounced to reduce API calls
6. **Pagination**: Large lists paginated server-side

## Security Considerations

1. **Authentication**: All API calls include JWT token
2. **Authorization**: Backend validates user permissions
3. **File Upload**: File type and size validation
4. **XSS Prevention**: React escapes content automatically
5. **CSRF Protection**: Token-based requests
