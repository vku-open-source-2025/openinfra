# Agent: dev08-command-center-ui

Loại: developer subagent
Model đề xuất: GPT-5.3-Codex
Parallel Group: B
Depends on: dev02-emergency-api, dev05-realtime-map

## Mission

Xây UI command center hợp nhất cho chỉ huy: map tactical, timeline, task board, resource board, alert feed, EOP panel.

## Owned Scope

- `frontend/src/routes/admin/`
- `frontend/src/pages/`
- `frontend/src/components/`
- `frontend/src/stores/`

## Responsibilities

- Tạo route `/admin/emergency-center`.
- Tạo dashboard với 6 khối chức năng chính.
- Tích hợp API emergency cho thao tác nhanh.
- Tích hợp realtime status task/resource/alert.
- Tối ưu UX cho desktop/tablet.

## Patch Handoff Contract

```yaml
agent: dev08-command-center-ui
changes:
  - emergency_center_route
  - dashboard_panels
  - api_bindings
  - realtime_status_updates
ux:
  - desktop_ready
  - tablet_ready
tests:
  - ui_flow_tests
status: done
```

## Done Criteria

1. Route mới hoạt động với phân quyền.
2. Dashboard điều hành đầy đủ tác vụ chính.
3. Realtime hiển thị đúng trạng thái.
4. UI ổn định trên desktop/tablet.
5. E2E flow cơ bản pass.
