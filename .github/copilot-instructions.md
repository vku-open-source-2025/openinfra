# OpenInfra — Complete AI Agent Skill Set

> **Team**: VKU.OneLove  
> **Domain**: Quản lý hạ tầng GIS (Infrastructure Management with GIS)  
> **Production**: https://openinfra.space | API: https://api.openinfra.space

---

## 1. System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Cloudflare Tunnel (f3de2209)                   │
│  openinfra.space → nginx:443 → frontend:5173                    │
│  api.openinfra.space → nginx:443 → backend:8000                 │
│  mcp.openinfra.space → nginx:443 → mcp-server:8000              │
│  contribapi.openinfra.space → localhost:8000 (datacollector)     │
│  contribution.openinfra.space → localhost:5175 (datacollector)   │
│  ssh.openinfra.space → localhost:22                              │
│  n8n.openinfra.space → localhost:8080                            │
└──────────────────────────────────────────────────────────────────┘

┌─ Main Stack (infra/docker-compose.yml) ──────────────────────────┐
│                                                                   │
│  Frontend (React 19 + Vite + TanStack Router)                    │
│      ↓ axios (httpClient.ts) → VITE_BASE_API_URL                │
│  Nginx (SSL termination, rate limiting 30r/s)                    │
│      ↓                                                            │
│  Backend (FastAPI + Pydantic v2)                                 │
│      ↓ Motor (async) / PyMongo (sync in Celery)                  │
│  MongoDB (:27017)                                                │
│      ↑                                                            │
│  Celery Worker + Beat → Redis (:6379)                            │
│                                                                   │
│  IoT Pipeline:                                                    │
│  ESP8266 → IoT Producer (HTTP/MQTT) → Kafka → IoT Consumer → DB │
│                                                                   │
│  MCP Server (FastMCP, SSE) — read-only Open Data API docs        │
└──────────────────────────────────────────────────────────────────┘

