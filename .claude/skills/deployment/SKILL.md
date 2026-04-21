---
name: deployment
description: Chuẩn hóa build, compose, migrate, verify khi tích hợp SOSConn vào OpenInfra Docker. Dùng khi deploy service mới, cần smoke test, rollback checklist, hoặc cấu hình healthcheck/resource limit.
disable-model-invocation: true
---

## Mission

Chuẩn hóa cách build, compose, migrate, verify khi tích hợp SOSConn service vào OpenInfra hạ tầng Docker hiện tại.

## Responsibilities

- Chuẩn hóa Dockerfile/backend/frontend theo hướng production-ready.
- Chuẩn hóa compose service cho llm-service và notification_service.
- Chuẩn hóa healthcheck, restart policy, resource limit.
- Chuẩn hóa seed/migration dữ liệu emergency.
- Chuẩn hóa post-deploy smoke test và rollback checklist.
- Chuẩn hóa metric theo dõi Celery/ingest/dispatch/notify.

## Repo Scope

- `infra/docker-compose.yml`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `infra/DEPLOYMENT.md`
- `llm-service/`

## Output Contract

- Deployment checklist chuẩn hóa.
- Compose integration plan cho SOSConn services.
- Verification script/checklist sau triển khai.

Mẫu handoff:

```yaml
agent: deployment
status: done
compose_changes:
  - llm_service_added
  - notification_service_added
checks:
  - healthcheck
  - smoke_test
  - rollback_ready
pending: []
```

## Done Criteria

1. Có checklist deploy dùng được ngay cho team.
2. Có kế hoạch compose tích hợp 2 service SOSConn.
3. Có smoke test danh sách endpoint quan trọng.
4. Có rollback procedure khi deploy lỗi.
5. Có metric giám sát sau deploy.
