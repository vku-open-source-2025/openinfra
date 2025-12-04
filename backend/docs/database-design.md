# OpenInfra Database Design

## Executive Summary

This document outlines the comprehensive database design for the OpenInfra Urban Infrastructure Asset Management System. After careful analysis of the requirements and current implementation, we recommend **MongoDB with geospatial indexing** as the primary database, with considerations for future PostgreSQL + PostGIS migration if relational integrity becomes critical.

## Database Technology Assessment

### MongoDB vs PostgreSQL + PostGIS

| Criteria | MongoDB | PostgreSQL + PostGIS | Recommendation |
|----------|---------|---------------------|----------------|
| **Geospatial Support** | ✅ Good (2dsphere indexes) | ✅ Excellent (PostGIS) | MongoDB sufficient for current needs |
| **Schema Flexibility** | ✅ Excellent (schemaless) | ⚠️ Rigid (schema required) | MongoDB better for evolving requirements |
| **IoT Time-Series** | ✅ Native time-series collections | ⚠️ Requires TimescaleDB | MongoDB advantage |
| **Joins & Relations** | ⚠️ Limited (lookup) | ✅ Excellent (native JOINs) | PostgreSQL advantage |
| **Horizontal Scaling** | ✅ Native sharding | ⚠️ Complex (Citus extension) | MongoDB advantage |
| **Transaction Support** | ✅ ACID (4.0+) | ✅ ACID | Equal |
| **Current Team Expertise** | ✅ Already implemented | ❌ Not started | MongoDB advantage |

**Decision: Continue with MongoDB** for the following reasons:
1. Already implemented with working geospatial queries
2. Better fit for IoT time-series data
3. Schema flexibility for evolving asset attributes
4. Excellent horizontal scaling for city-wide deployment
5. Native support for hierarchical/nested data

**Migration Path**: If relational integrity becomes critical (complex budget tracking, deep referential integrity), we can migrate specific collections to PostgreSQL in a hybrid architecture.

## Database Collections Schema

### 1. users
**Purpose**: User authentication, authorization, and profile management

```javascript
{
  _id: ObjectId,
  username: String,              // Unique username
  email: String,                 // Unique email
  password_hash: String,         // Bcrypt hashed password
  full_name: String,             // Display name
  phone: String?,                // Optional phone number
  role: String,                  // "admin" | "technician" | "citizen"
  permissions: [String],         // ["view_assets", "edit_assets", "manage_users", ...]
  department: String?,           // For admin/technician
  avatar_url: String?,           // Profile picture URL
  status: String,                // "active" | "inactive" | "suspended"
  language: String,              // "vi" | "en" (default: "vi")
  notification_preferences: {
    email: Boolean,
    push: Boolean,
    sms: Boolean
  },
  last_login: Date?,
  created_at: Date,
  updated_at: Date,
  created_by: ObjectId?,         // Reference to users._id
  metadata: Object               // Additional custom fields
}
```

**Indexes**:
```javascript
db.users.createIndex({ "username": 1 }, { unique: true })
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "role": 1 })
db.users.createIndex({ "status": 1 })
db.users.createIndex({ "created_at": -1 })
```

---

### 2. assets
**Purpose**: Infrastructure asset registry with geospatial data

```javascript
{
  _id: ObjectId,
  asset_code: String,            // Unique identifier (e.g., "TDN-001")
  name: String,                  // Asset name
  feature_type: String,          // "Trạm điện", "Trạm sạc", "Đèn đường", etc.
  feature_code: String,          // Internal code category
  category: String,              // Grouping: "electrical", "transportation", "lighting"

  // Geospatial Data
  geometry: {
    type: String,                // "Point" | "LineString" | "Polygon"
    coordinates: [Number]        // [longitude, latitude] or array of coordinates
  },
  location: {
    address: String,             // Full address
    ward: String,                // Phường/Xã
    district: String,            // Quận/Huyện
    city: String,                // Thành phố
    country: String              // Default: "Vietnam"
  },

  // Asset Details
  specifications: {
    manufacturer: String?,
    model: String?,
    serial_number: String?,
    installation_date: Date?,
    warranty_expiry: Date?,
    capacity: String?,           // e.g., "500kW", "100L"
    dimensions: String?,         // e.g., "2m x 3m x 1.5m"
    weight: String?,
    material: String?,
    custom_fields: Object        // Flexible schema for asset-specific attributes
  },

  // Lifecycle
  status: String,                // "operational" | "maintenance" | "damaged" | "retired"
  condition: String,             // "excellent" | "good" | "fair" | "poor"
  lifecycle_stage: String,       // "planning" | "construction" | "operational" | "decommissioned"
  installation_cost: Number?,
  current_value: Number?,        // Depreciated value
  depreciation_rate: Number?,    // Annual depreciation %

  // Ownership & Management
  owner: String,                 // Organization/department
  manager_id: ObjectId?,         // Reference to users._id
  vendor_id: ObjectId?,          // Reference to vendors collection (future)

  // QR/NFC Integration
  qr_code: String?,              // QR code data
  nfc_tag_id: String?,           // NFC tag identifier
  public_info_visible: Boolean,  // Show to citizens via QR/NFC

  // IoT Integration
  iot_enabled: Boolean,
  sensor_ids: [ObjectId],        // References to iot_sensors._id

  // Metadata
  tags: [String],                // ["critical", "high-priority", "renovation-2024"]
  notes: String?,
  attachments: [{
    file_name: String,
    file_url: String,
    file_type: String,
    uploaded_at: Date,
    uploaded_by: ObjectId
  }],

  created_at: Date,
  updated_at: Date,
  created_by: ObjectId,          // Reference to users._id
  updated_by: ObjectId
}
```

