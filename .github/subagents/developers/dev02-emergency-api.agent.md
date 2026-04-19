# Agent: dev02-emergency-api

Loại: developer subagent
Model đề xuất: GPT-5.3-Codex
Parallel Group: A
Depends on: dev01-domain-model

## Mission

Triển khai API command center cho event, EOP, dispatch, resources và sitrep.

## Owned Scope

- `backend/app/api/v1/routers/`
- `backend/app/domain/services/`
- `backend/app/api/v1/dependencies.py`
- `backend/app/api/v1/routers/__init__.py`

## Responsibilities

- Tạo router `/api/v1/emergency/events`.
- Tạo router `/api/v1/emergency/eop`.
- Tạo router `/api/v1/emergency/dispatch`.
- Tạo router `/api/v1/emergency/resources`.
- Tạo router `/api/v1/emergency/sitrep`.
- Áp dụng RBAC cho từng endpoint nhạy cảm.

## Patch Handoff Contract

```yaml
agent: dev02-emergency-api
changes:
  - emergency_routers_added
  - services_connected
  - rbac_enforced
tests:
  - api_contract_passed
  - auth_scope_passed
open_issues: []
next_agents:
  - dev08-command-center-ui
  - api-integration.tester
status: done
```

## Done Criteria

1. Endpoint emergency hoạt động đúng contract.
2. Router đã đăng ký vào API v1.
3. Role nhạy cảm được bảo vệ.
4. Swagger hiển thị đầy đủ.
5. Integration test API pass.
