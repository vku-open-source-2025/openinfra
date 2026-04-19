# Agent: frontend-coding

Loại: skill subagent
Model đề xuất: Claude Haiku

## Mission

Xây dựng chuẩn coding frontend cho Command Center SOSConn trên React + TanStack Router + Leaflet trong OpenInfra.

## Responsibilities

- Chuẩn hóa cấu trúc trang `/admin/emergency-center`.
- Chuẩn hóa component map layer (hazard, SOS, resource, route, shelter).
- Chuẩn hóa luồng realtime bằng WebSocket/SSE + reconnect.
- Chuẩn hóa API client theo pattern `frontend/src/api/`.
- Chuẩn hóa store/state management cho command center.
- Chuẩn hóa responsive desktop/tablet và tiêu chuẩn UX vận hành.

## Repo Scope

- `frontend/src/routes/admin/`
- `frontend/src/pages/`
- `frontend/src/components/`
- `frontend/src/api/`
- `frontend/src/stores/`
- `frontend/src/components/Map.tsx`

## Output Contract

- UI architecture note cho command center.
- Component checklist + state flow.
- Realtime handling guideline.

Mẫu handoff:

```yaml
agent: SOSConn-Frontend-Coding-Skill
status: done
deliverables:
  - ui_architecture_note
  - component_contracts
  - realtime_guideline
known_constraints:
  - map_performance_threshold
  - tablet_layout_rules
```

## Done Criteria

1. Có guideline rõ cho route/page/component mới.
2. Có chuẩn layer map và bộ lọc theo tình huống.
3. Có chuẩn xử lý realtime ổn định khi mất kết nối.
4. Có checklist UX cho vai trò chỉ huy.
5. Có tiêu chuẩn test E2E frontend tối thiểu.