**Indexes**:
```javascript
// Geospatial index (critical for map queries)
db.assets.createIndex({ "geometry": "2dsphere" })

// Performance indexes
db.assets.createIndex({ "asset_code": 1 }, { unique: true })
db.assets.createIndex({ "feature_type": 1 })
db.assets.createIndex({ "category": 1 })
db.assets.createIndex({ "status": 1 })
db.assets.createIndex({ "location.district": 1, "location.ward": 1 })
db.assets.createIndex({ "qr_code": 1 }, { sparse: true })
db.assets.createIndex({ "nfc_tag_id": 1 }, { sparse: true })
db.assets.createIndex({ "created_at": -1 })

// Compound indexes for common queries
db.assets.createIndex({ "status": 1, "feature_type": 1 })
db.assets.createIndex({ "category": 1, "status": 1 })
```

---

### 3. maintenance_records
**Purpose**: Maintenance history, work orders, and scheduled maintenance

```javascript
{
  _id: ObjectId,
  work_order_number: String,     // Unique work order ID (e.g., "WO-2024-001")
  asset_id: ObjectId,            // Reference to assets._id

  // Work Order Details
  type: String,                  // "preventive" | "corrective" | "predictive" | "emergency"
  priority: String,              // "low" | "medium" | "high" | "critical"
  title: String,                 // Brief description
  description: String,           // Detailed work description

  // Scheduling
  status: String,                // "scheduled" | "in_progress" | "completed" | "cancelled" | "on_hold"
  scheduled_date: Date,
  scheduled_start_time: Date?,
  scheduled_end_time: Date?,
  actual_start_time: Date?,
  actual_end_time: Date?,
  estimated_duration: Number,    // in minutes
  actual_duration: Number?,      // in minutes

  // Assignment
  assigned_to: ObjectId?,        // Reference to users._id (technician)
  assigned_team: [ObjectId],     // Multiple technicians
  supervisor_id: ObjectId?,      // Reference to users._id

  // Execution Details
  work_performed: String?,       // What was actually done
  parts_used: [{
    part_name: String,
    part_code: String?,
    quantity: Number,
    unit_cost: Number?,
    total_cost: Number?
  }],
  tools_used: [String],

  // Financial
  labor_cost: Number?,
  parts_cost: Number?,
  other_costs: Number?,
  total_cost: Number,
  budget_id: ObjectId?,          // Reference to budgets._id

  // Quality & Safety
  quality_check: {
    performed: Boolean,
    passed: Boolean?,
    checked_by: ObjectId?,
    checked_at: Date?,
    notes: String?
  },
  safety_incidents: [{
    description: String,
    severity: String,
    reported_at: Date,
    reported_by: ObjectId
  }],

  // Documentation
  before_photos: [String],       // URLs
  after_photos: [String],        // URLs
  attachments: [{
    file_name: String,
    file_url: String,
    file_type: String,
    uploaded_at: Date
  }],

  // Follow-up
  follow_up_required: Boolean,
  follow_up_date: Date?,
  follow_up_notes: String?,
  recurring: Boolean,            // Is this recurring maintenance?
  recurrence_pattern: String?,   // "daily" | "weekly" | "monthly" | "yearly" | "custom"
  next_maintenance_date: Date?,

  // Tracking
  created_at: Date,
  updated_at: Date,
  created_by: ObjectId,
  completed_by: ObjectId?,
  cancelled_by: ObjectId?,
  cancellation_reason: String?,

  // Analytics
  downtime_minutes: Number?,     // Asset downtime caused
  impact_assessment: String?     // Impact on operations
}
```

