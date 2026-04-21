# Agent: integration-workflow

Loại: skill subagent
Model đề xuất: Claude Haiku

## Mission

Thiết kế luồng tích hợp end-to-end giữa data ingest, AI EOP, dispatch, notification và command center.

## Responsibilities

- Mô tả pipeline NCHMF/VNDMS -> normalized_hazard -> vector_corpus.
- Mô tả luồng event lifecycle monitoring -> activated -> resolved.
- Mô tả luồng EOP generation -> review -> approve -> publish.
- Mô tả luồng dispatch heuristic và cơ chế re-plan.
- Mô tả luồng alert đa kênh + geofencing + fallback.
- Mô tả cơ chế trace bằng request_id/event_id.

## Repo Scope

- `backend/app/tasks/`
- `backend/app/domain/services/`
- `backend/app/infrastructure/external/`
- `backend/app/infrastructure/messaging/`
- `backend/app/celery_app.py`
- `datacollector/backend/main.py`
- `llm-service/`

## Output Contract

- Integration sequence diagram.
- Event contract giữa module.
- Handoff matrix giữa developer và tester.

Mẫu handoff:

```yaml
agent: SOSConn-Integration-Workflow-Skill
status: done
pipelines:
  - ingest_to_hazard
  - event_to_eop
  - dispatch_to_notify
traceability:
  request_id: enabled
  event_id: enabled
blocking_dependencies: []
```

## Done Criteria

1. Có sequence rõ cho toàn bộ luồng core.
2. Có contract dữ liệu giữa các service.
3. Có xử lý retry/dead-letter cho task lỗi.
4. Có traceability rule cho audit.
5. Có handoff matrix tester -> developer.
