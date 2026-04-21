# OpenInfra — Deployment Guide

> Hướng dẫn triển khai toàn bộ hệ thống OpenInfra trên server cá nhân với Cloudflare Tunnel (không cần port forwarding, không cần public IP).

## Bước 0: Gọi DevOps Subagent Trước Khi Deploy

Trước khi chạy deploy production, bắt buộc gọi DevOps subagent để kiểm tra rủi ro cấu hình và thứ tự triển khai an toàn.

- Subagent profile: `.github/subagents/devops/devops-cloudflare-tunnel.agent.md`
- Hướng dẫn gọi: `.github/subagents/deployment/call-devops-agent.md`

Áp dụng bắt buộc trong các trường hợp:

- Deploy production theo `infra/deploy.sh`
- Có thay đổi ở `infra/nginx/nginx.conf`
- Có thay đổi ở `infra/cloudflared/config-openinfra.example.yml`
- Thêm service mới vào `infra/docker-compose.yml`

## Kiến trúc triển khai

```
Internet
    ↓
Cloudflare Edge (CNAME records → tunnel)
    ↓
cloudflared tunnel (outbound connection từ server)
    ↓
nginx (port 443, SSL via certbot DNS challenge)
    ├── openinfra.space      → frontend:5173
    ├── api.openinfra.space  → backend:8000
    ├── mcp.openinfra.space  → mcp-server:8000
    └── ssh.openinfra.space  → SSH (port 22)
    ↓
Docker services
    ├── backend (FastAPI)
    ├── frontend (React/Vite)
    ├── mcp-server
    ├── celery-worker + celery-beat
    ├── MongoDB + Redis + Kafka
    └── certbot (auto-renew SSL)
```

### Tại sao dùng Cloudflare Tunnel?

- **Không cần port forwarding** — Tunnel tạo outbound connection từ server đến Cloudflare Edge
- **Hoạt động qua NAT/CGNAT** — Server có thể nằm sau nhiều lớp NAT
- **Không cần public IP** — IP thay đổi không ảnh hưởng (tunnel duy trì kết nối)
- **Bảo mật** — Server không expose port nào ra internet
- **DDoS protection** — Cloudflare proxy filter traffic

## Yêu cầu

