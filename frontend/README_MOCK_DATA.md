# Mock Data Setup for Asset Lifecycle Management

This document explains how to use mock data for the Asset Lifecycle Management feature before backend endpoints are implemented.

## Overview

Mock data implementations have been added to allow frontend development and testing without waiting for backend API endpoints. The mocks simulate realistic API responses with appropriate delays.

## Enabling Mock Data

To enable mock data, set the environment variable `VITE_USE_MOCK_DATA=true`:

### Option 1: Environment File
Create or update `.env.local`:
```bash
VITE_USE_MOCK_DATA=true
```

### Option 2: Command Line
```bash
VITE_USE_MOCK_DATA=true npm run dev
```

### Option 3: Package.json Script
Add to `package.json`:
```json
{
  "scripts": {
    "dev:mock": "VITE_USE_MOCK_DATA=true vite"
  }
}
```

## Mocked Endpoints

The following endpoints are mocked when `VITE_USE_MOCK_DATA=true`:

### Asset Endpoints
- `GET /assets/{id}/lifecycle` - Returns asset with lifecycle data
- `GET /assets/{id}/health-score` - Returns health score and factors
- `GET /assets/{id}/documents` - Returns list of documents

### Maintenance Endpoints
- `GET /maintenance/asset/{assetId}/history` - Returns filtered maintenance history

### Preventive Maintenance Endpoints
- `GET /assets/{assetId}/preventive-maintenance` - Returns preventive maintenance plan
- `GET /assets/{assetId}/preventive-maintenance/tasks` - Returns upcoming tasks
- `GET /assets/{assetId}/preventive-maintenance/overdue` - Returns overdue tasks

### Incident Endpoints
- `GET /incidents` (with asset_id filter) - Returns incidents for asset

## Mock Data Files

- **Location**: `src/api/mocks/assetLifecycleMocks.ts`
- **Functions**:
  - `mockAssetWithLifecycle(id)` - Mock asset with lifecycle data
  - `mockHealthScore(id)` - Mock health score calculation
  - `mockMaintenanceHistory(assetId)` - Mock maintenance records
  - `mockPreventiveMaintenancePlan(assetId)` - Mock preventive plan
  - `mockUpcomingTasks(assetId)` - Mock upcoming tasks
  - `mockOverdueTasks(assetId)` - Mock overdue tasks
  - `mockIncidents(assetId)` - Mock incidents
  - `mockDocuments(assetId)` - Mock documents

## Customizing Mock Data

To customize mock data, edit `src/api/mocks/assetLifecycleMocks.ts`:

```typescript
// Example: Change health score
export const mockHealthScore = (assetId: string) => ({
  health_score: 95, // Changed from 87
  factors: {
    incident_frequency: 90,
    // ... other factors
  },
});
```

## Removing Mocks

Once backend endpoints are implemented:

1. Set `VITE_USE_MOCK_DATA=false` or remove the environment variable
2. The code will automatically use real API calls
3. Optionally delete `src/api/mocks/assetLifecycleMocks.ts` after testing

## Testing with Mocks

Mock data includes:
- Realistic delays (300-500ms) to simulate network latency
- Proper TypeScript types
- Filtering logic for maintenance history and incidents
- Multiple records for testing pagination and lists

## Notes

- Mock data is only used when `USE_MOCK_DATA` is `true`
- All mock functions return properly typed data
- Network delays are simulated for realistic testing
- Filtering is implemented for maintenance history queries
- Mock data persists across page refreshes (no real backend)