**Indexes**:
```javascript
db.maintenance_records.createIndex({ "work_order_number": 1 }, { unique: true })
db.maintenance_records.createIndex({ "asset_id": 1 })
db.maintenance_records.createIndex({ "status": 1 })
db.maintenance_records.createIndex({ "assigned_to": 1 })
db.maintenance_records.createIndex({ "scheduled_date": 1 })
db.maintenance_records.createIndex({ "created_at": -1 })

// Compound indexes
db.maintenance_records.createIndex({ "asset_id": 1, "status": 1 })
db.maintenance_records.createIndex({ "status": 1, "priority": 1, "scheduled_date": 1 })
db.maintenance_records.createIndex({ "assigned_to": 1, "status": 1 })
```

---

### 4. incidents
**Purpose**: Issue tracking, citizen reports, and incident management

```javascript
{
  _id: ObjectId,
  incident_number: String,       // Unique identifier (e.g., "INC-2024-001")
  asset_id: ObjectId?,           // Reference to assets._id (may be null for general issues)

  // Incident Details
  title: String,
  description: String,
  category: String,              // "damage" | "malfunction" | "safety_hazard" | "vandalism" | "other"
  severity: String,              // "low" | "medium" | "high" | "critical"
  status: String,                // "reported" | "acknowledged" | "investigating" | "resolved" | "closed"

  // Location (if not asset-specific)
  location: {
    geometry: {
      type: String,              // "Point"
      coordinates: [Number]
    },
    address: String?,
    description: String?         // "Near the bus stop on Main Street"
  },

  // Reporter Information
  reported_by: ObjectId?,        // Reference to users._id (null for anonymous)
  reporter_type: String,         // "citizen" | "technician" | "admin" | "system"
  reporter_contact: {
    name: String?,
    email: String?,
    phone: String?
  },
  reported_via: String,          // "web" | "mobile" | "qr_code" | "phone" | "system"
  reported_at: Date,

  // Assignment & Resolution
  assigned_to: ObjectId?,        // Reference to users._id
  acknowledged_at: Date?,
  acknowledged_by: ObjectId?,
  resolved_at: Date?,
  resolved_by: ObjectId?,
  resolution_notes: String?,
  resolution_type: String?,      // "fixed" | "duplicate" | "not_an_issue" | "transferred"

  // Linked Records
  maintenance_record_id: ObjectId?,  // Created maintenance work order
  related_incidents: [ObjectId],     // Related incident reports

  // Media & Evidence
  photos: [String],              // URLs
  videos: [String],              // URLs
  attachments: [{
    file_name: String,
    file_url: String,
    file_type: String,
    uploaded_at: Date
  }],

  // Citizen Engagement
  public_visible: Boolean,       // Show to public
  upvotes: Number,               // Citizen support count
  upvoted_by: [ObjectId],        // Users who upvoted
  comments: [{
    user_id: ObjectId?,
    comment: String,
    posted_at: Date,
    is_internal: Boolean         // Internal staff notes vs public comments
  }],

  // Notifications
  notifications_sent: [{
    recipient_id: ObjectId,
    sent_at: Date,
    method: String,              // "email" | "push" | "sms"
    status: String               // "sent" | "delivered" | "failed"
  }],

  // Tracking
  created_at: Date,
  updated_at: Date,
  closed_at: Date?,

  // Analytics
  response_time_minutes: Number?, // Time to first response
  resolution_time_minutes: Number?, // Time to resolution
  citizen_satisfaction: Number?   // 1-5 rating
}
```

**Indexes**:
```javascript
db.incidents.createIndex({ "incident_number": 1 }, { unique: true })
db.incidents.createIndex({ "asset_id": 1 })
db.incidents.createIndex({ "status": 1 })
db.incidents.createIndex({ "severity": 1 })
db.incidents.createIndex({ "reported_by": 1 })
db.incidents.createIndex({ "assigned_to": 1 })
db.incidents.createIndex({ "reported_at": -1 })
db.incidents.createIndex({ "location.geometry": "2dsphere" })

// Compound indexes
db.incidents.createIndex({ "status": 1, "severity": 1 })
db.incidents.createIndex({ "asset_id": 1, "status": 1 })
```

---

### 5. iot_sensors
**Purpose**: IoT sensor device registry