- Docker + Docker Compose
- `cloudflared` (Cloudflare Tunnel client) — [Download](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
- Domain được quản lý bởi Cloudflare
- Cloudflare API Token với quyền **Edit zone DNS**

## Các bước triển khai

### Bước 1: Clone và chuẩn bị

```bash
git clone <repo-url> openinfra
cd openinfra
```

### Bước 2: Tạo Cloudflare API Token

1. Vào https://dash.cloudflare.com/profile/api-tokens
2. Click **Create Token**
3. Chọn template **Edit zone DNS**
4. Zone Resources → Include → Specific zone → `openinfra.space`
5. Click **Continue to summary** → **Create Token**
6. Copy token

### Bước 3: Cấu hình environment

```bash
cd infra

# Copy env mẫu
cp .env.example .env
cp .env.cloudflare.example .env.cloudflare

# Chỉnh sửa .env
nano .env
```

**Các biến quan trọng trong `.env`:**

| Biến | Mô tả | Ví dụ |
|------|--------|-------|
| `MONGODB_URL` | MongoDB connection | `mongodb://mongo:27017` |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` |
| `BACKEND_PORT` | Backend exposed port | `8001` |
| `FRONTEND_PORT` | Frontend exposed port | `5174` |
| `CF_API_TOKEN` | Cloudflare API token | `xxxxxxxx` |
| `CF_ZONE_ID` | Cloudflare Zone ID | `7fdd60684d...` |
| `CF_DOMAIN` | Domain | `openinfra.space` |

**Chỉnh sửa `.env.cloudflare`:**

```bash
nano .env.cloudflare
# Điền CF_API_TOKEN và CF_ZONE_ID
```

### Bước 4: Cài đặt cloudflared

```bash
# Cài cloudflared
# Debian/Ubuntu:
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Đăng nhập Cloudflare
cloudflared tunnel login
# → Mở browser, chọn zone openinfra.space
```

### Bước 5: Deploy tự động (recommended)

```bash
cd infra
chmod +x deploy.sh
./deploy.sh
```

Script `deploy.sh` tự động thực hiện:
1. Kiểm tra port conflicts
2. Start Docker services
3. Xin wildcard SSL certificate (DNS challenge)
4. Tạo/kiểm tra Cloudflare Tunnel
5. Tạo CNAME records trên Cloudflare
6. Start tunnel as systemd service
7. Verify deployment

### Bước 5 (thay thế): Deploy thủ công

#### 5a. Start Docker services

```bash
cd infra

# Tạo thư mục certbot
mkdir -p certbot/conf certbot/www certbot/cloudflare

# Tạo credentials cho certbot DNS challenge
echo "dns_cloudflare_api_token = YOUR_TOKEN" > certbot/cloudflare/credentials.ini
chmod 600 certbot/cloudflare/credentials.ini

docker compose up -d --build
```

#### 5b. Xin wildcard SSL certificate (DNS challenge)

```bash
docker compose run --rm certbot certonly \
    --dns-cloudflare \
    --dns-cloudflare-credentials /etc/letsencrypt/cloudflare/credentials.ini \
    --dns-cloudflare-propagation-seconds 30 \
    --email admin@openinfra.space \
    --agree-tos \
    --no-eff-email \
    -d openinfra.space \
    -d "*.openinfra.space"

# Reload nginx
docker compose exec nginx nginx -s reload
```

#### 5c. Tạo Cloudflare Tunnel

```bash
# Tạo tunnel
cloudflared tunnel create openinfra

# Lấy tunnel ID (UUID)
TUNNEL_ID=$(cloudflared tunnel list --output json | python3 -c "
import sys, json
for t in json.load(sys.stdin):
    if t['name'] == 'openinfra':
        print(t['id']); break
")

# Copy config mẫu và thay thế placeholder
cp infra/cloudflared/config-openinfra.example.yml ~/.cloudflared/config-openinfra.yml
sed -i "s/<TUNNEL_ID>/${TUNNEL_ID}/g; s/<USERNAME>/$(whoami)/g" ~/.cloudflared/config-openinfra.yml
```

#### 5d. Tạo DNS CNAME records

```bash
source infra/.env.cloudflare
TUNNEL_CNAME="${TUNNEL_ID}.cfargotunnel.com"

# Tạo CNAME records cho mỗi domain
for DOMAIN in openinfra.space api.openinfra.space mcp.openinfra.space; do
  curl -X POST "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records" \
    -H "Authorization: Bearer ${CF_API_TOKEN}" \
    -H "Content-Type: application/json" \
    --data "{\"type\":\"CNAME\",\"name\":\"${DOMAIN}\",\"content\":\"${TUNNEL_CNAME}\",\"proxied\":true}"
done
```

#### 5e. Start tunnel

```bash
# Test (foreground)
cloudflared tunnel --config ~/.cloudflared/config-openinfra.yml run openinfra

# Hoặc tạo systemd user service (recommended)
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/cloudflared-openinfra.service << EOF
[Unit]
Description=Cloudflare Tunnel for openinfra.space
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$(which cloudflared) tunnel --config /home/$(whoami)/.cloudflared/config-openinfra.yml run openinfra
Restart=always
RestartSec=5
Environment="NO_AUTOUPDATE=true"

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable cloudflared-openinfra.service
systemctl --user start cloudflared-openinfra.service

# Enable linger (persist after logout)
loginctl enable-linger $(whoami)
```

### Bước 5f: Update cloudflared (khuyến nghị)

Luôn giữ `cloudflared` ở phiên bản mới nhất để tránh lỗi connection pooling, memory leak:

```bash
# Kiểm tra phiên bản hiện tại
cloudflared --version

# Update
sudo cloudflared update

# Restart tunnel
systemctl --user restart cloudflared-openinfra
```

### Bước 6: Seed data (nếu cần)

```bash
cd infra
python3 seed_data.py
python3 seed_iot_data.py
```

### Bước 7: Tạo admin user

```bash
docker compose exec backend python scripts/create_superuser.py
```

## SSL Certificate

### Wildcard cert via DNS challenge
Dùng certbot với Cloudflare DNS plugin — **không cần port 80 mở**, hoạt động qua NAT.

### Auto-renew
```bash
docker compose run --rm certbot renew
docker compose exec nginx nginx -s reload
```

### Kiểm tra certificate
```bash
echo | openssl s_client -connect openinfra.space:443 2>/dev/null | openssl x509 -noout -dates
```

## Quản lý Tunnel

### Xem trạng thái
```bash
# Systemd service
systemctl --user status cloudflared-openinfra

# Tunnel connections
cloudflared tunnel info openinfra

# Logs
journalctl --user -u cloudflared-openinfra -f
```

### Restart tunnel
```bash
systemctl --user restart cloudflared-openinfra
```

### Stop tunnel
```bash
systemctl --user stop cloudflared-openinfra
```

## Cloudflare Settings (khuyến nghị)

Trên Cloudflare Dashboard → `openinfra.space`:

| Setting | Value | Lý do |
|---------|-------|-------|
| SSL/TLS Mode | **Full** | Server có self-signed cert, tunnel dùng noTLSVerify |
| Always Use HTTPS | **On** | Force HTTPS |
| Minimum TLS | **1.2** | Security |
| Auto Minify | **On** | Performance |
| Brotli | **On** | Compression |

## Cấu trúc file

```
infra/
├── docker-compose.yml          # Docker services
├── deploy.sh                   # Auto deployment script (tunnel approach)
├── .env                        # Environment variables
├── .env.example                # Template
├── .env.cloudflare             # Cloudflare credentials
├── .env.cloudflare.example     # Template
├── cloudflared/
│   └── config-openinfra.example.yml  # Tunnel config mẫu (copy → ~/.cloudflared/)
├── nginx/
│   ├── nginx.conf              # Production config (SSL)
│   └── nginx-init.conf         # Bootstrap config (HTTP only)
├── certbot/
│   ├── conf/                   # SSL certificates (auto-generated)
│   ├── www/                    # ACME challenge files
│   └── cloudflare/
│       └── credentials.ini     # Cloudflare API token for DNS challenge
└── ...

~/.cloudflared/
├── config-openinfra.yml        # Tunnel config (ingress rules)
├── <tunnel-id>.json            # Tunnel credentials
└── cert.pem                    # Cloudflare login certificate

~/.config/systemd/user/
└── cloudflared-openinfra.service  # Systemd user service
```

## Troubleshooting

### 502 Bad Gateway qua Cloudflare Tunnel

Lỗi 502 nghĩa là **cloudflared nhận request từ Cloudflare edge nhưng không forward được tới backend**. Không phải Cloudflare chặn.

**Nguyên nhân phổ biến:**

| Nguyên nhân | Giải pháp |
|---|---|
| `cloudflared` phiên bản cũ | `sudo cloudflared update` rồi restart tunnel |
| Không có keepAlive tuning | Thêm `keepAliveConnections: 100` + `keepAliveTimeout: 90s` vào config |
| Connect timeout quá ngắn (default 10s) | Tăng `connectTimeout: 30s` |
| TLS handshake overhead (localhost) | Cân nhắc dùng `http://localhost:80` thay vì `https://localhost:443` |
| Nginx/backend bị quá tải | Kiểm tra `docker compose logs nginx` và `free -h` |

**Kiểm tra nhanh:**
```bash
# Xem phiên bản cloudflared
cloudflared --version

# Update cloudflared (khuyến nghị luôn dùng bản mới nhất)
sudo cloudflared update

# Kiểm tra tunnel đang chạy
ps aux | grep cloudflared | grep -v grep

# Xem logs realtime
journalctl --user -u cloudflared-openinfra -f

# Restart tunnel sau khi sửa config
kill $(pgrep -f 'cloudflared.*openinfra') && sleep 3
systemctl --user start cloudflared-openinfra
```

**Config tối ưu (đã áp dụng):** xem mẫu tại Bước 5c với các tham số `connectTimeout`, `keepAliveConnections`, `keepAliveTimeout`.

### DNS không resolve
```bash
# Kiểm tra DNS
dig +short openinfra.space
dig +short api.openinfra.space

# Kiểm tra CNAME records trên Cloudflare
source infra/.env.cloudflare
curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
    "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" | \
    python3 -c "import sys,json; [print(f'{x[\"type\"]} {x[\"name\"]} → {x[\"content\"]}') for x in json.load(sys.stdin)['result']]"
```

### Error 1033 (Argo Tunnel error)
DNS CNAME records trỏ sai tunnel ID:
```bash
# Kiểm tra tunnel ID
cloudflared tunnel list
# TUNNEL_ID=<id-đúng>

# Kiểm tra CNAME records
# Nếu CNAME trỏ đến UUID khác → cần update:
source infra/.env.cloudflare
CORRECT_TUNNEL="<TUNNEL_ID>.cfargotunnel.com"
for DOMAIN in openinfra.space api.openinfra.space mcp.openinfra.space; do
  REC_ID=$(curl -s "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records?name=${DOMAIN}" \
    -H "Authorization: Bearer ${CF_API_TOKEN}" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['id'])")
  curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records/${REC_ID}" \
    -H "Authorization: Bearer ${CF_API_TOKEN}" \
    -H "Content-Type: application/json" \
    --data "{\"content\":\"${CORRECT_TUNNEL}\",\"proxied\":true}"
done
```

### Tunnel không chạy
```bash
# Kiểm tra service
systemctl --user status cloudflared-openinfra

# Xem logs
journalctl --user -u cloudflared-openinfra --no-pager -n 50

# Restart
systemctl --user restart cloudflared-openinfra

# Kiểm tra credentials file
ls -la ~/.cloudflared/*.json
cat ~/.cloudflared/config-openinfra.yml
```

### Certbot DNS challenge fail
```bash
# Kiểm tra credentials
cat infra/certbot/cloudflare/credentials.ini

# Kiểm tra API token có quyền DNS
curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
    "https://api.cloudflare.com/client/v4/user/tokens/verify" | python3 -m json.tool

# Thử lại
docker compose run --rm certbot certonly \
    --dns-cloudflare \
    --dns-cloudflare-credentials /etc/letsencrypt/cloudflare/credentials.ini \
    --dns-cloudflare-propagation-seconds 60 \
    -d openinfra.space -d "*.openinfra.space"
```

### Port 80/443 conflict (Docker)
```bash
# Kiểm tra process đang dùng port
sudo ss -tlnp | grep -E ':80|:443'

# Dừng nginx host (nếu chạy)
sudo systemctl stop nginx
sudo systemctl disable nginx
```

## Outage Rollback and Smoke Playbook

### Khi nào chạy playbook này

- Sau khi thay đổi `infra/docker-compose.yml`, `infra/nginx/nginx.conf`, hoặc tunnel config.
- Ngay khi public probe trả về 5xx kéo dài trên `openinfra.space` hoặc `api.openinfra.space`.

### Bước 1: Preflight cấu hình

```bash
cd infra
docker compose config -q
```

### Bước 2: Triển khai và xác nhận health nội bộ

```bash
cd infra
docker compose up -d --build
docker compose ps
docker compose logs nginx --tail 100
```

### Bước 3: Smoke test local qua nginx

```bash
cd infra
curl -k -sS -o /dev/null -w 'openinfra_map=%{http_code}\n' -H 'Host: openinfra.space' https://127.0.0.1/map
curl -k -sS -o /dev/null -w 'api_health=%{http_code}\n' -H 'Host: api.openinfra.space' https://127.0.0.1/health
```

### Bước 4: Smoke test public

```bash
curl -sS -o /dev/null -w 'openinfra_map=%{http_code}\n' https://openinfra.space/map
curl -sS -o /dev/null -w 'api_health=%{http_code}\n' https://api.openinfra.space/health
```

### Bước 5: Rollback nhanh về cấu hình đã biết tốt

```bash
# Ví dụ rollback theo commit/tag đã xác nhận ổn định
git checkout <known-good-ref> -- infra/docker-compose.yml infra/nginx/nginx.conf

cd infra
docker compose up -d --build
docker compose ps
```

### Bước 6: Xác nhận sau rollback

- Lặp lại Bước 3 và Bước 4.
- Kiểm tra tunnel ổn định: `systemctl --user status cloudflared-openinfra`.
- Nếu còn lỗi 5xx: thu thập logs `nginx`, `backend`, `frontend`, `cloudflared` trước khi thay đổi tiếp.

## Redeploy

```bash
cd infra

# Redeploy toàn bộ
./deploy.sh

# Chỉ restart Docker services
docker compose restart

# Rebuild và restart
docker compose up -d --build

# Restart tunnel
systemctl --user restart cloudflared-openinfra
```
