# Agent: dev07-datacollector-sync

Loại: developer subagent
Model đề xuất: GPT-5.3-Codex
Parallel Group: B
Depends on: dev01-domain-model, dev03-data-ingest-vector

## Mission

Đồng bộ luồng báo cáo cộng đồng từ Datacollector vào command center SOSConn và phản hồi ngược trạng thái xử lý.

## Owned Scope

- `datacollector/backend/main.py`
- `backend/app/tasks/contribution_etl.py`
- `backend/app/api/v1/routers/incidents.py`
- `backend/app/domain/services/`

## Responsibilities

- Chuẩn hóa schema contribution -> incident/SOS event.
- Đồng bộ trạng thái pending/approved/rejected hai chiều.
- Hỗ trợ media metadata cho ảnh/video.
- Gắn SLA xử lý báo cáo cộng đồng.
- Chống duplicate và conflict update.

## Patch Handoff Contract

```yaml
agent: dev07-datacollector-sync
changes:
  - schema_mapping
  - bidirectional_status_sync
  - media_metadata_flow
  - dedup_logic
sla:
  - ingest_to_command_center_latency
tests:
  - etl_sync_tests
status: done
```

## Done Criteria

1. Báo cáo cộng đồng đi vào command center đúng luồng.
2. Trạng thái phản hồi đồng bộ hai chiều.
3. Có kiểm soát duplicate.
4. Có SLA metric cho sync.
5. ETL test pass.