```javascript
{
  _id: ObjectId,
  sensor_code: String,           // Unique identifier (e.g., "SENS-001")
  asset_id: ObjectId,            // Reference to assets._id

  // Sensor Details
  sensor_type: String,           // "temperature" | "humidity" | "pressure" | "vibration" | "power" | "custom"
  manufacturer: String?,
  model: String?,
  firmware_version: String?,

  // Configuration
  measurement_unit: String,      // "°C" | "%" | "kPa" | "Hz" | "kW"
  sample_rate: Number,           // seconds between readings
  thresholds: {
    min_value: Number?,
    max_value: Number?,
    critical_min: Number?,
    critical_max: Number?,
    warning_min: Number?,
    warning_max: Number?
  },

  // Connectivity
  connection_type: String,       // "wifi" | "lora" | "cellular" | "zigbee" | "bluetooth"
  ip_address: String?,
  mac_address: String?,
  gateway_id: String?,

  // Status
  status: String,                // "online" | "offline" | "maintenance" | "error"
  last_seen: Date,
  last_reading: {
    value: Number,
    timestamp: Date,
    status: String               // "normal" | "warning" | "critical"
  },

  // Calibration
  calibration_date: Date?,
  calibration_due: Date?,
  calibration_factor: Number?,   // Adjustment multiplier

  // Installation
  installed_at: Date?,
  installed_by: ObjectId?,
  location_description: String?, // "Top of pole, facing north"

  // Maintenance
  maintenance_schedule: String?, // "monthly" | "quarterly" | "yearly"
  last_maintenance: Date?,
  next_maintenance: Date?,

  // Tracking
  created_at: Date,
  updated_at: Date,
  created_by: ObjectId,

  // Metadata
  notes: String?,
  tags: [String]
}
```

**Indexes**:
```javascript
db.iot_sensors.createIndex({ "sensor_code": 1 }, { unique: true })
db.iot_sensors.createIndex({ "asset_id": 1 })
db.iot_sensors.createIndex({ "status": 1 })
db.iot_sensors.createIndex({ "sensor_type": 1 })
db.iot_sensors.createIndex({ "last_seen": -1 })
```

---

### 6. sensor_data
**Purpose**: Time-series sensor readings (consider MongoDB Time Series Collection)

```javascript
{
  _id: ObjectId,
  sensor_id: ObjectId,           // Reference to iot_sensors._id
  asset_id: ObjectId,            // Denormalized for query performance

  // Reading
  timestamp: Date,               // Measurement time
  value: Number,                 // Sensor reading
  unit: String,                  // Measurement unit (denormalized)

  // Quality
  quality: String,               // "good" | "suspect" | "bad"
  quality_flags: [String],       // ["out_of_range", "sensor_drift", ...]

  // Analysis
  status: String,                // "normal" | "warning" | "critical"
  threshold_exceeded: Boolean,

  // Metadata
  metadata: {
    battery_level: Number?,      // For battery-powered sensors
    signal_strength: Number?,
    temperature: Number?,        // Sensor internal temp
    custom: Object
  }
}
```

**Time-Series Collection Configuration**:
```javascript
db.createCollection("sensor_data", {
  timeseries: {
    timeField: "timestamp",
    metaField: "sensor_id",
    granularity: "minutes"
  },
  expireAfterSeconds: 31536000    // 1 year retention
})

// Indexes
db.sensor_data.createIndex({ "sensor_id": 1, "timestamp": -1 })
db.sensor_data.createIndex({ "asset_id": 1, "timestamp": -1 })
db.sensor_data.createIndex({ "status": 1, "timestamp": -1 })
```

**Data Retention Policy**:
- Raw data: 1 year
- Hourly aggregations: 3 years
- Daily aggregations: 10 years

---

### 7. alerts
**Purpose**: System alerts and warnings from IoT sensors or system events

```javascript
{
  _id: ObjectId,
  alert_code: String,            // Unique identifier

  // Source
  source_type: String,           // "sensor" | "system" | "manual"
  sensor_id: ObjectId?,          // Reference to iot_sensors._id
  asset_id: ObjectId?,           // Reference to assets._id

  // Alert Details
  type: String,                  // "threshold_exceeded" | "sensor_offline" | "maintenance_due" | "custom"
  severity: String,              // "info" | "warning" | "critical" | "emergency"
  title: String,
  message: String,

  // Trigger Conditions
  trigger_value: Number?,        // Value that triggered alert
  threshold_value: Number?,      // Threshold that was exceeded
  condition: String?,            // "greater_than" | "less_than" | "equals"

  // Status
  status: String,                // "active" | "acknowledged" | "resolved" | "dismissed"
  acknowledged_at: Date?,
  acknowledged_by: ObjectId?,
  resolved_at: Date?,
  resolved_by: ObjectId?,
  resolution_notes: String?,

  // Actions Taken
  incident_created: Boolean,
  incident_id: ObjectId?,
  maintenance_created: Boolean,
  maintenance_id: ObjectId?,

  // Notifications
  notifications_sent: [{
    recipient_id: ObjectId,
    method: String,              // "email" | "push" | "sms"
    sent_at: Date,
    delivered: Boolean
  }],

  // Tracking
  triggered_at: Date,
  created_at: Date,
  updated_at: Date,

  // Metadata
  metadata: Object,              // Additional context
  auto_created: Boolean          // Created by system vs manual
}
```

