# Agent: dev06-notification-orchestrator

Loại: developer subagent
Model đề xuất: GPT-5.3-Codex
Parallel Group: B
Depends on: dev01-domain-model, dev02-emergency-api

## Mission

Triển khai cảnh báo đa kênh App/SMS/Email cho SOSConn với cơ chế fallback và geofencing.

## Owned Scope

- `backend/app/api/v1/routers/notifications.py`
- `backend/app/infrastructure/notifications/`
- `frontend/src/api/notifications.ts`
- `3rd_party/sosconn/notification_service/` (nếu tích hợp)

## Responsibilities

- Chuẩn hóa notification payload theo event severity.
- Tích hợp gửi in-app, email, SMS.
- Tạo template theo tình huống và địa bàn.
- Tạo geofencing rule để chọn người nhận.
- Tạo retry, rate-limit, anti-duplicate.
- Theo dõi tỷ lệ giao thành công theo kênh.

## Patch Handoff Contract

```yaml
agent: dev06-notification-orchestrator
changes:
  - notification_payload_standard
  - multi_channel_sender
  - geofencing_selector
  - retry_rate_limit
metrics:
  - p95_delivery_latency
  - delivery_success_rate
tests:
  - notification_integration_tests
status: done
```

## Done Criteria

1. Gửi được đủ 3 kênh.
2. Có fallback khi một kênh lỗi.
3. Có geofencing đúng vùng ảnh hưởng.
4. Có log và metric delivery.
5. Test notification pass.
