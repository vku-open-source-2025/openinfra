# Data Seeding Guide

This document explains how fake data is generated in the Infrastructure Management System.

## Overview

The system uses **two approaches** for data generation:

1. **Database Seeding** (Persistent) - Real data stored in MongoDB
2. **Frontend Simulation** (In-Memory) - Temporary data generated on the client

---

## 1. Database Seeding (Persistent Data)

### What Gets Seeded:
- ✅ **Assets** (from CSV file)
- ✅ **Maintenance Logs** (randomly generated)

### Two Methods Available:

#### Method A: API-Based Seeding (Current)
**File:** `infra/seed_data.py`

This script uses the FastAPI endpoints to upload data:
```bash
cd infra
python seed_data.py
```

**How it works:**
1. Uploads CSV via `/api/ingest/csv` endpoint
2. Fetches assets via `/api/assets/` endpoint
3. Creates maintenance logs via `/api/maintenance/` endpoint

**Pros:**
- Tests the API endpoints
- Works with authentication if enabled
- Validates data through Pydantic models

**Cons:**
- Requires the backend to be running
- Slower (HTTP overhead)

---

#### Method B: Direct MongoDB Migration (New)
**File:** `infra/migrate_seed_data.py`

This script directly inserts data into MongoDB:

```bash
# Install dependencies
pip install pymongo pandas

# Run migration
cd infra
python migrate_seed_data.py
```

**How it works:**
1. Connects directly to MongoDB
2. Clears existing collections
3. Parses CSV and inserts assets
4. Generates and inserts maintenance logs
5. Creates database indexes

**Pros:**
- ✅ Much faster (direct DB access)
- ✅ Can run without backend
- ✅ Creates indexes automatically
- ✅ Provides detailed summary

**Cons:**
- Bypasses API validation
- Requires MongoDB connection

---

## 2. Frontend Simulation (In-Memory Data)

### What Gets Simulated:
- ⚡ **IoT Status Updates** (Online/Offline)
- 📅 **Calendar Events** (for demo purposes)
- 🚨 **Real-time Alerts**

### How It Works:

#### IoT Simulation
**File:** `frontend/src/hooks/useIoT.ts`

```typescript
// Randomly changes asset status every 2 seconds
const { assetsWithStatus, alerts } = useIoT(assets);
```

**Features:**
- Assets randomly go offline (1% chance per update)
- Offline assets come back online (10% chance)
- Generates live alerts when assets go offline
- Updates every 2 seconds

#### Calendar Events
**File:** `frontend/src/pages/Dashboard.tsx`

```typescript
// Generates 50 fake calendar events
const fakeCalendarLogs = useMemo(() => {
  // Creates events ±30 days from today
  // Random statuses: Pending, In Progress, Completed
}, [initialAssets]);
```

**Why in-memory?**
- Demo purposes only
- No need to persist calendar data
- Regenerates on page refresh

---

## Comparison Table

| Feature | API Seeding | Direct Migration | Frontend Simulation |
|---------|-------------|------------------|---------------------|
| **Speed** | Slow | Fast | Instant |
| **Persistence** | ✅ Yes | ✅ Yes | ❌ No |
| **Requires Backend** | ✅ Yes | ❌ No | ❌ No |
| **Validates Data** | ✅ Yes | ⚠️ Partial | ❌ No |
| **Creates Indexes** | ❌ No | ✅ Yes | N/A |
| **Use Case** | Testing API | Production Setup | UI Demo |

---

## Recommended Workflow

### For Development:
```bash
# 1. Start services
cd infra
docker-compose up -d

# 2. Seed database (choose one)
python seed_data.py          # API-based
# OR
python migrate_seed_data.py  # Direct migration (faster)

# 3. Access application
open http://localhost
```

### For Production:
```bash
# Use the migration script for initial setup
python migrate_seed_data.py

# Frontend simulation will work automatically
```

---

## Data Statistics

After running the migration, you'll get:

- **~1000 Assets** (from CSV)
- **~400-800 Maintenance Logs** (40% of assets, 1-3 logs each)
- **Real-time IoT Updates** (frontend simulation)
- **50 Calendar Events** (frontend simulation)

---

## Customization

### To modify fake data:

1. **Asset Data**: Edit `sample_data.csv`
2. **Maintenance Logs**: Edit the arrays in the migration script:
   ```python
   statuses = ["Pending", "In Progress", "Completed", "Scheduled"]
   technicians = ["Nguyen Van A", "Tran Thi B", ...]
   descriptions = ["Routine inspection", ...]
   ```
3. **IoT Behavior**: Edit `frontend/src/hooks/useIoT.ts`
4. **Calendar Events**: Edit `frontend/src/pages/Dashboard.tsx`

---

## Troubleshooting

### "No assets found"
- Check if `sample_data.csv` exists
- Verify CSV format (geometry column)

### "Connection refused"
- Ensure MongoDB is running: `docker-compose ps`
- Check MongoDB URL in script

### "Duplicate key error"
- Run `clear_collections()` first
- Or manually: `db.assets.deleteMany({})`

---

## Next Steps

For a production system, consider:
- [ ] Replace CSV with real data source
- [ ] Add data validation rules
- [ ] Implement incremental updates
- [ ] Add rollback mechanism
- [ ] Create backup before migration
