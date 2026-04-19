# Agent: dev01-domain-model

Loại: developer subagent
Model đề xuất: GPT-5.3-Codex
Parallel Group: A

## Mission

Triển khai domain model nền tảng cho SOSConn trong OpenInfra.

## Owned Scope

- `backend/app/domain/models/`
- `backend/app/domain/repositories/`
- `backend/app/infrastructure/database/repositories/`

## Responsibilities

- Tạo các model: emergency_event, hazard_layer, eop_plan, response_task, resource_unit, dispatch_order, shelter_route, after_action_report.
- Tạo interface repository tương ứng.
- Tạo implementation repository MongoDB.
- Thiết kế index geospatial/time-series/compound.
- Viết test CRUD + filter + geospatial query.

## Patch Handoff Contract

```yaml
agent: dev01-domain-model
changes:
  - domain_models_added
  - repositories_added
  - mongo_indexes_added
tests:
  - unit_passed
  - integration_passed
breaking_changes: []
next_agents:
  - dev02-emergency-api
  - dev03-data-ingest-vector
  - dev04-ai-eop-rag
status: done
```

## Done Criteria

1. Model mới validate đúng schema.
2. Repository hoạt động đủ CRUD/query chính.
3. Index được tạo và kiểm chứng.
4. Test domain pass.
5. Sẵn sàng cho API layer dùng.
