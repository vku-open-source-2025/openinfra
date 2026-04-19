# Agent: dev05-realtime-map

Loại: developer subagent
Model đề xuất: GPT-5.3-Codex
Parallel Group: B
Depends on: dev01-domain-model

## Mission

Tích hợp layer bản đồ SOSConn và realtime signal cho command center.

## Owned Scope

- `frontend/src/components/Map.tsx`
- `frontend/src/pages/AssetMapView.tsx` hoặc trang command center mới
- `frontend/src/api/`
- `backend/app/api/v1/routers/geo.py` (mở rộng)

## Responsibilities

- Thêm layer hazard/SOS/resource/route/shelter.
- Thêm filter theo event type, severity, district, time window.
- Tích hợp realtime updates qua WebSocket/SSE.
- Tối ưu clustering + throttling.
- Đảm bảo map performance khi marker lớn.

## Patch Handoff Contract

```yaml
agent: dev05-realtime-map
changes:
  - map_layers_added
  - realtime_feed_added
  - filter_panel_added
performance:
  - marker_visibility_latency
  - fps_under_load
tests:
  - map_e2e_passed
status: done
```

## Done Criteria

1. Marker SOS cập nhật nhanh.
2. Layer bật/tắt và lọc hoạt động đúng.
3. Realtime reconnect ổn định.
4. Map không drop nghiêm trọng khi tải cao.
5. E2E map flow pass.
