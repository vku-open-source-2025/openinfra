# Gọi DevOps Agent Khi Deployment

File này quy định cách gọi DevOps subagent trước và trong khi triển khai.

## Agent sử dụng

- `SOSConn-DevOps-Cloudflare-Tunnel`
- Định nghĩa tại: `../devops/devops-cloudflare-tunnel.agent.md`

## Thời điểm bắt buộc gọi

1. Trước khi chạy `infra/deploy.sh` trên production.
2. Sau khi thay đổi `infra/nginx/nginx.conf` hoặc `infra/cloudflared/config-openinfra.example.yml`.
3. Sau khi thêm service mới vào `infra/docker-compose.yml`.

## Prompt mẫu cho runSubagent

```text
Đóng vai SOSConn-DevOps-Cloudflare-Tunnel.
Mục tiêu: kiểm tra sẵn sàng deploy OpenInfra + SOSConn trên Cloudflare Tunnel.
Hãy:
1) kiểm tra cấu hình compose/nginx/cloudflared,
2) liệt kê rủi ro production,
3) đề xuất thứ tự deploy an toàn,
4) trả về checklist smoke test và rollback plan.
Dữ liệu tham chiếu: infra/DEPLOYMENT.md, infra/docker-compose.yml, infra/nginx/nginx.conf, .notes/sosconn_integration.md.
```

## Checklist sau khi gọi agent

- [ ] Đã xác nhận pre-deploy checklist pass.
- [ ] Đã xác nhận tunnel + DNS + SSL hợp lệ.
- [ ] Đã chạy smoke test endpoint chính sau deploy.
- [ ] Đã lưu deployment report cho team.
