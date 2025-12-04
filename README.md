# OpenInfra 🏗️

**Urban Infrastructure Asset Management System**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-green.svg)](https://www.mongodb.com/)

OpenInfra is a comprehensive urban infrastructure asset management system designed to digitize and optimize the lifecycle management of public infrastructure and telecommunications assets. The system helps government agencies and utilities track, maintain, and optimize infrastructure assets while improving service quality, extending asset lifespan, reducing costs, and enhancing community safety through data-driven decision making.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Application](#running-the-application)
- [User Roles](#-user-roles)
- [API Documentation](#-api-documentation)
- [Deployment](#-deployment)
- [Data Sources](#-data-sources)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## 🎯 Overview

OpenInfra addresses the critical need for modern infrastructure management by providing:

- **Complete Asset Lifecycle Management**: Track assets from installation to retirement
- **Real-time IoT Monitoring**: Monitor infrastructure health with sensor data and alerts
- **GIS Integration**: Visualize and query assets on interactive maps
- **Maintenance Optimization**: Schedule preventive maintenance and track work orders
- **Citizen Engagement**: Enable public reporting through QR/NFC codes
- **Budget Management**: Track costs and optimize resource allocation
- **Data-driven Decisions**: Generate insights through analytics and reporting

The system is built on **Clean Architecture** principles with **Domain-Driven Design** patterns, ensuring scalability, maintainability, and production-grade reliability.

---

## ✨ Key Features

### 1. 🗺️ Interactive GIS Mapping

- **Multi-layer Visualization**: Display BTS stations, signal strength (RSRP, SINR), and coverage anomalies
- **Geospatial Queries**: Find assets by location, radius, or custom polygons
- **Real-time Updates**: View live asset status and sensor readings
- **Coverage Analysis**: Automatically detect and alert on signal coverage issues
- **Population-weighted Prioritization**: Focus on high-impact areas

### 2. 📦 Complete Asset Lifecycle Management

- **Comprehensive Asset Profiles**: Track manufacturer, model, installation date, specifications
- **Maintenance History**: Complete audit trail of all maintenance and repairs
- **Incident Tracking**: Record and manage infrastructure issues
- **Preventive Maintenance Scheduling**: Automated reminders and planning
- **Document Management**: Store drawings, manuals, and contracts
- **Advanced Search & Reporting**: Filter, export, and analyze asset data

### 3. 📱 Field Access via QR/NFC

- **Quick Scanning**: Access asset information instantly in the field
- **Public Information**: Citizens can view basic asset details
- **Citizen Reporting**: Report issues with photos directly from scanned assets
- **Technician Access**: Field workers get full maintenance information
- **Offline Support**: Basic information available without connectivity

### 4. 🔔 Real-time IoT Monitoring & Alerts

- **Multi-sensor Support**: Temperature, tilt, door sensors, voltage, UPS, A/C monitoring
- **Threshold-based Alerts**: Automatic warnings when readings exceed limits
- **24/7 Monitoring Dashboard**: Real-time overview of all sensors and alerts
- **Automatic Ticket Generation**: Create maintenance tasks from critical alerts
- **Historical Analytics**: Trend analysis and predictive maintenance

### 5. 📡 Intelligent Coverage Monitoring

- **Automatic Anomaly Detection**: Identify areas with degraded RSRP/SINR signals
- **Citizen Feedback Integration**: Incorporate user reports into analysis
- **Population Density Weighting**: Prioritize high-impact areas
- **Nearby Station Identification**: Find relevant infrastructure for troubleshooting
- **Alert Management**: Proactive notifications for coverage issues

### 6. 🔧 Maintenance Management

- **Work Order System**: Create, assign, and track maintenance tasks
- **Technician Assignment**: Route tasks to appropriate field workers
- **Mobile-friendly Interface**: Optimized for field use
- **Cost Tracking**: Record labor, parts, and total expenses
- **Quality Assurance**: Approval workflows and verification
- **Recurring Maintenance**: Automated scheduling for preventive tasks

### 7. 💰 Budget Management

- **Budget Planning**: Allocate funds by department and category
- **Transaction Tracking**: Monitor actual spending vs. budget
- **Approval Workflows**: Multi-level authorization for expenses
- **Financial Reporting**: Real-time budget utilization dashboards
- **Cost Analysis**: Link maintenance costs to assets and projects

### 8. 🤖 AI-Ready API (MCP - Model Context Protocol)

- **Semantic API**: JSON-LD for machine-readable data
- **MCP Integration**: Simplified AI agent interaction
- **Self-documenting**: No need to learn complex API structures
- **Automatic Authentication**: Built-in security for AI systems

---

## 🛠️ Technology Stack

### Backend

- **Framework**: FastAPI (Python 3.11+)
- **Database**: MongoDB 7.0+ (geospatial, time-series)
- **Cache**: Redis 7.0+
- **Task Queue**: Celery + Redis
- **IoT Gateway**: MQTT (Mosquitto)
- **Storage**: MinIO (S3-compatible object storage)
- **Authentication**: JWT with RBAC

### Frontend

- **Framework**: React 18+ with TypeScript
- **Routing**: TanStack Router
- **State Management**: Zustand + TanStack Query
- **UI Components**: shadcn/ui + Tailwind CSS
- **Maps**: Leaflet + OpenStreetMap
- **Forms**: React Hook Form + Zod validation

### DevOps & Infrastructure

- **Containerization**: Docker + Docker Compose
- **Orchestration**: Kubernetes (production)
- **CI/CD**: GitHub Actions
- **Cloud Platform**: Google Cloud Platform (GCP)
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: OpenTelemetry + Jaeger

---

## 🏗️ Architecture

OpenInfra follows **Clean Architecture** principles with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer (React)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              API Layer (FastAPI Routers)                    │
│  • Authentication & Authorization (JWT + RBAC)              │
│  • Request Validation (Pydantic)                            │
│  • Rate Limiting & CORS                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               Domain Layer (Business Logic)                 │
│  • Services: Asset, Maintenance, IoT, Budget, Alert         │
│  • Models: Domain entities with business rules              │
│  • Repositories: Abstract data access interfaces            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           Infrastructure Layer (Implementations)            │
│  • MongoDB (with Motor async driver)                        │
│  • Redis (caching & pub/sub)                                │
│  • Celery (background tasks)                                │
│  • MQTT (IoT data ingestion)                                │
│  • MinIO (object storage)                                   │
│  • External APIs (OSM, email, SMS)                          │
└─────────────────────────────────────────────────────────────┘
```

**Key Architecture Benefits**:
- ✅ **Testable**: Business logic independent of frameworks
- ✅ **Maintainable**: Clear boundaries between layers
- ✅ **Scalable**: Horizontal scaling of all components
- ✅ **Flexible**: Easy to swap infrastructure components

For detailed architecture documentation, see [backend/docs/architecture.md](backend/docs/architecture.md).

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Docker & Docker Compose** - [Download](https://www.docker.com/get-started)
- **Git** - [Download](https://git-scm.com/)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/your-org/openinfra.git
cd openinfra
```

2. **Start infrastructure services**

```bash
cd infra
docker-compose up -d
```

This starts:
- MongoDB (port 27017)
- Redis (port 6379)
- MQTT Broker (port 1883)

3. **Setup Backend**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment file
cp .env.example .env
# Edit .env with your settings (see Configuration section)
```

4. **Initialize Database**

```bash
# Create database structure and indexes
python scripts/init_db.py

# Create admin superuser
python scripts/create_superuser.py
```

5. **Setup Frontend**

```bash
cd frontend

# Install dependencies
npm install

# Copy and configure environment file
cp .env.example .env
# Edit .env with backend API URL
```

### Configuration

#### Backend Configuration (`.env`)

```bash
# Application
PROJECT_NAME=OpenInfra
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug

# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=openinfra_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Admin Account (for create_superuser.py)
ADMIN_DEFAULT_USERNAME=admin
ADMIN_DEFAULT_PASSWORD=change-this-strong-password

# External Services (Optional)
OSM_NOMINATIM_URL=https://nominatim.openstreetmap.org
SENDGRID_API_KEY=your-sendgrid-api-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token

# Storage (local for development, minio for production)
STORAGE_BACKEND=local
# For MinIO:
# STORAGE_BACKEND=minio
# MINIO_ENDPOINT=localhost:9000
# MINIO_ACCESS_KEY=minioadmin
# MINIO_SECRET_KEY=minioadmin
# MINIO_BUCKET_NAME=openinfra-assets
# MINIO_USE_SSL=false

# MQTT
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=openinfra
MQTT_PASSWORD=change-this

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

#### Frontend Configuration (`.env`)

```bash
VITE_BASE_API_URL=http://localhost:8000
VITE_LEADERBOARD_URL=http://localhost:8000
```

### Running the Application

#### Backend Services

Open **3 separate terminals** for backend services:

**Terminal 1 - API Server:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Celery Worker (Background Tasks):**
```bash
cd backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info
```

**Terminal 3 - Celery Beat (Task Scheduler):**
```bash
cd backend
source venv/bin/activate
celery -A app.celery_app beat --loglevel=info
```

#### Frontend

```bash
cd frontend
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **API Documentation (ReDoc)**: http://localhost:8000/redoc

### Default Admin Login

- **Login URL**: http://localhost:5173/admin/login
- **Username**: Set in `.env` (`ADMIN_DEFAULT_USERNAME`)
- **Password**: Set in `.env` (`ADMIN_DEFAULT_PASSWORD`)

**⚠️ Security Note**: Change the default credentials in `.env` before running `create_superuser.py`. Never use example credentials in production.

---

## 👥 User Roles

### 🔑 Administrator
**Full system access and management**

- Manage all assets and infrastructure
- Create and assign maintenance work orders
- Allocate and approve budgets
- Monitor system-wide status and alerts
- Generate reports and analytics
- Manage user accounts and permissions

### 🔧 Technician
**Field operations and maintenance**

- View assigned assets and locations
- Receive and update maintenance tasks
- Report incidents and issues
- Upload photos and documentation
- Update asset status in the field
- Access mobile-optimized interface

### 👨‍👩‍👧‍👦 Citizen (Public)
**Information access and issue reporting**

- View public asset information via QR/NFC
- Report infrastructure issues with photos
- Track submitted incident reports
- View basic infrastructure status
- **Restricted**: Cannot modify any data

---

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Versioning

All endpoints are versioned: `/api/v1/...`

### Authentication

Most endpoints require JWT authentication:

```bash
# Login to get token
POST /api/v1/auth/login
{
  "username": "your_username",
  "password": "your_password"
}

# Use token in subsequent requests
Authorization: Bearer <your_jwt_token>
```

### Key Endpoints

```
Authentication
  POST   /api/v1/auth/login              # Login
  POST   /api/v1/auth/register           # Register
  POST   /api/v1/auth/refresh            # Refresh token

Assets
  GET    /api/v1/assets                  # List assets (paginated)
  POST   /api/v1/assets                  # Create asset
  GET    /api/v1/assets/{id}             # Get asset details
  PUT    /api/v1/assets/{id}             # Update asset
  DELETE /api/v1/assets/{id}             # Delete asset
  GET    /api/v1/assets/nearby           # Find nearby assets
  GET    /api/v1/assets/{id}/history     # Asset change history

Maintenance
  GET    /api/v1/maintenance             # List work orders
  POST   /api/v1/maintenance             # Create work order
  GET    /api/v1/maintenance/{id}        # Get work order
  PUT    /api/v1/maintenance/{id}        # Update work order
  POST   /api/v1/maintenance/{id}/assign # Assign to technician

Incidents
  GET    /api/v1/incidents               # List incidents
  POST   /api/v1/incidents               # Report incident
  GET    /api/v1/incidents/{id}          # Get incident details
  PUT    /api/v1/incidents/{id}          # Update incident

IoT Sensors
  GET    /api/v1/iot/sensors             # List sensors
  POST   /api/v1/iot/sensors             # Register sensor
  GET    /api/v1/iot/sensors/{id}/data   # Get sensor readings
  POST   /api/v1/iot/sensors/{id}/data   # Ingest reading (API key)

Alerts
  GET    /api/v1/alerts                  # List alerts
  POST   /api/v1/alerts/{id}/acknowledge # Acknowledge alert
  POST   /api/v1/alerts/{id}/resolve     # Resolve alert

Budgets
  GET    /api/v1/budgets                 # List budgets
  POST   /api/v1/budgets                 # Create budget
  GET    /api/v1/budgets/{id}            # Get budget details

Public Access (No Authentication)
  GET    /api/v1/public/assets/{code}    # Get asset by QR/NFC code
  POST   /api/v1/public/incidents        # Anonymous incident reporting
```

For complete API documentation, see [backend/docs/API_DOCUMENTATION.md](backend/docs/API_DOCUMENTATION.md).

---

## 🚢 Deployment

### Development Environment

Use Docker Compose (already running from setup):

```bash
cd infra
docker-compose up -d
```

### Production Deployment

OpenInfra supports multiple deployment strategies:

#### 1. Docker Compose (Small/Medium Deployments)

```bash
# Production Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

#### 2. Kubernetes (Large Scale/Enterprise)

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/
```

**Production Features**:
- Horizontal Pod Autoscaling
- Load balancing
- Health checks
- Rolling updates
- Secret management
- TLS/SSL certificates

#### 3. Cloud Platforms

**Recommended**: Google Cloud Platform (GKE)
- Managed Kubernetes
- MongoDB Atlas (managed database)
- Cloud Storage for files
- Cloud Monitoring & Logging

For detailed deployment instructions, see [backend/docs/deployment.md](backend/docs/deployment.md).

---

## 📊 Data Sources

OpenInfra integrates data from multiple Vietnamese telecommunications sources:

1. **nPerf.com** - Mobifone 3G/4G/5G speed data
2. **Open Network (Viettel)** - Network infrastructure data
3. **MobiMap** (Mobifone Band Map) - BTS station locations
4. **Da Nang Public Service Portal** - BTS station data (crawled)
5. **Certification Data Lookup** - BTS station information
6. **OpenStreetMap** - Geospatial data and geocoding

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Ways to Contribute

- 🐛 **Report bugs** via GitHub Issues
- 💡 **Suggest features** via GitHub Discussions
- 📝 **Improve documentation**
- 🔧 **Submit pull requests**

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add tests** for new functionality
5. **Ensure tests pass**: `pytest` (backend), `npm test` (frontend)
6. **Commit with clear messages**: `git commit -m "feat: add amazing feature"`
7. **Push to your fork**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Code Style

**Backend (Python)**:
- Follow PEP 8
- Use Black for formatting
- Use type hints
- Write docstrings (Google style)

**Frontend (TypeScript)**:
- Use ESLint + Prettier
- Follow React best practices
- Write clear component documentation

### Running Tests

**Backend:**
```bash
cd backend
pytest --cov=app --cov-report=html
```

**Frontend:**
```bash
cd frontend
npm test
npm run test:e2e
```

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenStreetMap** - Geospatial data and mapping services
- **FastAPI** - Modern, fast web framework
- **MongoDB** - Flexible, scalable database
- **React Community** - Frontend ecosystem
- **shadcn/ui** - Beautiful UI components
- **Font Awesome** - Icons by Font Awesome (https://fontawesome.com) licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- **Vietnamese Telecom Providers** - Infrastructure data sources
- All open-source contributors

---

## 📞 Support & Contact

- **Documentation**: [backend/docs/](backend/docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/openinfra/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/openinfra/discussions)

---

## 🗺️ Project Roadmap

### Completed ✅
- Core authentication and authorization
- Basic asset management
- GIS integration
- IoT sensor monitoring
- Real-time alerts

### In Progress 🚧
- Advanced coverage analysis
- Predictive maintenance
- Mobile app for technicians
- Advanced reporting

### Planned 🔮
- Machine learning for anomaly detection
- 5G network optimization
- Multi-city deployment
- Public API marketplace
- Integration with government systems

---

## 📈 Performance & Scale

OpenInfra is designed to handle city-scale deployments:

- **Assets**: 1,000,000+ infrastructure items
- **Concurrent Users**: 10,000+ simultaneous users
- **Sensor Data**: 10,000 messages/second ingestion
- **API Response**: < 200ms (p95)
- **Uptime**: > 99.9% availability

---

## 🎓 Learn More

- **Architecture Guide**: [backend/docs/architecture.md](backend/docs/architecture.md)
- **Database Design**: [backend/docs/database-design.md](backend/docs/database-design.md)
- **API Design**: [backend/docs/api-design.md](backend/docs/api-design.md)
- **Project Plan**: [backend/docs/project-plan.md](backend/docs/project-plan.md)
- **Deployment Guide**: [backend/docs/deployment.md](backend/docs/deployment.md)

---

<div align="center">

**Built with ❤️ for better urban infrastructure management**

[⭐ Star us on GitHub](https://github.com/your-org/openinfra) | [🐛 Report Bug](https://github.com/your-org/openinfra/issues) | [💡 Request Feature](https://github.com/your-org/openinfra/issues)

</div>
