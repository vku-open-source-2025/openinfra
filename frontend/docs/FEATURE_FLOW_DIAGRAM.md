# Asset Lifecycle Management - Visual Flow Diagrams

## High-Level User Journey

```
┌─────────────┐
│  Dashboard  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Asset List  │ ────► Search/Filter Assets
└──────┬──────┘
       │ Click Asset
       ▼
┌─────────────────┐
│  Asset Detail   │
│  ┌───────────┐  │
│  │  Header   │  │ ────► Health Score, Maintenance Dates
│  └───────────┘  │
│  ┌───────────┐  │
│  │ Quick     │  │ ────► Add Maintenance, Report Incident
│  │ Actions   │  │
│  └───────────┘  │
│  ┌───────────┐  │
│  │   7 Tabs  │  │
│  └───────────┘  │
└─────────────────┘
       │
       ├──► Overview ──────────► Basic Info + Recent Activity
       ├──► Maintenance ───────► Timeline + Approval Workflow
       ├──► Incidents ──────────► Incident List + Details
       ├──► Preventive ─────────► Schedule + Calendar
       ├──► Lifecycle ──────────► Health Score + Factors
       ├──► Documents ──────────► Upload + Manage Files
       └──► Reports ────────────► Generate PDF/Excel
```

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERACTION                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              REACT COMPONENTS (UI Layer)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ AssetList    │  │ AssetDetail  │  │ Tab Components│     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼─────────────────┼──────────────────┼────────────┘
          │                 │                  │
          │                 │                  │
          ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│         TANSTACK QUERY (State Management)                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Query Cache                                       │    │
│  │  - ['assets', 'list'] → Asset[]                   │    │
│  │  - ['asset', id, 'lifecycle'] → Asset              │    │
│  │  - ['maintenance', assetId] → Maintenance[]        │    │
│  │  - ['preventive-maintenance', assetId] → Plan      │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Mutations                                          │    │
│  │  - approveMaintenance()                            │    │
│  │  - uploadDocument()                                │    │
│  │  - generateReport()                                │    │
│  └────────────────────────────────────────────────────┘    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ assetsApi    │  │ maintenance  │  │ preventive   │     │
│  │              │  │ Api          │  │ Maintenance  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼─────────────────┼──────────────────┼────────────┘
          │                 │                  │
          │                 │                  │
          ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│              HTTP CLIENT (Axios)                            │
│  - Adds JWT token to headers                                │
│  - Handles errors                                            │
│  - Transforms requests/responses                             │
└────────────────────┬────────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
┌──────────────────┐   ┌──────────────────┐
│   BACKEND API    │   │   MOCK DATA      │
│   (Production)   │   │   (Development)  │
└──────────────────┘   └──────────────────┘
```

## Maintenance Approval Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    MAINTENANCE LIFECYCLE                     │
└─────────────────────────────────────────────────────────────┘

1. CREATION
   Technician submits maintenance record
   ┌──────────────┐
   │ POST /maintenance │
   │ { asset_id, description, ... } │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Status: "pending" │
   │ Approval: "pending" │
   └──────┬───────┘
          │
          ▼
2. REVIEW
   Admin views in Maintenance History tab
   ┌──────────────┐
   │ Timeline shows │
   │ pending record │
   └──────┬───────┘
          │
          ▼
3. APPROVAL/DECISION
   ┌──────────────┐      ┌──────────────┐
   │   APPROVE    │      │    REJECT    │
   │ POST /approve│      │ POST /reject │
   └──────┬───────┘      └──────┬───────┘
          │                      │
          ▼                      ▼
   ┌──────────────┐      ┌──────────────┐
   │ Status:      │      │ Status:      │
   │ "approved"   │      │ "rejected"    │
   │              │      │ + reason      │
   └──────┬───────┘      └──────┬───────┘
          │                      │
          ▼                      ▼
4. CONSEQUENCES
   ┌─────────────────────────────────────┐
   │ • Update asset.last_maintenance_date│
   │ • Recalculate preventive schedule   │
   │ • Update health score factors       │
   │ • Trigger notifications             │
   └─────────────────────────────────────┘
          │
          ▼
5. UI UPDATE
   ┌──────────────┐
   │ Cache        │
   │ Invalidation │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Timeline      │
   │ Refreshes     │
   └──────────────┘
```

## Preventive Maintenance Cycle

```
┌─────────────────────────────────────────────────────────────┐
│              PREVENTIVE MAINTENANCE CYCLE                   │
└─────────────────────────────────────────────────────────────┘

DAY 0: Plan Created
┌──────────────┐
│ Cycle: 180 days │
│ Next: +180 days│
└──────┬───────┘
       │
       ▼
DAY 173: Warning Window (7 days before)
┌──────────────┐
│ Status: "due_soon" │
│ Notification sent │
└──────┬───────┘
       │
       ▼
DAY 180: Due Date
┌──────────────┐
│ Status: "overdue" │
│ Alert generated │
└──────┬───────┘
       │
       ▼
DAY 185: Maintenance Completed
┌──────────────┐
│ POST /maintenance/{id}/complete │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Backend Updates: │
│ • last_maintenance_date = today │
│ • next_maintenance_date = today + 180 │
│ • Mark task as completed │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ New Cycle Starts │
│ Next due: +180 days │
└──────────────┘
```