**Indexes**:
```javascript
db.alerts.createIndex({ "alert_code": 1 }, { unique: true })
db.alerts.createIndex({ "asset_id": 1 })
db.alerts.createIndex({ "sensor_id": 1 })
db.alerts.createIndex({ "status": 1 })
db.alerts.createIndex({ "severity": 1 })
db.alerts.createIndex({ "triggered_at": -1 })

// Compound indexes
db.alerts.createIndex({ "status": 1, "severity": 1, "triggered_at": -1 })
```

---

### 8. budgets
**Purpose**: Budget planning, allocation, and tracking

```javascript
{
  _id: ObjectId,
  budget_code: String,           // Unique identifier (e.g., "BDG-2024-Q1")

  // Budget Period
  fiscal_year: Number,           // 2024
  period_type: String,           // "annual" | "quarterly" | "monthly" | "project-based"
  start_date: Date,
  end_date: Date,

  // Budget Details
  name: String,                  // "Q1 2024 Maintenance Budget"
  description: String?,
  category: String,              // "maintenance" | "capital" | "operations" | "emergency"

  // Allocation
  total_allocated: Number,       // Total budget amount
  departments: [{
    department: String,
    allocated_amount: Number,
    spent_amount: Number,
    remaining_amount: Number
  }],

  // Breakdown by Type
  breakdown: [{
    category: String,            // "labor" | "materials" | "equipment" | "contractors"
    allocated: Number,
    spent: Number,
    remaining: Number
  }],

  // Asset Categories
  asset_allocations: [{
    feature_type: String,        // "Trạm điện", "Đèn đường"
    allocated: Number,
    spent: Number,
    count: Number                // Number of assets
  }],

  // Financial Tracking
  currency: String,              // "VND"
  total_spent: Number,
  total_committed: Number,       // Committed but not yet spent
  total_remaining: Number,
  utilization_rate: Number,      // percentage spent

  // Approval
  status: String,                // "draft" | "pending_approval" | "approved" | "active" | "closed"
  submitted_by: ObjectId?,
  submitted_at: Date?,
  approved_by: ObjectId?,
  approved_at: Date?,
  rejection_reason: String?,

  // Tracking
  created_at: Date,
  updated_at: Date,
  created_by: ObjectId,
  closed_at: Date?,
  closed_by: ObjectId?,

  // Notes
  notes: String?,
  attachments: [{
    file_name: String,
    file_url: String,
    file_type: String,
    uploaded_at: Date
  }]
}
```

**Indexes**:
```javascript
db.budgets.createIndex({ "budget_code": 1 }, { unique: true })
db.budgets.createIndex({ "fiscal_year": 1 })
db.budgets.createIndex({ "status": 1 })
db.budgets.createIndex({ "category": 1 })
db.budgets.createIndex({ "start_date": 1, "end_date": 1 })
```

---

### 9. budget_transactions
**Purpose**: Individual budget expenses and transactions

```javascript
{
  _id: ObjectId,
  transaction_number: String,    // Unique identifier
  budget_id: ObjectId,           // Reference to budgets._id

  // Transaction Details
  type: String,                  // "expense" | "allocation" | "adjustment" | "refund"
  category: String,              // "labor" | "materials" | "equipment" | "contractors" | "other"
  description: String,
  amount: Number,
  currency: String,              // "VND"

  // Related Records
  maintenance_record_id: ObjectId?, // Reference to maintenance_records._id
  asset_id: ObjectId?,
  vendor_id: ObjectId?,          // Future: vendor management

  // Payment Details
  payment_method: String?,       // "bank_transfer" | "cash" | "credit_card" | "check"
  payment_reference: String?,    // Invoice number, receipt number
  payment_date: Date?,

  // Approval
  status: String,                // "pending" | "approved" | "rejected" | "paid"
  requires_approval: Boolean,
  approved_by: ObjectId?,
  approved_at: Date?,
  rejection_reason: String?,

  // Documentation
  invoice_number: String?,
  receipt_url: String?,
  attachments: [{
    file_name: String,
    file_url: String,
    file_type: String,
    uploaded_at: Date
  }],

  // Tracking
  transaction_date: Date,
  created_at: Date,
  updated_at: Date,
  created_by: ObjectId,

  // Accounting
  account_code: String?,         // Integration with accounting systems
  cost_center: String?,
  department: String?,

  // Notes
  notes: String?
}
```

