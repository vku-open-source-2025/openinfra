# Agent: dev04-ai-eop-rag

Loại: developer subagent
Model đề xuất: GPT-5.3-Codex
Parallel Group: A
Depends on: dev01-domain-model, dev03-data-ingest-vector

## Mission

Triển khai AI Agent sinh EOP dựa trên dữ liệu tình huống + RAG.

## Owned Scope

- `backend/app/services/ai_agent.py` hoặc service mới
- `backend/app/api/v1/routers/ai_agent.py`
- `backend/app/domain/models/`
- `frontend/src/components/AIChatWidget.tsx` (phần integration nếu cần)

## Responsibilities

- Định nghĩa EOP schema JSON chuẩn.
- Tạo pipeline generate EOP draft.
- Tích hợp retrieval từ vector corpus.
- Thêm workflow review/approve/publish.
- Lưu versioning + audit trail EOP.

## Patch Handoff Contract

```yaml
agent: dev04-ai-eop-rag
changes:
  - eop_schema
  - eop_generation_service
  - review_approve_publish_workflow
validation:
  - schema_valid_rate
  - retrieval_relevance
tests:
  - ai_eop_tests_passed
status: done
```

## Done Criteria

1. EOP sinh ra đúng schema.
2. Có luồng phê duyệt và publish.
3. Có version lịch sử EOP.
4. Có log/audit cho thao tác quan trọng.
5. Test AI service pass ở mức chấp nhận.
