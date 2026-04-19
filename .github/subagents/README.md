# SOSConn Integration Subagents

Bộ subagent này dùng cho mục tiêu tích hợp SOSConn vào OpenInfra theo tài liệu phân tích tại `.notes/sosconn_integration.md`.

## Cấu trúc

- `skills/`: 5 subagent tạo kỹ năng hệ thống, coding và deploy.
- `testers/`: 2 subagent kiểm thử, phát hiện bug, bàn giao cho developer.
- `developers/`: 10 subagent chuyên trách fix bug và tích hợp từng mảng.
- `devops/`: 1 subagent triển khai với Cloudflare Tunnel.
- `deployment/`: hướng dẫn gọi DevOps subagent khi deploy.

## Nguyên tắc chạy song song

- Phase 1 (nền tảng): `skills/*` + `developers/dev01..dev04`.
- Phase 2 (tích hợp): `developers/dev05..dev08`.
- Phase 3 (hardening): `developers/dev09..dev10` + `devops/*`.
- Phase 4 (kiểm thử): `testers/*` chạy song song và gửi bug cho developer tương ứng.

## Cách gọi bằng runSubagent

Dùng prompt trong từng file `.agent.md` làm input cho `runSubagent`.

Ví dụ luồng deployment:

1. Mở file `devops/devops-cloudflare-tunnel.agent.md`.
2. Copy phần nhiệm vụ vào `runSubagent`.
3. Chạy deploy theo checklist trong `deployment/call-devops-agent.md`.
