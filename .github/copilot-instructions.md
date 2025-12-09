# OpenInfra - AI Coding Agent Instructions

## Project Overview
OpenInfra là hệ thống quản lý hạ tầng GIS với kiến trúc microservices: **FastAPI backend** + **React/Vite frontend** + **MongoDB** + **Celery/Redis** cho background tasks.

## Architecture & Data Flow

```
Frontend (React/Vite:5173)
    ↓ REST API (axios)
Backend (FastAPI:8000)
    ↓ Motor (async MongoDB driver)
MongoDB ← Celery Worker (CSV import scheduled daily 2AM UTC)
    ↑ Redis (message broker)
```

### Key Directories
- `backend/app/routers/` - API endpoints (assets, maintenance, auth, ingest)
- `backend/app/models/` - Pydantic models with GeoJSON geometry support
- `backend/app/services/` - Business logic (CSV parsing, ingestion)
- `backend/app/tasks/` - Celery async tasks
- `frontend/src/pages/` - Main views (Dashboard, PublicMap, AdminLogin)
- `frontend/src/components/` - Reusable UI (Map, AssetTable, MaintenanceLog)

## Development Commands

### Docker (Recommended)
```bash
cd infra
cp .env.example .env  # Configure environment
docker-compose up --build
python3 seed_data.py  # Seed sample data
```

### Local Development
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend  
cd frontend && npm install && npm run dev

# Create admin user
python backend/scripts/create_superuser.py
```

## Coding Patterns

### Backend - FastAPI Router Pattern
```python
# backend/app/routers/assets.py pattern:
from app.db.mongodb import get_database
from app.models.asset import Asset, AssetCreate

@router.get("/", response_model=List[Asset])
async def list_assets():
    db = await get_database()
    cursor = db["assets"].find(query)
    # Use Motor async iteration
```

### GeoJSON Geometry Format
Assets store geometry in GeoJSON format. CSV ingestion parses `"TYPE [coords]"` → GeoJSON:
```python
# "POINT [108.25, 15.97]" → {"type": "Point", "coordinates": [108.25, 15.97]}
# Supported: Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon
```

### Frontend - React Query + Leaflet
```typescript
// Data fetching pattern (frontend/src/api.ts):
const { data: assets } = useQuery({ queryKey: ['assets'], queryFn: getAssets });

// Map component uses react-leaflet + MarkerClusterGroup
// Icons defined in frontend/src/utils/mapIcons.tsx by feature_code
```

### JWT Authentication
- Admin login: `POST /api/auth/login` → returns JWT token
- Token stored in `localStorage['access-token']`
- Protected routes use `RequireAuth` wrapper (frontend/src/App.tsx)

## Environment Configuration

| Service | File | Key Variables |
|---------|------|---------------|
| Backend | `backend/.env` | `MONGODB_URL`, `ADMIN_JWT_SECRET`, `ADMIN_DEFAULT_*` |
| Frontend | `frontend/.env` | `VITE_BASE_API_URL`, `VITE_LEADERBOARD_URL` |
| Docker | `infra/.env` | `BACKEND_PORT`, `FRONTEND_PORT`, `CSV_IMPORT_URL` |

## Celery Background Tasks
- Scheduled CSV import runs daily at 2AM UTC (`backend/app/celery_app.py`)
- Manual trigger: `python backend/trigger_import.py`
- Task skips duplicate coordinates to avoid data duplication

## IoT Data Standards
- **Standard API** (`/api/v1/iot`): Simple JSON format for frontend consumption
- **NGSI-LD API** (`/api/v1/ld`): ETSI NGSI-LD format for semantic interoperability
  - Properties: `{"type": "Property", "value": ...}`
  - Relationships: `{"type": "Relationship", "object": "urn:..."}`
  - Context: NGSI-LD core + Schema.org vocabulary
- **SOSA Ontology**: Used only for internal IoT device-to-frontend communication (NOT in public API)

## API Endpoints Quick Reference
- `GET/POST /api/assets/` - List/create infrastructure assets
- `GET/PUT/DELETE /api/assets/{id}` - Single asset operations
- `POST /api/ingest/csv` - Upload CSV file for bulk import
- `GET/POST /api/maintenance/` - Maintenance logs
- `POST /api/auth/login` - Admin authentication
- `GET /api/v1/iot/*` - IoT sensors (standard JSON format)
- `GET /api/v1/ld/*` - IoT sensors & observations (NGSI-LD format)

## Frontend Routes
- `/` - Landing page (HomePage)
- `/map` - Public map view (PublicMap)
- `/admin/login` - Admin login
- `/admin` - Dashboard (protected, requires auth)


Tên của team (copyright): VKU.OneLove

# Hạ tầng hiện tại
- Code đang chạy thẳng trên server
- Triển khai bằng nginx, nếu cần tự chạy lệnh để ls với cat trong nginx
- Backend đang mở https://api.openinfra.space/
