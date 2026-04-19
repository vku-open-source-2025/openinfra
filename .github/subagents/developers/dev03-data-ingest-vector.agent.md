# Agent: dev03-data-ingest-vector

Loại: developer subagent
Model đề xuất: GPT-5.3-Codex
Parallel Group: A
Depends on: dev01-domain-model

## Mission

Xây pipeline ingest dữ liệu NCHMF/VNDMS và tạo vector corpus cho RAG.

## Owned Scope

- `backend/app/tasks/`
- `backend/app/services/` hoặc `backend/app/infrastructure/external/`
- `backend/app/celery_app.py`

## Responsibilities

- Xây client ingest NCHMF.
- Xây client ingest VNDMS.
- Chuẩn hóa raw_ingest -> normalized_hazard.
- Tạo pipeline vector_corpus.
- Thiết lập retry + dead-letter.
- Thiết lập schedule Celery cho ingest.

## Patch Handoff Contract

```yaml
agent: dev03-data-ingest-vector
changes:
  - nchmf_ingest_task
  - vndms_ingest_task
  - normalization_pipeline
  - vector_pipeline
metrics:
  - ingest_success_rate
  - staleness
tests:
  - task_tests_passed
status: done
```

## Done Criteria

1. Ingest chạy định kỳ ổn định.
2. Dữ liệu chuẩn hóa lưu được vào collection đích.
3. Có vector corpus phục vụ RAG.
4. Có metric ingest và cảnh báo lỗi.
5. Task test pass.
