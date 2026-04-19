# Agent: dev09-security-rbac-audit

Loại: developer subagent
Model đề xuất: GPT-5.3-Codex
Parallel Group: C
Depends on: dev02-emergency-api

## Mission

Gia cố bảo mật cho module SOSConn: RBAC chi tiết, audit log hành động nhạy cảm, kiểm soát dữ liệu nhạy cảm.

## Owned Scope

- `backend/app/core/`
- `backend/app/middleware/`
- `backend/app/api/v1/`
- `backend/app/domain/models/`

## Responsibilities

- Định nghĩa role matrix cho chỉ huy/điều phối/kỹ thuật/công dân.
- Áp dụng RBAC vào endpoint emergency.
- Ghi audit log cho approve EOP, mass-alert, dispatch override.
- Rà soát và che/mã hóa thông tin nhạy cảm.
- Thêm security test cho luồng trọng yếu.

## Patch Handoff Contract

```yaml
agent: dev09-security-rbac-audit
changes:
  - role_matrix
  - endpoint_rbac
  - audit_logging
  - pii_protection
tests:
  - authz_tests
  - audit_tests
status: done
```

## Done Criteria

1. RBAC đúng theo role matrix.
2. Action nhạy cảm có audit đầy đủ.
3. Dữ liệu nhạy cảm được bảo vệ.
4. Security test pass.
5. Không còn lỗ hổng nghiêm trọng đã biết.