┌─ Datacollector Stack (datacollector/docker-compose.yml) ─────────┐
│  Frontend (React 18 + Vite, production build via serve)          │
│  Backend (FastAPI, port 8000 → tunnel contribapi)                │
│  MongoDB (:27018 → openinfra_gis DB)                             │
│  ETL: Celery task syncs approved contributions → main DB (6h)    │
└──────────────────────────────────────────────────────────────────┘
```

### Port Mapping

| Service              | Internal | External | Domain                          |
|----------------------|----------|----------|---------------------------------|
| Main Frontend        | 5173     | 5174     | openinfra.space                 |
| Main Backend         | 8000     | 8001     | api.openinfra.space             |
| MCP Server           | 8000     | 8003     | mcp.openinfra.space             |
| IoT Producer         | 8001     | 8002     | —                               |
| MongoDB (main)       | 27017    | 27017    | —                               |
| MongoDB (datacoll.)  | 27017    | 27018    | —                               |
| Datacollector API    | 8000     | 8000     | contribapi.openinfra.space      |
| Datacollector UI     | 5173     | 5175     | contribution.openinfra.space    |
| Mongo Express        | 8081     | 8081     | — (internal only)               |
| n8n                  | 5678     | 8080     | n8n.openinfra.space             |

---

## 2. Directory Structure & Key Files

```
openinfra/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app, lifespan, CORS
│   │   ├── celery_app.py             # Celery config + beat schedule
│   │   ├── core/
│   │   │   ├── config.py             # Settings (pydantic-settings, .env)
│   │   │   ├── exceptions.py         # Custom exceptions
│   │   │   └── logging.py            # Structured logging
│   │   ├── api/v1/routers/
│   │   │   ├── __init__.py           # Router aggregation (api_router)
│   │   │   ├── assets.py             # CRUD /assets
│   │   │   ├── auth.py               # JWT login /auth
│   │   │   ├── maintenance.py        # /maintenance
│   │   │   ├── ingest.py             # CSV upload /ingest
│   │   │   ├── iot.py                # /iot sensors (JSON)
│   │   │   ├── linked_data.py        # /ld NGSI-LD format
│   │   │   ├── incidents.py          # /incidents (AI verification)
│   │   │   ├── alerts.py             # /alerts
│   │   │   ├── budgets.py            # /budgets
│   │   │   ├── reports.py            # /reports
│   │   │   ├── geo.py                # /geo geospatial queries
│   │   │   ├── map_proxy.py          # /map VietMap tile proxy
│   │   │   ├── notifications.py      # /notifications
│   │   │   ├── users.py              # /users management
│   │   │   ├── public.py             # /public open data
│   │   │   └── ai_agent.py           # AI chat agent (Gemini)
│   │   ├── domain/                    # DDD Domain Layer
│   │   │   ├── models/               # Pydantic domain entities
│   │   │   ├── repositories/         # Abstract repository interfaces
│   │   │   ├── services/             # Domain business logic
│   │   │   └── value_objects/         # coordinates, location, specs
│   │   ├── infrastructure/            # DDD Infrastructure Layer
│   │   │   ├── database/             # MongoDB connection + concrete repos
│   │   │   ├── cache/                # Redis caching
│   │   │   ├── external/             # Gemini AI, OSM Nominatim
│   │   │   ├── storage/              # File storage (local/MinIO)
│   │   │   ├── security/             # JWT, password hashing
│   │   │   ├── messaging/            # Kafka producer
│   │   │   ├── notifications/        # Push notifications (FCM)
│   │   │   └── reports/              # Report generation (PDF)
│   │   ├── models/                    # Legacy Pydantic models (asset, iot, maintenance)
│   │   ├── services/                  # Legacy services (CSV, AI agent, Kafka consumer)
│   │   ├── tasks/                     # Celery tasks
│   │   │   ├── csv_import.py         # Scheduled CSV import
│   │   │   ├── contribution_etl.py   # Sync contributions → main DB
│   │   │   ├── sensor_monitoring.py  # Offline detection, aggregation, risk AI
│   │   │   ├── report_generation.py  # Scheduled report gen
│   │   │   └── content_filter.py     # Inappropriate content filter
│   │   └── middleware/                # Error handler, logging middleware
│   ├── scripts/                       # Admin utilities
│   │   ├── create_superuser.py
│   │   ├── create_admins.py          # Bulk admin creation
│   │   ├── seed_db.py, seed_*.py
│   │   └── migrate_sosa_metadata.py
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── main.tsx                   # React 19 entry
│   │   ├── routes/                    # TanStack Router file-based routes
│   │   │   ├── __root.tsx
│   │   │   ├── index.tsx              # / HomePage
│   │   │   ├── map.tsx               # /map PublicMap
│   │   │   ├── login.tsx             # /login
│   │   │   ├── admin.tsx             # /admin layout (protected)
│   │   │   ├── admin/                # /admin/* nested routes
│   │   │   └── asset.$id.tsx         # /asset/:id detail
│   │   ├── api/                       # API client modules per domain
│   │   ├── components/                # Reusable UI components
│   │   │   ├── Map.tsx               # Leaflet map (VietMap tiles via proxy)
│   │   │   ├── AIChatWidget.tsx      # AI assistant (WebSocket)
│   │   │   ├── ui/                   # shadcn/ui primitives
│   │   │   └── ...                   # Domain-specific components
│   │   ├── pages/                     # Page components
│   │   │   ├── AssetMapView.tsx      # Full map view with filters
│   │   │   ├── Dashboard.tsx
│   │   │   └── iot/, incidents/, ...
│   │   ├── lib/httpClient.ts          # Axios instance + interceptors
│   │   ├── stores/                    # Zustand stores (auth, app)
│   │   ├── hooks/                     # Custom hooks (IoT, PWA, debounce)
│   │   ├── types/                     # TypeScript interfaces per domain
│   │   └── utils/                     # mapIcons, formatters
│   └── e2e/                           # Playwright E2E tests
├── datacollector/                     # Contribution data collection app
│   ├── backend/                       # FastAPI (separate from main)
│   │   ├── main.py                   # Features CRUD, contributions, exports, tile proxy
│   │   └── models.py                 # MongoDB models
│   ├── frontend/                      # React 18 + Vite (production build)
│   │   ├── src/pages/               # ContributorView, AdminView, Leaderboard
│   │   └── src/components/Map/      # MapView (VietMap via proxy)
│   └── docker-compose.yml
├── infra/
│   ├── docker-compose.yml             # Main orchestration (12 services)
│   ├── nginx/nginx.conf               # Reverse proxy + SSL
│   ├── certbot/                       # Let's Encrypt via Cloudflare DNS
│   ├── .env                           # All environment variables
│   └── seed_data.py, seed_*.py       # Data seeding scripts
├── iot_integration/
│   ├── producer/                      # HTTP/MQTT → Kafka bridge
│   └── esp8266/                       # ESP8266 firmware (drainage sensor)
├── mcp-server/                        # MCP Server (FastMCP, read-only)
├── llm-service/                       # LLM service (FastAPI, GitHub Copilot)
└── .notes/accounts.md                 # Admin credentials (gitignored)
```

---

## 3. Backend Patterns

### 3.1 Domain-Driven Design (DDD)

```python
# Layer flow: Router → Service → Repository → MongoDB