## Health Score Calculation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    HEALTH SCORE CALCULATION                 │
└─────────────────────────────────────────────────────────────┘

Data Collection
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Incidents    │  │ Maintenance  │  │ IoT Sensors  │
│ (last 12mo)  │  │ Records      │  │ (if available)│
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       ▼                 ▼                  ▼
Factor Calculation
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Frequency    │  │ Recency      │  │ Alerts       │
│ Factor: 85   │  │ Factor: 80   │  │ Factor: 95   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       └─────────┬───────┴──────────────────┘
                 │
                 ▼
Weighted Calculation
┌─────────────────────────────────────┐
│ Frequency:    85 × 25% = 21.25     │
│ Severity:     90 × 25% = 22.50     │
│ Recency:      80 × 20% = 16.00     │
│ Cost Trend:   75 × 15% = 11.25     │
│ IoT Alerts:   95 × 15% = 14.25     │
│ ─────────────────────────────────── │
│ Total Score:           85/100      │
└─────────────────────────────────────┘
                 │
                 ▼
Color & Label Mapping
┌──────────────┐
│ Score: 85    │
│ Color: Green │
│ Label: Good  │
└──────┬───────┘
       │
       ▼
UI Display
┌──────────────┐
│ Circular     │
│ Gauge: 85/100│
│ Green color  │
└──────────────┘
```

## Document Upload Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCUMENT UPLOAD FLOW                      │
└─────────────────────────────────────────────────────────────┘

1. User Action
┌──────────────┐
│ Select File  │
│ (Drag & Drop)│
└──────┬───────┘
       │
       ▼
2. Validation
┌──────────────┐
│ • File type  │
│ • File size  │
│ • Virus scan │
└──────┬───────┘
       │
       ▼
3. Upload
┌──────────────┐
│ POST /assets/{id}/documents │
│ multipart/form-data         │
│ { file, document_type, is_public } │
└──────┬───────┘
       │
       ▼
4. Backend Processing
┌──────────────┐
│ • Upload to  │
│   Cloud Storage │
│ • Generate URL │
│ • Store metadata │
│ • Version control │
└──────┬───────┘
       │
       ▼
5. Response
┌──────────────┐
│ AssetAttachment │
│ { file_url, ... } │
└──────┬───────┘
       │
       ▼
6. UI Update
┌──────────────┐
│ Document List │
│ Refreshes    │
└──────────────┘
```

## Report Generation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    REPORT GENERATION FLOW                    │
└─────────────────────────────────────────────────────────────┘

User Configuration
┌──────────────┐
│ Report Type: │
│ Maintenance Summary │
│ Format: PDF  │
│ Filters: {...} │
└──────┬───────┘
       │
       ▼
Request
┌──────────────┐
│ POST /assets/{id}/reports │
│ { report_type, format, filters } │
└──────┬───────┘
       │
       ▼
Immediate Response
┌──────────────┐
│ { report_id, status: "processing" } │
└──────┬───────┘
       │
       ▼
Background Processing (Async)
┌──────────────┐
│ 1. Fetch data │
│ 2. Compile report │
│ 3. Generate PDF │
│ 4. Upload to storage │
│ 5. Update status │
└──────┬───────┘
       │
       ▼
Polling/Webhook
┌──────────────┐
│ GET /reports/{id}/status │
└──────┬───────┘
       │
       ▼
Completion
┌──────────────┐
│ { report_url, status: "completed" } │
└──────┬───────┘
       │
       ▼
Download
┌──────────────┐
│ User clicks │
│ Download button │
│ Opens report_url │
└──────────────┘
```

## Cache Invalidation Strategy

```
┌─────────────────────────────────────────────────────────────┐
│              CACHE INVALIDATION FLOW                         │
└─────────────────────────────────────────────────────────────┘

Mutation Occurs
┌──────────────┐
│ approveMaintenance(id) │
└──────┬───────┘
       │
       ▼
Success Callback
┌──────────────┐
│ invalidateQueries([ │
│   'maintenance',    │
│   assetId           │
│ ])                  │
└──────┬───────┘
       │
       ▼
Related Queries Marked Stale
┌──────────────┐
│ ['maintenance', assetId] │
│ ['maintenance', 'history', assetId] │
│ ['asset', assetId, 'lifecycle'] │
└──────┬───────┘
       │
       ▼
Auto Refetch on Next Access
┌──────────────┐
│ Component    │
│ Re-renders   │
│ with fresh   │
│ data         │
└──────────────┘
```

## Key Data Transformations

### Asset ID Handling
```
API Response: { id: "abc123" } or { _id: "abc123" }
       │
       ▼
Component: asset._id || asset.id
       │
       ▼
Navigation: `/admin/assets/${asset._id || asset.id}`
```

### Date Formatting
```
API: "2024-01-15T00:00:00Z"
       │
       ▼
Parse: new Date(dateString)
       │
       ▼
Display: format(date, "dd/MM/yyyy") → "15/01/2024"
```

### Status Mapping
```
API: "under_repair"
       │
       ▼
Display: replace("_", " ") → "under repair"
       │
       ▼
Title Case: "Under Repair"
       │
       ▼
Badge Color: getStatusBadgeColor() → "bg-yellow-100"
```
