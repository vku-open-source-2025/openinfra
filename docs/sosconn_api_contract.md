# SOSConn API Contract Baseline (Hazards and Emergency Streams)

Status: baseline, contract-first
Version: 1.0
Scope: request and response contracts only (no runtime behavior changes)

## 1. Base Path

All HTTP paths below are relative to:

`/api/v1`

## 2. Hazard Contracts

### 2.1 List Hazards

- Method: `GET`
- Path: `/hazards`
- Auth: not required

Query parameters:

| Name | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `skip` | integer | no | `0` | `>= 0` |
| `limit` | integer | no | `100` | `1..500` |
| `active_only` | boolean | no | `true` | Return only active hazards when true |
| `event_type` | string | no | - | Flood, storm, landslide, fire, earthquake, outage, pollution, drought, other |
| `severity` | string | no | - | low, medium, high, critical |
| `source` | string | no | - | nchmf, vndms, iot, manual, other |
| `district` | string | no | - | District filter |
| `ward` | string | no | - | Ward filter |

Response: `200 OK`

```json
[
  {
    "id": "6802f0c1d72c0d3d0f59d8a0",
    "hazard_id": "HZ-2026-0001",
    "title": "Canh bao ngap do mua lon",
    "description": "Risk of flash flood in low-lying wards",
    "event_type": "flood",
    "severity": "high",
    "source": "nchmf",
    "geometry": {
      "type": "Point",
      "coordinates": [108.2208, 16.0544]
    },
    "affected_polygon": null,
    "intensity_level": 0.82,
    "forecast_confidence": 0.91,
    "affected_population": 2400,
    "district": "Hai Chau",
    "ward": "Binh Hien",
    "detected_at": "2026-04-19T09:00:00Z",
    "ingest_timestamp": "2026-04-19T09:00:04Z",
    "expires_at": "2026-04-19T15:00:00Z",
    "is_active": true,
    "vector_embedding": null,
    "metadata": {
      "provider": "nchmf"
    },
    "created_at": "2026-04-19T09:00:04Z",
    "updated_at": "2026-04-19T09:00:04Z"
  }
]
```

### 2.2 Nearby Hazards

- Method: `GET`
- Path: `/hazards/geo/near`
- Auth: not required

Query parameters:

| Name | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `lat` | number | yes | - | `-90..90` |
| `lng` | number | yes | - | `-180..180` |
| `radius_m` | integer | no | `5000` | `100..200000` |
| `limit` | integer | no | `100` | `1..500` |

Response: `200 OK`

- Same body schema as `GET /hazards`.

### 2.3 Expire Stale Hazards

- Method: `POST`
- Path: `/hazards/expire-stale`
- Auth: required (`Bearer` token, operator role)

Response: `200 OK`

```json
{
  "updated": 7
}
```

Compatibility note:

- Consumers may map `updated` to local alias `expired_count` when needed.

## 3. Emergency Stream Contract

This section defines payload contracts for event stream transport (SSE/WebSocket/message-bus).

### 3.1 Canonical Envelope

```json
{
  "event": "hazard.upsert",
  "event_type": "hazard.upsert",
  "schema_version": "1.0",
  "emitted_at": "2026-04-19T09:12:00Z",
  "request_id": "d9a2f9fd-2a98-4e6d-a6a5-c826c132f2ec",
  "entity_id": "HZ-2026-0001",
  "payload": {},
  "data": {}
}
```

Rules:

- `event` is canonical event name.
- `event_type` is a compatibility alias of `event`.
- `payload` is canonical body.
- `data` is a compatibility alias of `payload`.
- `schema_version` defaults to `1.0`.

### 3.2 Hazard Stream Payload

Model: `HazardStreamEvent`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `stream_type` | string | no | Default `hazard` |
| `action` | string | no | Default `upsert` |
| `hazard_id` | string | no | Canonical hazard identifier |
| `id` | string | no | Legacy/alternate identifier |
| `title` | string | no | Human-readable title |
| `description` | string | no | Optional details |
| `event_type` | string | no | Hazard domain type |
| `severity` | string | no | low/medium/high/critical |
| `source` | string | no | Data source |
| `status` | string | no | Optional status alias for clients |
| `is_active` | boolean | no | Active flag |
| `geometry` | object | no | GeoJSON geometry |
| `district` | string | no | District |
| `ward` | string | no | Ward |
| `detected_at` | datetime | no | Detection timestamp |
| `expires_at` | datetime | no | Expiration timestamp |
| `metadata` | object | no | Free-form dictionary |
| `occurred_at` | datetime | no | Event time, defaults to now |
| `request_id` | string | no | Trace identifier |

### 3.3 Emergency Stream Payload

Model: `EmergencyStreamEvent`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `stream_type` | string | no | Default `emergency` |
| `action` | string | no | Default `upsert` |
| `event_id` | string | no | Canonical emergency event id |
| `emergency_event_id` | string | no | Legacy/alternate event id |
| `id` | string | no | Legacy/alternate identifier |
| `event_code` | string | no | Business code |
| `title` | string | no | Human-readable title |
| `description` | string | no | Optional details |
| `event_type` | string | no | Emergency domain type |
| `severity` | string | no | low/medium/high/critical |
| `status` | string | no | monitoring/active/contained/resolved/canceled |
| `source` | string | no | Signal source |
| `location` | object | no | Geo/location object |
| `affected_asset_ids` | array[string] | no | Asset ids |
| `tags` | array[string] | no | Classification tags |
| `started_at` | datetime | no | Start timestamp |
| `ended_at` | datetime | no | End timestamp |
| `metadata` | object | no | Free-form dictionary |
| `occurred_at` | datetime | no | Event time, defaults to now |
| `request_id` | string | no | Trace identifier |

## 4. Helper Binding

Contract helper and payload schemas are defined in:

- `backend/app/domain/models/contracts.py`

Primary helper:

- `as_stream_envelope(...)`

It normalizes payloads into the canonical envelope and preserves compatibility aliases.