# Domain Model (backend/app/domain/models/asset.py)
class Asset(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    asset_code: str
    name: str
    feature_type: str              # e.g., "tram_dien", "cot_dien"
    status: AssetStatus            # Enum: operational/maintenance/damaged/retired
    geometry: dict                 # GeoJSON: {"type": "Point", "coordinates": [lng, lat]}
    location: Optional[Location]   # Value object with address, ward, district

# Repository Interface (backend/app/domain/repositories/asset_repository.py)
class AssetRepository(ABC):
    @abstractmethod
    async def create(self, asset_data: dict) -> Asset: ...
    @abstractmethod
    async def find_by_id(self, asset_id: str) -> Optional[Asset]: ...

# Domain Service (backend/app/domain/services/asset_service.py)
class AssetService:
    def __init__(self, asset_repository: AssetRepository, audit_service=None):
        self.repository = asset_repository
    async def create_asset(self, asset_data: AssetCreate) -> Asset: ...

# Infrastructure Repository (backend/app/infrastructure/database/repositories/)
class MongoAssetRepository(AssetRepository):
    async def create(self, asset_data: dict) -> Asset:
        db = self.db_client[self.db_name]
        result = await db["assets"].insert_one(asset_data)
        ...
```

### 3.2 Router Pattern

```python
# backend/app/api/v1/routers/assets.py
from app.domain.services.asset_service import AssetService

@router.get("/", response_model=List[Asset])
async def list_assets(skip: int = 0, limit: int = 100):
    service = AssetService(repository=MongoAssetRepository())
    return await service.list_assets(skip=skip, limit=limit)
```

All routers registered in `backend/app/api/v1/routers/__init__.py`:
```python
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
# ... etc (14 router groups)
```

Mounted in `main.py`:
```python
app.include_router(api_router, prefix="/api/v1")
```

### 3.3 MongoDB Patterns

- **Driver**: Motor (async) for FastAPI, PyMongo (sync) for Celery tasks
- **Database**: `openinfra` (main), `openinfra_gis` (datacollector)
- **Collections**: `assets`, `maintenance_records`, `iot_sensors`, `sensor_readings`, `incidents`, `alerts`, `budgets`, `reports`, `users`, `notifications`, `audit_logs`
- **GeoJSON fields**: Always `{"type": "Point", "coordinates": [longitude, latitude]}`
- **ObjectId handling**: Serialized as string with `field_serializer`

### 3.4 GeoJSON Geometry Format

```python
# CSV ingestion parses: "POINT [108.25, 15.97]" → GeoJSON
{"type": "Point", "coordinates": [108.25, 15.97]}
{"type": "LineString", "coordinates": [[108.1, 15.9], [108.2, 16.0]]}
{"type": "Polygon", "coordinates": [[[108.1, 15.9], [108.2, 15.9], [108.2, 16.0], [108.1, 15.9]]]}
# Supported: Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon
```

### 3.5 Authentication

- JWT tokens via `python-jose`
- Login: `POST /api/v1/auth/login` → `{"access_token": "...", "token_type": "bearer"}`
- Config: `ADMIN_JWT_SECRET`, `ADMIN_JWT_ALGORITHM=HS256`, `ADMIN_JWT_EXPIRE_MINUTES=1440`
- Frontend stores token in Zustand store (`authStore.ts`), sends via `Authorization: Bearer <token>`

### 3.6 VietMap Tile Proxy

```python
# backend/app/api/v1/routers/map_proxy.py
@router.get("/tiles/{z}/{x}/{y}")   # Proxies to VietMap, appends API key server-side
@router.get("/config")               # Returns tile URL config (no key exposed)
```

Frontend fetches `/api/v1/map/config` → gets relative tileUrl → prepends API origin:
```typescript
const apiOrigin = BASE_API.replace(/\/api\/v1$/, '');
cfg.tileUrl = `${apiOrigin}${cfg.tileUrl}`;
```

### 3.7 Celery Tasks & Schedule

| Task | Schedule | Purpose |
|------|----------|---------|
| `check_sensor_offline_status` | Every 15 min | Detect offline IoT sensors |
| `aggregate_sensor_data_hourly` | Hourly | Aggregate sensor readings |
| `ai_automated_risk_detection` | Every 15 min | AI risk analysis on sensor data |
| `generate_scheduled_reports` | Daily midnight | Auto-generate reports |
| `filter_inappropriate_content` | Hourly | Content moderation |
| `sync_contributions` | Every 6 hours | ETL: datacollector → main DB |

### 3.8 IoT Data Pipeline

```
ESP8266 sensor → HTTP POST / MQTT publish
    → IoT Producer (FastAPI, bridges to Kafka)
    → Kafka topic: iot-sensor-data
    → IoT Consumer (Python, stores in MongoDB)
    → Backend API serves via /api/v1/iot (JSON) and /api/v1/ld (NGSI-LD)
```

**NGSI-LD Format** (ETSI standard):
```json
{
  "id": "urn:ngsi-ld:Sensor:temp-001",
  "type": "Sensor",
  "temperature": {"type": "Property", "value": 25.5},
  "location": {"type": "GeoProperty", "value": {"type": "Point", "coordinates": [108.2, 16.0]}}
}
```

### 3.9 AI Integration (Gemini)

- **Text Embedding**: `text-embedding-004` for semantic search / duplicate detection
- **Vision**: `gemini-2.5-flash` for incident image verification
- **Chat Agent**: `gemini-2.5-flash` (stable) or `gemini-2.0-flash` (Live API)
- **Duplicate Detection**: Cosine similarity on embeddings, configurable thresholds
- **AI Chat Widget**: WebSocket-based, integrated into admin dashboard

---

## 4. Frontend Patterns

### 4.1 Tech Stack

- **React 19** + **TypeScript**
- **TanStack Router** (file-based routing in `src/routes/`)
- **TanStack React Query** for server state
- **Zustand** for client state (auth, app)
- **Leaflet** + **react-leaflet** for maps (with VietMap tiles)
- **Tailwind CSS v4** + **shadcn/ui** components
- **Axios** via `httpClient` (centralized interceptors)
- **Lucide React** + **Font Awesome** icons
- **Vite** bundler

### 4.2 HTTP Client

```typescript
// frontend/src/lib/httpClient.ts
export const httpClient = axios.create({
    baseURL: getApiBaseUrl(),  // VITE_BASE_API_URL || "/api/v1"
    timeout: 30000,
});
// Auto-attaches JWT from Zustand authStore
// Auto-handles 401 → logout + redirect
```

### 4.3 API Module Pattern

```typescript
// frontend/src/api/assets.ts
export const assetsApi = {
    list: async (params?: AssetListParams): Promise<Asset[]> => {
        const response = await httpClient.get<Asset[]>("/assets", { params });
        return response.data;
    },
    getById: async (id: string): Promise<Asset> => { ... },
    create: async (data: AssetCreateRequest): Promise<Asset> => { ... },
};
```

### 4.4 Route Structure

```
/                    → HomePage (landing)
/map                 → PublicMap (AssetMapView)
/login               → LoginPage
/register            → RegisterPage
/about               → AboutUs
/docs                → ApiDocsPage
/asset/:id           → AssetDetailPage
/admin               → Dashboard (protected)
/admin/*             → Admin sub-routes (assets, incidents, IoT, etc.)
/technician          → Technician portal
/public/*            → Public data views
```

### 4.5 Map Component

```typescript
// Uses vanilla Leaflet (L.map) NOT react-leaflet <MapContainer>
// Tile config fetched from backend: GET /api/v1/map/config
fetchTileConfig().then((cfg) => {
    // Prepend API origin for cross-origin tile proxy
    if (!cfg.tileUrl.startsWith('http')) {
        const apiOrigin = BASE_API.replace(/\/api\/v1$/, '');
        cfg.tileUrl = `${apiOrigin}${cfg.tileUrl}`;
    }
    L.tileLayer(cfg.tileUrl, { attribution: cfg.attribution, maxZoom: cfg.maxZoom }).addTo(map);
});
```

---

## 5. Datacollector (Contribution System)

Separate app for crowdsourced infrastructure data collection.

### 5.1 Architecture

- **Backend**: FastAPI (single `main.py`), MongoDB `openinfra_gis` DB
- **Frontend**: React 18 + Vite, **production build** (`npm run build` → `serve -s dist`)
  - ⚠️ Dev mode causes React duplicate instance errors via Docker; always use production build
- **API Base**: `https://contribapi.openinfra.space`
- **UI**: `https://contribution.openinfra.space`

### 5.2 Key Endpoints

```
GET  /api/features                    # All approved features (GeoJSON FeatureCollection)
POST /api/features                    # Admin: create feature directly
POST /api/contributions               # User: submit for review
GET  /api/contributions               # Admin: list pending
PUT  /api/contributions/:id/approve   # Admin: approve → becomes feature
GET  /api/export_csv?types=...        # Export as CSV (consumed by main ETL)
GET  /api/leaderboard                 # Top contributors
GET  /api/map/config                  # VietMap tile config
GET  /api/map/tiles/{z}/{x}/{y}       # Tile proxy
```

### 5.3 ETL Pipeline

```python
# backend/app/tasks/contribution_etl.py
# Runs every 6 hours, syncs approved features → main "assets" collection
# - Connects to contrib MongoDB via CONTRIB_MONGO_URL
# - Normalizes Vietnamese feature_codes
# - Deduplicates via _contrib_id field
```

### 5.4 Docker Notes

```yaml
# datacollector/docker-compose.yml
frontend:
  # MUST use production build (Dockerfile: npm run build + serve -s dist)
  # Do NOT use dev mode with bind mounts — causes React duplicate instance error
  # No volumes: (all baked into image)
```

---

## 6. Infrastructure & Deployment

### 6.1 SSL & Reverse Proxy

- **Nginx** terminates SSL (Let's Encrypt via Cloudflare DNS challenge)
- **Wildcard cert**: `openinfra.space` covers all subdomains
- **Rate limiting**: 30 req/s with burst=50 on API
- **WebSocket support**: For AI chat agent and SSE (MCP)

### 6.2 Cloudflare Tunnel

```yaml
# ~/.cloudflared/config-openinfra.yml
tunnel: f3de2209-ef7e-4f10-abbf-39a817f2c472
# Routes: openinfra.space, api.*, mcp.*, ssh.*, n8n.*, contribapi.*, contribution.*
# Main domains → nginx:443 (noTLSVerify: true)
# Datacollector → localhost:8000/5175 directly
```

- No port forwarding needed — tunnel maintains outbound connection

### 6.3 Cloudflare DNS

```bash
# Manual DNS update via infra/cloudflare-dns-setup.sh
# Updates Cloudflare DNS A records via CF_API_TOKEN
# Records: @ api mcp (CF_RECORDS env var)
```

### 6.4 Environment Variables

```bash
# infra/.env — Key variables
MONGODB_URL=mongodb://mongo:27017
DATABASE_NAME=openinfra
REDIS_URL=redis://redis:6379/0
BACKEND_PORT=8001
FRONTEND_PORT=5174
VITE_BASE_API_URL=https://api.openinfra.space/api/v1
VITE_VIETMAP_API_KEY=<key>
CSV_IMPORT_URL=https://contribapi.openinfra.space/api/export_csv?types=...
GEMINI_API_KEY=<key>
CF_API_TOKEN=<token>  CF_ZONE_ID=<zone>  CF_DOMAIN=openinfra.space
```

### 6.5 Docker Commands

```bash
# Main stack
cd infra && docker compose up -d --build
cd infra && docker compose restart <service>
cd infra && docker compose logs <service> --tail 50

# Datacollector
cd datacollector && docker compose up -d --build

# Seed data
cd infra && python3 seed_data.py

# Create admin users
docker exec -it infra-backend-1 python scripts/create_admins.py
```

---

## 7. API Endpoints Reference

### Main API (`https://api.openinfra.space/api/v1`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/login` | — | JWT login |
| POST | `/auth/register` | — | User registration |
| GET | `/assets` | — | List all assets |
| POST | `/assets` | JWT | Create asset |
| GET | `/assets/{id}` | — | Get asset by ID |
| PUT | `/assets/{id}` | JWT | Update asset |
| DELETE | `/assets/{id}` | JWT | Delete asset |
| POST | `/ingest/csv` | JWT | Upload CSV for bulk import |
| GET/POST | `/maintenance` | JWT | Maintenance records |
| GET/POST | `/incidents` | JWT | Incident reports (AI-verified) |
| GET/POST | `/alerts` | JWT | Alert management |
| GET/POST | `/budgets` | JWT | Budget tracking |
| GET | `/reports` | JWT | Generated reports |
| GET | `/iot/sensors` | — | IoT sensors (JSON) |
| GET | `/iot/sensors/{id}/readings` | — | Sensor readings |
| GET | `/ld/entities` | — | NGSI-LD entities |
| GET | `/geo/nearby` | — | Geospatial proximity search |
| GET | `/public/assets` | — | Open data API |
| GET | `/map/config` | — | VietMap tile config |
| GET | `/map/tiles/{z}/{x}/{y}` | — | Tile proxy |
| POST | `/notifications` | JWT | Send notifications |
| WS | `/ws/chat` | JWT | AI agent chat |

---

## 8. Data Models (Key Collections)

### assets
```json
{
  "_id": "ObjectId",
  "asset_code": "TD-001",
  "name": "Trạm điện Hải Châu",
  "feature_type": "tram_dien",
  "feature_code": "TD",
  "status": "operational",
  "condition": "good",
  "geometry": {"type": "Point", "coordinates": [108.2, 16.0]},
  "location": {"address": "...", "ward": "...", "district": "..."},
  "specifications": {},
  "installed_date": "2024-01-15",
  "lifecycle_stage": "operational"
}
```

### Feature Types (Vietnamese)
| Code | feature_type | Description |
|------|-------------|-------------|
| TD | tram_dien | Trạm điện |
| CD | cot_dien | Cột điện |
| DOD | duong_ong_dien | Đường ống điện |
| DD | den_duong | Đèn đường |
| DGT | den_giao_thong | Đèn giao thông |
| CTN | cong_thoat_nuoc | Cống thoát nước |
| ODN | ong_dan_nuoc | Ống dẫn nước |
| TCC | tru_chua_chay | Trụ chữa cháy |
| TS | tram_sac | Trạm sạc |

### iot_sensors
```json
{
  "_id": "ObjectId",
  "sensor_id": "temp-001",
  "name": "Temperature Sensor Block A",
  "type": "temperature",
  "location": {"type": "Point", "coordinates": [108.2, 16.0]},
  "status": "active",
  "last_reading": {"value": 25.5, "unit": "°C", "timestamp": "..."}
}
```

---

## 9. Troubleshooting Knowledge

### React Duplicate Instance (Datacollector)
- **Symptom**: `Invalid hook call` + `Cannot read properties of null (reading 'useState')`
- **Cause**: Vite dev mode + Docker bind mount + anonymous volume creates separate React module instances
- **Fix**: Use production build (`npm run build` → `serve -s dist`), remove bind mounts + anonymous volumes

### Map Tiles Not Loading (Main Site)
- **Symptom**: White/blank map on `openinfra.space/map`
- **Cause**: `/api/v1/map/config` returns relative tileUrl, but frontend is on different origin than API
- **Fix**: Frontend prepends API origin to relative tileUrl before passing to Leaflet

### DNS Issues
- **ISP DNS negative cache**: After adding new CNAME, local ISP DNS may cache NXDOMAIN for up to 30 min
- **Test**: `curl --resolve domain:443:127.0.0.1 https://domain/` to bypass DNS
- **Cloudflare Tunnel**: No need for A records if using tunnel — just add CNAME → tunnel UUID

### Docker Volume Issues
- **Stale anonymous volumes**: Use `docker compose up -d --build -V` to recreate anonymous volumes
- **Bind mount node_modules**: Either install on host (no anonymous volume) or use anonymous volume (don't mix)

---

## 10. Development Workflow

### Adding a New Backend Router

1. Create router file: `backend/app/api/v1/routers/new_feature.py`
2. Define domain model: `backend/app/domain/models/new_feature.py`
3. Define repository interface: `backend/app/domain/repositories/new_feature_repository.py`
4. Implement MongoDB repository: `backend/app/infrastructure/database/repositories/new_feature_repo.py`
5. Create domain service: `backend/app/domain/services/new_feature_service.py`
6. Register in `backend/app/api/v1/routers/__init__.py`

### Adding a New Frontend Page

1. Create route file: `frontend/src/routes/new-page.tsx`
2. Create page component: `frontend/src/pages/NewPage.tsx`
3. Add API client: `frontend/src/api/newFeature.ts`
4. Add types: `frontend/src/types/newFeature.ts`
5. TanStack Router auto-generates `routeTree.gen.ts`

### Adding a Celery Task

1. Create task file: `backend/app/tasks/new_task.py`
2. Add to `includes` in `backend/app/celery_app.py`
3. Add schedule to `app.conf.beat_schedule`
4. Restart `celery-worker` and `celery-beat` containers

---

## 11. Hạ tầng hiện tại

- Code chạy trực tiếp trên server (không qua CI/CD)
- Triển khai bằng Docker Compose + Nginx + Cloudflare Tunnel
- SSL: Let's Encrypt wildcard cert via Cloudflare DNS challenge
- Tunnel config: `~/.cloudflared/config-openinfra.yml`
- Nếu cần thay đổi nginx: `docker exec infra-nginx-1 cat /etc/nginx/nginx.conf`
- Backend API docs: https://api.openinfra.space/docs (FastAPI Swagger UI)
- MCP Server: https://mcp.openinfra.space (SSE endpoint cho AI assistants)

Tên của team (copyright): VKU.OneLove
