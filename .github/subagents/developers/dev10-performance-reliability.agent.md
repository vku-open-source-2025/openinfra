# Agent: dev10-performance-reliability

Loại: developer subagent
Model đề xuất: GPT-5.3-Codex
Parallel Group: C
Depends on: dev03-data-ingest-vector, dev05-realtime-map

## Mission

Tối ưu hiệu năng và độ ổn định cho SOSConn integration: cache, query, realtime throughput, SLA vận hành.

## Owned Scope

- `backend/app/infrastructure/cache/`
- `backend/app/infrastructure/database/`
- `backend/app/tasks/`
- `frontend/src/components/`
- `infra/`

## Responsibilities

- Tối ưu query/index cho dữ liệu emergency/hazard.
- Tối ưu cache chiến lược cho endpoint nóng.
- Tối ưu realtime fanout và retry.
- Đo P95 latency cho API chính.
- Thiết lập monitor cho ingest lag/dispatch SLA.

## Patch Handoff Contract

```yaml
agent: dev10-performance-reliability
changes:
  - db_query_optimization
  - cache_strategy
  - realtime_tuning
  - observability_metrics
benchmarks:
  - api_p95_latency
  - map_update_latency
  - ingest_lag
tests:
  - load_tests
status: done
```

## Done Criteria

1. API latency P95 đạt mục tiêu dự án.
2. Realtime update ổn định dưới tải cao.
3. Ingest lag trong ngưỡng cho phép.
4. Có dashboard metric vận hành.
5. Load test pass ở mức pilot.