**Indexes**:
```javascript
db.budget_transactions.createIndex({ "transaction_number": 1 }, { unique: true })
db.budget_transactions.createIndex({ "budget_id": 1 })
db.budget_transactions.createIndex({ "maintenance_record_id": 1 })
db.budget_transactions.createIndex({ "asset_id": 1 })
db.budget_transactions.createIndex({ "status": 1 })
db.budget_transactions.createIndex({ "transaction_date": -1 })
db.budget_transactions.createIndex({ "created_at": -1 })

// Compound indexes
db.budget_transactions.createIndex({ "budget_id": 1, "status": 1 })
```

---

### 10. notifications
**Purpose**: User notifications and communication

```javascript
{
  _id: ObjectId,

  // Recipient
  user_id: ObjectId,             // Reference to users._id

  // Notification Details
  type: String,                  // "maintenance_assigned" | "incident_reported" | "alert_triggered" | "budget_approved" | "comment_reply" | "system"
  title: String,
  message: String,

  // Related Resources
  resource_type: String?,        // "asset" | "maintenance" | "incident" | "alert" | "budget"
  resource_id: ObjectId?,

  // Action Link
  action_url: String?,           // Deep link to related resource
  action_label: String?,         // "View Incident" | "Review Work Order"

  // Delivery
  channels: [{
    type: String,                // "in_app" | "email" | "push" | "sms"
    status: String,              // "pending" | "sent" | "delivered" | "failed"
    sent_at: Date?,
    delivered_at: Date?,
    error: String?
  }],

  // Status
  read: Boolean,
  read_at: Date?,
  archived: Boolean,

  // Priority
  priority: String,              // "low" | "medium" | "high" | "urgent"

  // Tracking
  created_at: Date,
  expires_at: Date?,             // Auto-delete old notifications

  // Metadata
  metadata: Object               // Additional context
}
```

**Indexes**:
```javascript
db.notifications.createIndex({ "user_id": 1, "created_at": -1 })
db.notifications.createIndex({ "user_id": 1, "read": 1 })
db.notifications.createIndex({ "resource_type": 1, "resource_id": 1 })
db.notifications.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 }) // TTL index
```

---

### 11. audit_logs
**Purpose**: System activity audit trail

```javascript
{
  _id: ObjectId,

  // Actor
  user_id: ObjectId?,            // Reference to users._id (null for system)
  username: String?,
  user_role: String?,
  ip_address: String?,
  user_agent: String?,

  // Action
  action: String,                // "create" | "read" | "update" | "delete" | "login" | "logout"
  resource_type: String,         // "asset" | "user" | "maintenance" | "incident" | "budget"
  resource_id: String?,

  // Details
  description: String,           // Human-readable description
  changes: {
    before: Object?,             // Previous state
    after: Object?               // New state
  },

  // Context
  request_id: String?,           // Correlation ID
  session_id: String?,
  endpoint: String?,             // API endpoint
  http_method: String?,          // GET, POST, PUT, DELETE

  // Result
  status: String,                // "success" | "failure"
  error_message: String?,

  // Tracking
  timestamp: Date,

  // Compliance
  data_classification: String?,  // "public" | "internal" | "confidential" | "restricted"
  retention_period: Number?      // Days to retain
}
```

**Indexes**:
```javascript
db.audit_logs.createIndex({ "timestamp": -1 })
db.audit_logs.createIndex({ "user_id": 1, "timestamp": -1 })
db.audit_logs.createIndex({ "resource_type": 1, "resource_id": 1 })
db.audit_logs.createIndex({ "action": 1, "timestamp": -1 })
db.audit_logs.createIndex({ "request_id": 1 })

// TTL index for automatic cleanup (adjust based on compliance requirements)
db.audit_logs.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 31536000 }) // 1 year
```

---

### 12. reports
**Purpose**: Generated reports and analytics

