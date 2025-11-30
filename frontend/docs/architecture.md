# OpenInfra System Architecture

## Executive Summary

OpenInfra is a production-grade Urban Infrastructure Asset Management System designed using **Clean Architecture** principles with **Domain-Driven Design** (DDD) patterns. The system is built to be scalable, maintainable, and resilient, with clear separation of concerns and well-defined service boundaries.

**Architecture Style**: Modular Monolith with Microservices-Ready Design
**Primary Pattern**: Clean Architecture + Domain-Driven Design
**Database**: MongoDB with geospatial and time-series capabilities
**API Style**: RESTful JSON-LD with MCP (Model Context Protocol) for AI integration

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Design Principles](#design-principles)
3. [System Architecture](#system-architecture)
4. [Domain Model](#domain-model)
5. [Service Boundaries](#service-boundaries)
6. [Technology Stack](#technology-stack)
7. [Security Architecture](#security-architecture)
8. [Integration Architecture](#integration-architecture)
9. [Deployment Architecture](#deployment-architecture)
10. [Scalability & Performance](#scalability--performance)

---

## Architecture Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  Web App (React)  │  Mobile App  │  QR/NFC Scanner │  AI Agent  │
└────────────┬────────────────┬────────────────┬─────────────┬────┘
             │                │                │             │
             │                │                │             │
             ▼                ▼                ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API Gateway Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  • Authentication & Authorization (JWT/OAuth)                   │
│  • Rate Limiting & Throttling                                   │
│  • Request/Response Transformation                              │
│  • API Versioning (v1, v2)                                      │
│  • CORS & Security Headers                                      │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer (FastAPI)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Assets     │  │ Maintenance  │  │  Incidents   │         │
│  │   Router     │  │    Router    │  │    Router    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                  │                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │     IoT      │  │    Budget    │  │     User     │         │
│  │   Router     │  │    Router    │  │    Router    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                  │                 │
│         └─────────────────┴──────────────────┘                 │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Domain Layer                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              Domain Services (Business Logic)        │       │
│  ├─────────────────────────────────────────────────────┤       │
│  │  • AssetService         • MaintenanceService        │       │
│  │  • IncidentService      • IoTService                │       │
│  │  • BudgetService        • NotificationService       │       │
│  │  • AlertService         • ReportService             │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              Domain Models (Entities)                │       │
│  ├─────────────────────────────────────────────────────┤       │
│  │  • Asset            • MaintenanceRecord             │       │
│  │  • Incident         • IoTSensor                     │       │
│  │  • Budget           • Alert                         │       │
│  │  • User             • Notification                  │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   MongoDB    │  │    Redis     │  │   S3/GCS     │         │
│  │  (Primary)   │  │   (Cache)    │  │  (Storage)   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Celery     │  │  MQTT Broker │  │  Email/SMS   │         │
│  │ (Task Queue) │  │ (IoT Gateway)│  │   Gateway    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Design Principles

### 1. Clean Architecture (Uncle Bob)

We follow the **Clean Architecture** pattern with clear separation between layers:

```
┌─────────────────────────────────────────────┐
│         Frameworks & Drivers                │  ← Outermost (FastAPI, MongoDB, Redis)
├─────────────────────────────────────────────┤
│        Interface Adapters                   │  ← Controllers, Presenters, Gateways
├─────────────────────────────────────────────┤
│           Use Cases                         │  ← Application Business Rules
├─────────────────────────────────────────────┤
│           Entities                          │  ← Enterprise Business Rules (Core)
└─────────────────────────────────────────────┘
```

**Dependency Rule**: Dependencies point **inward** only. Inner layers know nothing about outer layers.

**Benefits**:
- ✅ Testable business logic independent of frameworks
- ✅ Framework-agnostic core domain
- ✅ Easy to swap infrastructure components
- ✅ Clear separation of concerns

### 2. Domain-Driven Design (DDD)

We organize code by **domain concepts**, not technical layers:

**Bounded Contexts**:
1. **Asset Management Context**: Assets, lifecycle, geospatial data
2. **Maintenance Context**: Work orders, scheduling, execution
3. **Incident Management Context**: Reports, investigations, resolution
4. **IoT Monitoring Context**: Sensors, data collection, alerts
5. **Budget Management Context**: Allocation, tracking, reporting
6. **Identity & Access Context**: Users, roles, permissions

**Ubiquitous Language**: We use domain terms consistently across code, docs, and communication.

### 3. SOLID Principles

- **S**ingle Responsibility: Each class has one reason to change
- **O**pen/Closed: Open for extension, closed for modification
- **L**iskov Substitution: Subtypes must be substitutable for their base types
- **I**nterface Segregation: Many specific interfaces > one general interface
- **D**ependency Inversion: Depend on abstractions, not concretions

### 4. API-First Design

- **Contract-First**: Define API contracts (OpenAPI) before implementation
- **Versioning**: All APIs versioned (`/api/v1/`, `/api/v2/`)
- **Standards**: Follow JSON-LD for linked data, MCP for AI integration
- **Documentation**: Auto-generated from Pydantic models and OpenAPI specs

---

## System Architecture

### Project Structure

```
backend/
├── app/
│   ├── main.py                    # Application entry point
│   │
│   ├── api/                       # API Layer (Interface Adapters)
│   │   ├── v1/                    # API Version 1
│   │   │   ├── routers/           # Route handlers
│   │   │   │   ├── assets.py
│   │   │   │   ├── maintenance.py
│   │   │   │   ├── incidents.py
│   │   │   │   ├── iot.py
│   │   │   │   ├── budgets.py
│   │   │   │   ├── users.py
│   │   │   │   ├── auth.py
│   │   │   │   └── reports.py
│   │   │   │
│   │   │   ├── dependencies.py    # DI container, common dependencies
│   │   │   └── schemas/           # API request/response schemas
│   │   │       ├── asset_schemas.py
│   │   │       ├── maintenance_schemas.py
│   │   │       └── ...
│   │   │
│   │   └── v2/                    # Future API Version 2
│   │
│   ├── domain/                    # Domain Layer (Business Logic)
│   │   ├── models/                # Domain Entities
│   │   │   ├── asset.py
│   │   │   ├── maintenance.py
│   │   │   ├── incident.py
│   │   │   ├── iot_sensor.py
│   │   │   ├── budget.py
│   │   │   ├── user.py
│   │   │   └── ...
│   │   │
│   │   ├── services/              # Domain Services (Use Cases)
│   │   │   ├── asset_service.py
│   │   │   ├── maintenance_service.py
│   │   │   ├── incident_service.py
│   │   │   ├── iot_service.py
│   │   │   ├── budget_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── alert_service.py
│   │   │   └── report_service.py
│   │   │
│   │   ├── repositories/          # Repository Interfaces (Abstractions)
│   │   │   ├── asset_repository.py
│   │   │   ├── maintenance_repository.py
│   │   │   └── ...
│   │   │
│   │   └── value_objects/         # Value Objects (DDD)
│   │       ├── coordinates.py
│   │       ├── money.py
│   │       └── ...
│   │
│   ├── infrastructure/            # Infrastructure Layer
│   │   ├── database/              # Database implementations
│   │   │   ├── mongodb.py         # MongoDB connection
│   │   │   ├── repositories/      # Repository implementations
│   │   │   │   ├── mongo_asset_repository.py
│   │   │   │   ├── mongo_maintenance_repository.py
│   │   │   │   └── ...
│   │   │   └── migrations/        # Database migrations
│   │   │
│   │   ├── cache/                 # Caching layer
│   │   │   └── redis_cache.py
│   │   │
│   │   ├── storage/               # File storage
│   │   │   ├── s3_storage.py
│   │   │   └── local_storage.py
│   │   │
│   │   ├── messaging/             # Message queues
│   │   │   ├── celery_config.py
│   │   │   └── mqtt_client.py
│   │   │
│   │   ├── external/              # External service integrations
│   │   │   ├── email_service.py
│   │   │   ├── sms_service.py
│   │   │   └── osm_service.py     # OpenStreetMap integration
│   │   │
│   │   └── security/              # Security implementations
│   │       ├── auth.py
│   │       ├── password.py
│   │       └── jwt.py
│   │
│   ├── core/                      # Core utilities (framework-agnostic)
│   │   ├── config.py              # Configuration management
│   │   ├── exceptions.py          # Custom exceptions
│   │   ├── logging.py             # Logging configuration
│   │   └── constants.py           # Application constants
│   │
│   ├── tasks/                     # Background tasks (Celery)
│   │   ├── maintenance_tasks.py
│   │   ├── notification_tasks.py
│   │   ├── report_tasks.py
│   │   └── iot_tasks.py
│   │
│   └── middleware/                # Custom middleware
│       ├── auth_middleware.py
│       ├── logging_middleware.py
│       └── rate_limit_middleware.py
│
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   ├── e2e/                       # End-to-end tests
│   └── fixtures/                  # Test fixtures
│
├── docs/                          # Documentation
├── migrations/                    # Database migrations
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Docker configuration
└── docker-compose.yml             # Docker Compose setup
```

### Layered Architecture Details

#### 1. API Layer (Interface Adapters)

**Responsibility**: Handle HTTP requests/responses, validate input, transform data

**Components**:
- **Routers**: FastAPI route handlers
- **Schemas**: Pydantic models for request/response validation
- **Dependencies**: Dependency injection for services

**Example**:
```python
# app/api/v1/routers/assets.py
from fastapi import APIRouter, Depends, HTTPException
from app.api.v1.schemas.asset_schemas import AssetCreate, AssetResponse
from app.domain.services.asset_service import AssetService
from app.api.v1.dependencies import get_asset_service

router = APIRouter()

@router.post("/", response_model=AssetResponse, status_code=201)
async def create_asset(
    asset_data: AssetCreate,
    asset_service: AssetService = Depends(get_asset_service)
):
    """Create a new infrastructure asset"""
    asset = await asset_service.create_asset(asset_data)
    return asset
```

#### 2. Domain Layer (Business Logic)

**Responsibility**: Core business logic, domain models, use cases

**Components**:
- **Models**: Domain entities (Asset, Maintenance, Incident, etc.)
- **Services**: Business logic and use cases
- **Repositories**: Abstract interfaces for data access
- **Value Objects**: Immutable domain objects

**Example**:
```python
# app/domain/services/asset_service.py
from app.domain.models.asset import Asset
from app.domain.repositories.asset_repository import AssetRepository
from app.domain.value_objects.coordinates import Coordinates

class AssetService:
    def __init__(self, asset_repository: AssetRepository):
        self.repository = asset_repository

    async def create_asset(self, asset_data: dict) -> Asset:
        """Business logic for creating an asset"""
        # Validate coordinates
        coords = Coordinates(
            longitude=asset_data["longitude"],
            latitude=asset_data["latitude"]
        )

        # Create asset entity
        asset = Asset(
            name=asset_data["name"],
            feature_type=asset_data["feature_type"],
            coordinates=coords,
            # ... other fields
        )

        # Business rules
        if asset.requires_approval():
            asset.status = "pending_approval"

        # Persist
        return await self.repository.create(asset)

    async def find_assets_nearby(
        self,
        coordinates: Coordinates,
        radius_meters: float
    ) -> list[Asset]:
        """Find assets within radius of coordinates"""
        return await self.repository.find_nearby(coordinates, radius_meters)
```

#### 3. Infrastructure Layer (Implementation Details)

**Responsibility**: External dependencies, database, third-party services

**Example**:
```python
# app/infrastructure/database/repositories/mongo_asset_repository.py
from app.domain.repositories.asset_repository import AssetRepository
from app.domain.models.asset import Asset
from motor.motor_asyncio import AsyncIOMotorDatabase

class MongoAssetRepository(AssetRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["assets"]

    async def create(self, asset: Asset) -> Asset:
        """MongoDB implementation of asset creation"""
        asset_dict = asset.dict()
        result = await self.collection.insert_one(asset_dict)
        asset.id = result.inserted_id
        return asset

    async def find_nearby(self, coords, radius_meters):
        """Geospatial query using MongoDB 2dsphere index"""
        query = {
            "geometry": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [coords.longitude, coords.latitude]
                    },
                    "$maxDistance": radius_meters
                }
            }
        }
        cursor = self.collection.find(query)
        assets = []
        async for doc in cursor:
            assets.append(Asset(**doc))
        return assets
```

---

## Domain Model

### Core Entities

```
┌─────────────────────────────────────────────────────────────────┐
│                         Asset (Root)                            │
├─────────────────────────────────────────────────────────────────┤
│ - id: ObjectId                                                  │
│ - asset_code: String                                            │
│ - name: String                                                  │
│ - feature_type: String                                          │
│ - geometry: Geometry (Value Object)                             │
│ - specifications: Specifications (Value Object)                 │
│ - status: AssetStatus (Enum)                                    │
│ - lifecycle_stage: LifecycleStage (Enum)                        │
├─────────────────────────────────────────────────────────────────┤
│ + add_sensor(sensor: IoTSensor)                                 │
│ + schedule_maintenance(schedule: MaintenanceSchedule)           │
│ + report_incident(incident: Incident)                           │
│ + calculate_depreciation(): Money                               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ has many
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MaintenanceRecord                           │
├─────────────────────────────────────────────────────────────────┤
│ - id: ObjectId                                                  │
│ - work_order_number: String                                     │
│ - asset_id: ObjectId                                            │
│ - type: MaintenanceType (Enum)                                  │
│ - status: MaintenanceStatus (Enum)                              │
│ - scheduled_date: DateTime                                      │
│ - cost: Money (Value Object)                                    │
├─────────────────────────────────────────────────────────────────┤
│ + assign_technician(technician: User)                           │
│ + start_work()                                                  │
│ + complete_work(notes: String)                                  │
│ + calculate_duration(): TimeDelta                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                          Incident                               │
├─────────────────────────────────────────────────────────────────┤
│ - id: ObjectId                                                  │
│ - incident_number: String                                       │
│ - asset_id: ObjectId?                                           │
│ - severity: Severity (Enum)                                     │
│ - status: IncidentStatus (Enum)                                 │
│ - reported_by: User                                             │
├─────────────────────────────────────────────────────────────────┤
│ + acknowledge(user: User)                                       │
│ + assign_to(technician: User)                                   │
│ + resolve(resolution: String)                                   │
│ + escalate()                                                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         IoTSensor                               │
├─────────────────────────────────────────────────────────────────┤
│ - id: ObjectId                                                  │
│ - sensor_code: String                                           │
│ - asset_id: ObjectId                                            │
│ - sensor_type: SensorType (Enum)                                │
│ - thresholds: SensorThresholds (Value Object)                   │
│ - status: SensorStatus (Enum)                                   │
├─────────────────────────────────────────────────────────────────┤
│ + record_reading(value: Number, timestamp: DateTime)            │
│ + check_thresholds(value: Number): Alert?                       │
│ + calibrate(factor: Number)                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Enumerations

```python
# Asset Status
class AssetStatus(str, Enum):
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    DAMAGED = "damaged"
    RETIRED = "retired"

# Maintenance Type
class MaintenanceType(str, Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"
    EMERGENCY = "emergency"

# Incident Severity
class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# User Roles
class UserRole(str, Enum):
    ADMIN = "admin"
    TECHNICIAN = "technician"
    CITIZEN = "citizen"
```

### Value Objects

```python
# Coordinates (immutable)
class Coordinates:
    def __init__(self, longitude: float, latitude: float):
        if not -180 <= longitude <= 180:
            raise ValueError("Invalid longitude")
        if not -90 <= latitude <= 90:
            raise ValueError("Invalid latitude")
        self._longitude = longitude
        self._latitude = latitude

    @property
    def longitude(self) -> float:
        return self._longitude

    @property
    def latitude(self) -> float:
        return self._latitude

    def to_geojson(self) -> dict:
        return {
            "type": "Point",
            "coordinates": [self._longitude, self._latitude]
        }

# Money (immutable)
class Money:
    def __init__(self, amount: Decimal, currency: str = "VND"):
        self._amount = amount
        self._currency = currency

    @property
    def amount(self) -> Decimal:
        return self._amount

    def add(self, other: 'Money') -> 'Money':
        if self._currency != other._currency:
            raise ValueError("Cannot add different currencies")
        return Money(self._amount + other._amount, self._currency)
```

---

## Service Boundaries

### 1. Asset Management Service

**Responsibility**: Manage infrastructure assets, lifecycle, geospatial queries

**Operations**:
- Create/Read/Update/Delete assets
- Geospatial queries (nearby assets, assets in area)
- Asset lifecycle management
- QR/NFC code generation
- Asset categorization and tagging

**Dependencies**: None (core domain)

---

### 2. Maintenance Service

**Responsibility**: Work order management, scheduling, execution tracking

**Operations**:
- Create work orders
- Schedule maintenance
- Assign technicians
- Track work progress
- Record costs and materials
- Generate maintenance reports

**Dependencies**: Asset Service, User Service, Budget Service

---

### 3. Incident Management Service

**Responsibility**: Citizen reports, issue tracking, resolution

**Operations**:
- Report incidents
- Assign incidents to technicians
- Track incident lifecycle
- Citizen engagement (comments, upvotes)
- Create maintenance work orders from incidents

**Dependencies**: Asset Service, User Service, Notification Service

---

### 4. IoT Monitoring Service

**Responsibility**: Sensor data collection, real-time monitoring, alerting

**Operations**:
- Register sensors
- Ingest sensor data
- Real-time threshold monitoring
- Generate alerts
- Sensor health monitoring

**Dependencies**: Asset Service, Alert Service

---

### 5. Budget Management Service

**Responsibility**: Budget planning, allocation, expense tracking

**Operations**:
- Create budgets
- Allocate funds
- Track expenses
- Budget approval workflow
- Financial reporting

**Dependencies**: Maintenance Service

---

### 6. Notification Service

**Responsibility**: Multi-channel notifications (email, SMS, push, in-app)

**Operations**:
- Send notifications
- Manage user preferences
- Notification templates
- Delivery tracking

**Dependencies**: User Service

---

### 7. Alert Service

**Responsibility**: Alert generation, prioritization, routing

**Operations**:
- Generate alerts from sensors
- Alert prioritization
- Alert routing to users
- Alert lifecycle management

**Dependencies**: IoT Service, Notification Service

---

### 8. User & Identity Service

**Responsibility**: Authentication, authorization, user management

**Operations**:
- User registration/login
- Role-based access control (RBAC)
- Permission management
- Session management
- Password management

**Dependencies**: None (core domain)

---

### 9. Report Service

**Responsibility**: Generate analytics, reports, dashboards

**Operations**:
- Generate scheduled reports
- Export data (PDF, Excel, CSV)
- Dashboard data aggregation
- Custom report builder

**Dependencies**: All services (read-only)

---

## Technology Stack

### Backend

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **API Framework** | FastAPI | Async, auto-docs, Pydantic validation, high performance |
| **Language** | Python 3.11+ | Ecosystem, async support, GIS libraries |
| **Database** | MongoDB 7.0+ | Geospatial, time-series, flexible schema |
| **Cache** | Redis 7.0+ | Fast in-memory cache, pub/sub for real-time |
| **Task Queue** | Celery + Redis | Distributed task processing, scheduling |
| **IoT Gateway** | MQTT (Mosquitto) | Lightweight, pub/sub for IoT devices |
| **Storage** | S3/GCS | Scalable object storage for files |
| **Search** | MongoDB Atlas Search | Full-text search within MongoDB |

### Frontend

| Component | Technology |
|-----------|-----------|
| **Framework** | React 18+ |
| **Maps** | Leaflet + OpenStreetMap |
| **State** | Zustand / TanStack Query |
| **UI** | Tailwind CSS + shadcn/ui |
| **Forms** | React Hook Form + Zod |

### DevOps & Infrastructure

| Component | Technology |
|-----------|-----------|
| **Containerization** | Docker |
| **Orchestration** | Docker Compose (dev), Kubernetes (prod) |
| **CI/CD** | GitHub Actions |
| **Cloud** | Google Cloud Platform |
| **Monitoring** | Prometheus + Grafana |
| **Logging** | ELK Stack (Elasticsearch, Logstash, Kibana) |
| **Tracing** | OpenTelemetry + Jaeger |

---

## Security Architecture

### Authentication & Authorization

**Strategy**: JWT-based authentication with role-based access control (RBAC)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Authentication Flow                          │
└─────────────────────────────────────────────────────────────────┘

Client                  API Gateway              Auth Service
  │                          │                        │
  ├─ POST /auth/login ──────▶│                        │
  │  { username, password }  │                        │
  │                          ├─ Verify credentials ──▶│
  │                          │                        │
  │                          │◀─ JWT token ───────────┤
  │◀─ { access_token } ──────┤                        │
  │                          │                        │
  ├─ GET /assets ───────────▶│                        │
  │  Authorization: Bearer.. │                        │
  │                          ├─ Validate JWT ────────▶│
  │                          │◀─ User + Roles ────────┤
  │                          ├─ Check permissions     │
  │◀─ { assets: [...] } ─────┤                        │
```

**JWT Token Structure**:
```json
{
  "sub": "user_id",
  "username": "john.doe",
  "role": "technician",
  "permissions": ["view_assets", "create_maintenance", "update_incidents"],
  "exp": 1735689600,
  "iat": 1735686000
}
```

### Role-Based Access Control (RBAC)

| Role | Permissions |
|------|------------|
| **Admin** | Full access to all resources, user management, budget approval |
| **Technician** | View assets, create/update maintenance, update incidents, mobile access |
| **Citizen** | View public assets (QR/NFC), report incidents, view own reports |

**Permission Matrix**:
```python
PERMISSIONS = {
    "admin": [
        "view_all_assets", "create_asset", "update_asset", "delete_asset",
        "view_all_maintenance", "create_maintenance", "update_maintenance",
        "view_all_incidents", "assign_incidents",
        "manage_users", "manage_budgets", "approve_budgets",
        "view_all_reports", "generate_reports"
    ],
    "technician": [
        "view_assigned_assets", "update_asset_status",
        "view_assigned_maintenance", "update_maintenance",
        "view_assigned_incidents", "update_incidents",
        "upload_photos"
    ],
    "citizen": [
        "view_public_assets", "scan_qr_code",
        "create_incident", "view_own_incidents", "comment_incidents"
    ]
}
```

### Data Security

1. **Encryption at Rest**: MongoDB encryption, encrypted S3 buckets
2. **Encryption in Transit**: TLS 1.3 for all communications
3. **Secrets Management**: Environment variables, Kubernetes secrets
4. **Input Validation**: Pydantic validation, SQL injection prevention
5. **Rate Limiting**: Per-user, per-IP rate limits
6. **CORS**: Whitelist allowed origins
7. **API Keys**: For external integrations (IoT devices, third-party systems)

### Audit Logging

All sensitive operations logged to `audit_logs` collection:
- User authentication events
- Asset CRUD operations
- Budget approvals
- Data exports
- Permission changes

---

## Integration Architecture

### 1. GIS Integration (OpenStreetMap)

**Purpose**: Geocoding, reverse geocoding, map tiles

**Integration Pattern**: External HTTP API calls

```python
# app/infrastructure/external/osm_service.py
class OSMService:
    async def geocode(self, address: str) -> Coordinates:
        """Convert address to coordinates"""
        # Call Nominatim API
        pass

    async def reverse_geocode(self, coords: Coordinates) -> str:
        """Convert coordinates to address"""
        pass
```

### 2. IoT Gateway Integration (MQTT)

**Purpose**: Real-time sensor data ingestion

**Integration Pattern**: MQTT pub/sub

```python
# app/infrastructure/messaging/mqtt_client.py
class MQTTClient:
    def subscribe_to_sensors(self):
        """Subscribe to sensor topics"""
        self.client.subscribe("sensors/+/data")
        self.client.on_message = self.on_sensor_data

    async def on_sensor_data(self, topic, payload):
        """Handle incoming sensor data"""
        sensor_id = topic.split("/")[1]
        await self.iot_service.ingest_sensor_data(sensor_id, payload)
```

### 3. Email/SMS Gateway

**Purpose**: Notification delivery

**Integration Pattern**: Third-party APIs (SendGrid, Twilio)

```python
# app/infrastructure/external/email_service.py
class EmailService:
    async def send_email(self, to: str, subject: str, body: str):
        """Send email via SendGrid"""
        pass

# app/infrastructure/external/sms_service.py
class SMSService:
    async def send_sms(self, to: str, message: str):
        """Send SMS via Twilio"""
        pass
```

### 4. AI Integration (MCP - Model Context Protocol)

**Purpose**: Enable AI agents to interact with the system

**Integration Pattern**: MCP-compliant API endpoints

```python
# app/api/v1/routers/mcp.py
@router.get("/mcp/context")
async def get_mcp_context():
    """Provide context to AI agents via MCP"""
    return {
        "@context": "https://schema.org",
        "@type": "InfrastructureManagementSystem",
        "capabilities": [
            "asset_management",
            "maintenance_scheduling",
            "incident_reporting"
        ],
        "endpoints": {
            "assets": "/api/v1/assets",
            "maintenance": "/api/v1/maintenance"
        }
    }
```

---

## Deployment Architecture

### Development Environment

```yaml
# docker-compose.yml
services:
  mongodb:
    image: mongo:7.0
    ports: ["27017:27017"]

  redis:
    image: redis:7.0
    ports: ["6379:6379"]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [mongodb, redis]

  frontend:
    build: ./frontend
    ports: ["5173:5173"]

  celery_worker:
    build: ./backend
    command: celery -A app.tasks worker
    depends_on: [redis, mongodb]

  celery_beat:
    build: ./backend
    command: celery -A app.tasks beat
    depends_on: [redis]
```

### Production Environment (Kubernetes)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer (GCP)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Ingress Controller                         │
│                         (NGINX)                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│   Frontend Pods (3x)     │   │   Backend Pods (5x)      │
│   - React App            │   │   - FastAPI              │
│   - Nginx                │   │   - Gunicorn + Uvicorn   │
└──────────────────────────┘   └─────────┬────────────────┘
                                         │
                      ┌──────────────────┴──────────────────┐
                      ▼                                     ▼
          ┌───────────────────────┐         ┌──────────────────────┐
          │  MongoDB Atlas        │         │  Redis Cloud         │
          │  (Replica Set 3x)     │         │  (HA Cluster)        │
          └───────────────────────┘         └──────────────────────┘
                      │
                      ▼
          ┌───────────────────────┐         ┌──────────────────────┐
          │  Celery Workers (3x)  │         │  MQTT Broker         │
          └───────────────────────┘         └──────────────────────┘
```

### Horizontal Scaling Strategy

| Component | Scaling Strategy | Min Replicas | Max Replicas |
|-----------|-----------------|--------------|--------------|
| Frontend | Horizontal Pod Autoscaler (CPU) | 2 | 10 |
| Backend API | HPA (CPU + Request Rate) | 3 | 20 |
| Celery Workers | HPA (Queue Length) | 2 | 10 |
| MongoDB | Replica Set (manual) | 3 | 5 |
| Redis | Cluster Mode | 3 | 6 |

---

## Scalability & Performance

### Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| API Response Time (p95) | < 200ms | Excluding heavy reports |
| API Response Time (p99) | < 500ms | Excluding heavy reports |
| Map Query Response | < 100ms | Geospatial queries with index |
| Concurrent Users | 10,000+ | City-wide deployment |
| Asset Count | 1,000,000+ | Scalable to large cities |
| Sensor Data Ingestion | 10,000 msg/s | MQTT + Celery processing |
| Database Size | 10TB+ | With time-series data |

### Optimization Strategies

1. **Database**:
   - Geospatial indexes (2dsphere) for map queries
   - Time-series collections for sensor data
   - Compound indexes for common query patterns
   - Read replicas for reporting

2. **Caching**:
   - Redis for frequently accessed data (assets, users)
   - Cache invalidation on writes
   - TTL-based expiration

3. **API**:
   - Pagination for all list endpoints
   - Field selection (GraphQL-style sparse fieldsets)
   - Response compression (gzip)
   - Connection pooling

4. **Background Processing**:
   - Celery for async tasks (reports, notifications)
   - Scheduled tasks for maintenance checks
   - Rate limiting for external APIs

5. **CDN**:
   - Static assets served from CDN
   - Map tiles cached at edge

---

## Observability

### Monitoring Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application                             │
│  (OpenTelemetry instrumentation for metrics, logs, traces)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Prometheus                                 │
│  - Scrapes metrics from /metrics endpoint                       │
│  - Stores time-series data                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Grafana                                  │
│  - Visualization dashboards                                     │
│  - Alerting rules                                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Jaeger                                     │
│  - Distributed tracing                                          │
│  - Request flow visualization                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ELK Stack                                    │
│  - Elasticsearch: Log storage                                   │
│  - Logstash: Log aggregation                                    │
│  - Kibana: Log visualization                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Key Metrics

- **Request Metrics**: Request rate, latency, error rate (RED metrics)
- **Database Metrics**: Query time, connection pool usage, slow queries
- **Cache Metrics**: Hit rate, miss rate, evictions
- **Celery Metrics**: Queue length, task success/failure rate, task duration
- **Business Metrics**: Assets created, maintenance completed, incidents resolved

---

## Conclusion

This architecture provides:

✅ **Scalability**: Horizontal scaling for all components
✅ **Maintainability**: Clean Architecture with clear boundaries
✅ **Testability**: Domain logic isolated from frameworks
✅ **Flexibility**: Easy to swap infrastructure components
✅ **Performance**: Optimized for low latency and high throughput
✅ **Security**: Multi-layer security with RBAC and encryption
✅ **Observability**: Comprehensive monitoring and logging
✅ **Resilience**: Fault tolerance and graceful degradation

**Next Steps**: See `api-design.md`, `project-plan.md`, and `deployment.md` for implementation details.
