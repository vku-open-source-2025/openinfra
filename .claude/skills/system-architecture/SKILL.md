---
name: system-architecture
description: Chuẩn hóa kiến trúc tích hợp SOSConn vào OpenInfra. Dùng khi cần chốt ADR, vẽ dependency map, thiết kế roadmap phase, hoặc giải quyết conflict kiến trúc.
disable-model-invocation: false
---

## Mission

Chuẩn hóa kiến trúc tích hợp SOSConn vào OpenInfra, chốt ADR, dependency map và tiêu chuẩn triển khai thống nhất.

## Responsibilities

- Cập nhật fit-gap dựa trên `.notes/sosconn_integration.md`.
- Soạn và duy trì ADR-01..ADR-05.
- Chuẩn hóa enum và naming convention xuyên backend/frontend.
- Định nghĩa boundary giữa OpenInfra core và SOSConn extension.
- Thiết kế roadmap P0/P1/P2 có milestone đo lường được.
- Duy trì risk register và mitigation plan.

## Repo Scope

- `.notes/sosconn_integration.md`
- `backend/app/domain/`
- `backend/app/api/v1/routers/`
- `frontend/src/routes/`
- `infra/docker-compose.yml`
- `3rd_party/sosconn/`

## Output Contract

- 1 tài liệu ADR summary.
- 1 dependency map theo phase song song.
- 1 checklist Definition of Done toàn hệ thống.

Mẫu handoff:

```yaml
agent: system-architecture
status: done
artifacts:
  - adr_summary
  - dependency_map
  - risk_register
blocked_items: []
next_agents:
  - dev01-domain-model
  - dev02-emergency-api
```

## Done Criteria

1. Có tối thiểu 5 ADR đã chốt.
2. Có roadmap 12-16 tuần với deliverable cụ thể.
3. Có chuẩn naming/enum được đội backend/frontend dùng thống nhất.
4. Có risk register tối thiểu 8 rủi ro.
5. Không còn conflict kiến trúc blocker mức P0.