```javascript
{
  _id: ObjectId,
  report_code: String,           // Unique identifier

  // Report Details
  name: String,
  type: String,                  // "maintenance_summary" | "asset_inventory" | "budget_report" | "incident_analysis" | "custom"
  description: String?,

  // Parameters
  parameters: {
    date_from: Date?,
    date_to: Date?,
    asset_types: [String]?,
    departments: [String]?,
    custom: Object
  },

  // Generated Data
  data: Object,                  // Report results (consider GridFS for large reports)
  summary: {
    total_records: Number,
    key_metrics: Object
  },

  // Export
  format: String,                // "pdf" | "excel" | "csv" | "json"
  file_url: String?,             // GridFS reference or MinIO URL
  file_size: Number?,            // bytes

  // Scheduling
  is_scheduled: Boolean,
  schedule: {
    frequency: String?,          // "daily" | "weekly" | "monthly"
    next_run: Date?,
    recipients: [ObjectId]       // User IDs to send to
  },

  // Status
  status: String,                // "generating" | "completed" | "failed"
  generation_started: Date?,
  generation_completed: Date?,
  error_message: String?,

  // Access
  created_by: ObjectId,
  shared_with: [ObjectId],       // User IDs with access
  is_public: Boolean,

  // Tracking
  created_at: Date,
  expires_at: Date?,             // Auto-delete old reports
  downloaded_count: Number,
  last_downloaded_at: Date?,

  // Metadata
  tags: [String],
  notes: String?
}
```

**Indexes**:
```javascript
db.reports.createIndex({ "report_code": 1 }, { unique: true })
db.reports.createIndex({ "type": 1 })
db.reports.createIndex({ "created_by": 1, "created_at": -1 })
db.reports.createIndex({ "status": 1 })
db.reports.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 }) // TTL index
```

---

### 13. system_settings
**Purpose**: Application configuration and settings

```javascript
{
  _id: ObjectId,
  key: String,                   // Unique setting key (e.g., "app.maintenance.default_duration")

  // Value
  value: Object,                 // Can be string, number, boolean, object, array
  data_type: String,             // "string" | "number" | "boolean" | "object" | "array"

  // Metadata
  category: String,              // "app" | "security" | "notifications" | "integrations" | "features"
  description: String,
  display_name: String,

  // Validation
  validation_rules: {
    required: Boolean?,
    min: Number?,
    max: Number?,
    pattern: String?,            // Regex pattern
    allowed_values: [Object]?
  },

  // Access Control
  is_public: Boolean,            // Can citizens see this?
  requires_admin: Boolean,       // Requires admin to modify

  // Environment
  environment: String?,          // "development" | "staging" | "production" | "all"

  // Tracking
  created_at: Date,
  updated_at: Date,
  updated_by: ObjectId?,

  // Audit
  change_history: [{
    previous_value: Object,
    new_value: Object,
    changed_by: ObjectId,
    changed_at: Date,
    reason: String?
  }]
}
```

**Indexes**:
```javascript
db.system_settings.createIndex({ "key": 1 }, { unique: true })
db.system_settings.createIndex({ "category": 1 })
db.system_settings.createIndex({ "environment": 1 })
```

**Example Settings**:
```javascript
// Maintenance defaults
{ key: "maintenance.default_duration_minutes", value: 120 }
{ key: "maintenance.require_photos", value: true }
{ key: "maintenance.auto_assign_enabled", value: false }

// Alert thresholds
{ key: "alerts.sensor_offline_threshold_minutes", value: 15 }
{ key: "alerts.critical_notification_channels", value: ["email", "sms", "push"] }

// Budget
{ key: "budget.approval_threshold_amount", value: 10000000 }
{ key: "budget.currency", value: "VND" }

// Features
{ key: "features.qr_code_enabled", value: true }
{ key: "features.citizen_reporting_enabled", value: true }
{ key: "features.iot_integration_enabled", value: true }

// Map
{ key: "map.default_center_lat", value: 15.974846711696628 }
{ key: "map.default_center_lng", value: 108.2544869184494 }
{ key: "map.default_zoom", value: 13 }
```

---

## Additional Collections (Future Considerations)

### 14. vendors (Future)
```javascript
{
  _id: ObjectId,
  vendor_code: String,
  name: String,
  contact_person: String,
  email: String,
  phone: String,
  address: String,
  services: [String],
  rating: Number,
  status: String,
  created_at: Date
}
```

### 15. work_schedules (Future)
```javascript
{
  _id: ObjectId,
  technician_id: ObjectId,
  date: Date,
  shifts: [{
    start_time: Date,
    end_time: Date,
    status: String
  }],
  assigned_tasks: [ObjectId]
}
```

### 16. asset_groups (Future)
```javascript
{
  _id: ObjectId,
  group_name: String,
  group_type: String,
  asset_ids: [ObjectId],
  created_at: Date
}
```

---

## Data Retention & Archival Strategy

### Hot Data (MongoDB Primary)
- **Assets**: Indefinite (active assets)
- **Users**: While active + 2 years after deactivation
- **Maintenance Records**: 3 years
- **Incidents**: 2 years
- **IoT Sensors**: Indefinite (active sensors)
- **Sensor Data**: 1 year (raw), 3 years (hourly), 10 years (daily)
- **Alerts**: 1 year
- **Notifications**: 90 days
- **Audit Logs**: 1 year

### Cold Storage (Archive/MinIO)
- Move older data to cheaper storage (MinIO with lifecycle policies)
- Compress and archive data beyond retention periods
- Keep searchable indexes for archived data

### Compliance Requirements
- Audit logs: Minimum 1 year (adjust for local regulations)
- Financial transactions: 7-10 years (per Vietnamese accounting law)
- User data: GDPR-compliant deletion upon request

---

## Performance Optimization

### 1. Indexing Strategy
✅ **Already Covered**: Comprehensive indexes for all collections above

### 2. Denormalization Opportunities
- Store `asset.name` and `asset.feature_type` in `maintenance_records` for faster queries
- Store `user.full_name` in `audit_logs` to avoid user lookup
- Store `sensor.unit` in `sensor_data` for performance

### 3. Aggregation Pipeline Optimization
```javascript
// Example: Get maintenance summary per asset type
db.maintenance_records.aggregate([
  {
    $lookup: {
      from: "assets",
      localField: "asset_id",
      foreignField: "_id",
      as: "asset"
    }
  },
  { $unwind: "$asset" },
  {
    $group: {
      _id: "$asset.feature_type",
      total_maintenance: { $sum: 1 },
      total_cost: { $sum: "$total_cost" },
      avg_duration: { $avg: "$actual_duration" }
    }
  }
])
```

### 4. Sharding Strategy (Future)
When data grows to TB scale:
- **Shard Key for `assets`**: `{ location.district: 1, _id: 1 }`
- **Shard Key for `sensor_data`**: `{ sensor_id: 1, timestamp: 1 }`
- **Shard Key for `audit_logs`**: `{ timestamp: 1, user_id: 1 }`

---

## Migration from Current Schema

### Current State
- ✅ `assets` - Basic implementation exists
- ✅ `maintenance_records` - Basic implementation exists
- ❌ All other collections - Need to be created

### Migration Steps

1. **Add Missing Fields to Existing Collections**
   - Enhance `assets` with all new fields
   - Enhance `maintenance_records` with financial tracking

2. **Create New Collections**
   - Create all 11 new collections with proper schemas

3. **Data Migration**
   - Migrate existing data to new schema
   - Backfill required fields with defaults

4. **Index Creation**
   - Create all recommended indexes
   - Monitor index performance

5. **Application Update**
   - Update Pydantic models
   - Update API endpoints
   - Update business logic

---

## Database Design Best Practices Applied

✅ **Atomicity**: Use MongoDB transactions for multi-document updates
✅ **Denormalization**: Strategic denormalization for performance (asset names, user names)
✅ **Embedding vs Referencing**: Embed small, stable data; reference large, changing data
✅ **Indexing**: Comprehensive indexes on all query patterns
✅ **Time-Series**: Use time-series collections for sensor data
✅ **TTL Indexes**: Auto-delete old notifications, reports, audit logs
✅ **Geospatial**: 2dsphere indexes for map queries
✅ **Soft Deletes**: Use `status: "deleted"` instead of hard deletes for important data
✅ **Audit Trail**: Comprehensive audit logging
✅ **Schema Validation**: Use MongoDB schema validation (optional, Pydantic handles this)

---

## Conclusion

This database design provides:
1. **Scalability**: Horizontal scaling via sharding, time-series for IoT
2. **Performance**: Comprehensive indexing, strategic denormalization
3. **Flexibility**: Schema-less MongoDB for evolving requirements
4. **Geospatial**: Native 2dsphere indexes for map queries
5. **Time-Series**: Optimized for IoT sensor data
6. **Audit & Compliance**: Complete audit trail, data retention policies
7. **Multi-tenancy Ready**: Department-based data segregation
8. **API-Friendly**: JSON-native storage for JSON-LD APIs

**Next Steps**:
1. Implement Pydantic models for all collections
2. Create migration scripts
3. Set up MongoDB indexes
4. Implement data seeding for testing
5. Build API endpoints following the API design document
