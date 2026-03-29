#!/bin/bash
# ============================================================
# OpenInfra Full Deployment Script
# Deploys: Docker → SSL (DNS challenge) → Cloudflare Tunnel
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CF_CONFIG_DIR="${HOME}/.cloudflared"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[DEPLOY]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ============================================================
# Pre-flight checks
# ============================================================
log "=== OpenInfra Deployment ==="
log "Project root: ${PROJECT_ROOT}"

[[ -f "$SCRIPT_DIR/.env" ]] || error "Missing infra/.env — copy from .env.example"
[[ -f "$SCRIPT_DIR/.env.cloudflare" ]] || error "Missing infra/.env.cloudflare"

source "$SCRIPT_DIR/.env.cloudflare"

CF_DOMAIN="${CF_DOMAIN:-openinfra.space}"

command -v docker >/dev/null 2>&1 || error "Docker not installed"
command -v cloudflared >/dev/null 2>&1 || error "cloudflared not installed — https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"

# Docker compose command
if docker compose version >/dev/null 2>&1; then
    DC="docker compose"
else
    DC="docker-compose"
fi

# ============================================================
# Step 1: Check port conflicts
# ============================================================
log ""
log "=== Step 1: Check port conflicts ==="

if ss -tlnp 2>/dev/null | grep -qE ':80\b.*nginx'; then
    warn "Host nginx is running on port 80. Attempting to stop..."
    sudo systemctl stop nginx 2>/dev/null || sudo service nginx stop 2>/dev/null || true
    sudo systemctl disable nginx 2>/dev/null || true
    log "Host nginx stopped"
else
    log "No port conflicts detected"
fi

# ============================================================
# Step 2: Start Docker services
# ============================================================
log ""
log "=== Step 2: Start Docker services ==="
cd "$SCRIPT_DIR"

# Create certbot directories
mkdir -p certbot/conf certbot/www certbot/cloudflare

# Start all services
$DC up -d --build

log "Waiting for services to start..."
sleep 10

# Check services
RUNNING=$($DC ps --format "{{.Name}}" --status running | wc -l)
log "${RUNNING} services running"

# ============================================================
# Step 3: Obtain SSL certificates (DNS challenge)
# ============================================================
log ""
log "=== Step 3: Obtain SSL certificates ==="

if [[ -f "certbot/conf/live/${CF_DOMAIN}/fullchain.pem" ]]; then
    log "Certificates already exist, skipping certbot"
else
    # Ensure cloudflare credentials exist for certbot
    if [[ ! -f "certbot/cloudflare/credentials.ini" ]]; then
        log "Creating certbot cloudflare credentials..."
        echo "dns_cloudflare_api_token = ${CF_API_TOKEN}" > certbot/cloudflare/credentials.ini
        chmod 600 certbot/cloudflare/credentials.ini
    fi

    log "Requesting wildcard certificate for ${CF_DOMAIN} via DNS challenge..."

    $DC run --rm certbot certonly \
        --dns-cloudflare \
        --dns-cloudflare-credentials /etc/letsencrypt/cloudflare/credentials.ini \
        --dns-cloudflare-propagation-seconds 30 \
        --email "admin@${CF_DOMAIN}" \
        --agree-tos \
        --no-eff-email \
        -d "${CF_DOMAIN}" \
        -d "*.${CF_DOMAIN}" \
        || error "Certbot DNS challenge failed. Check CF_API_TOKEN permissions."

    log "Wildcard certificate obtained!"
fi

# Reload nginx to pick up certificates
$DC exec nginx nginx -s reload 2>/dev/null || $DC restart nginx
log "Nginx reloaded with SSL"

# ============================================================
# Step 4: Setup Cloudflare Tunnel
# ============================================================
log ""
log "=== Step 4: Setup Cloudflare Tunnel ==="

TUNNEL_NAME="openinfra"

# Check if tunnel already exists
EXISTING_TUNNEL=$(cloudflared tunnel list --output json 2>/dev/null | python3 -c "
import sys, json
for t in json.load(sys.stdin):
    if t['name'] == '${TUNNEL_NAME}':
        print(t['id'])
        break
" 2>/dev/null) || true

if [[ -n "$EXISTING_TUNNEL" ]]; then
    TUNNEL_ID="$EXISTING_TUNNEL"
    log "Using existing tunnel: ${TUNNEL_ID}"
else
    log "Creating tunnel '${TUNNEL_NAME}'..."
    TUNNEL_ID=$(cloudflared tunnel create "${TUNNEL_NAME}" 2>&1 | grep -oP '[0-9a-f-]{36}' | head -1)
    [[ -n "$TUNNEL_ID" ]] || error "Failed to create tunnel"
    log "Tunnel created: ${TUNNEL_ID}"
fi

# Write tunnel config
TUNNEL_CONFIG="${CF_CONFIG_DIR}/config-openinfra.yml"
cat > "$TUNNEL_CONFIG" << EOF
tunnel: ${TUNNEL_ID}
credentials-file: ${CF_CONFIG_DIR}/${TUNNEL_ID}.json

ingress:
  # Frontend (main domain)
  - hostname: ${CF_DOMAIN}
    service: https://localhost:443
    originRequest:
      noTLSVerify: true
  # API backend
  - hostname: api.${CF_DOMAIN}
    service: https://localhost:443
    originRequest:
      noTLSVerify: true
  # MCP server
  - hostname: mcp.${CF_DOMAIN}
    service: https://localhost:443
    originRequest:
      noTLSVerify: true
  # Catch-all
  - service: http_status:404
EOF
log "Tunnel config written to ${TUNNEL_CONFIG}"

# ============================================================
# Step 5: Setup DNS CNAME records (via Cloudflare API)
# ============================================================
log ""
log "=== Step 5: Setup DNS CNAME records ==="

TUNNEL_CNAME="${TUNNEL_ID}.cfargotunnel.com"

cf_api() {
    local method="$1" endpoint="$2" data="${3:-}"
    local url="https://api.cloudflare.com/client/v4${endpoint}"
    if [[ -n "$data" ]]; then
        curl -s -X "$method" "$url" \
            -H "Authorization: Bearer ${CF_API_TOKEN}" \
            -H "Content-Type: application/json" \
            --data "$data"
    else
        curl -s -X "$method" "$url" \
            -H "Authorization: Bearer ${CF_API_TOKEN}"
    fi
}

upsert_cname() {
    local fqdn="$1"
    local data
    data=$(python3 -c "
import json
print(json.dumps({
    'type': 'CNAME',
    'name': '${fqdn}',
    'content': '${TUNNEL_CNAME}',
    'proxied': True,
    'ttl': 1
}))
")

    # Check for existing record (any type)
    local existing
    existing=$(cf_api GET "/zones/${CF_ZONE_ID}/dns_records?name=${fqdn}" | python3 -c "
import sys, json
r = json.load(sys.stdin)
for rec in r.get('result', []):
    print(rec['id'], rec['type'])
    break
" 2>/dev/null) || true

    if [[ -n "$existing" ]]; then
        local rec_id rec_type
        rec_id=$(echo "$existing" | awk '{print $1}')
        rec_type=$(echo "$existing" | awk '{print $2}')
        if [[ "$rec_type" != "CNAME" ]]; then
            # Delete non-CNAME record first
            cf_api DELETE "/zones/${CF_ZONE_ID}/dns_records/${rec_id}" >/dev/null
            cf_api POST "/zones/${CF_ZONE_ID}/dns_records" "$data" >/dev/null
            log "  Replaced ${rec_type} → CNAME: ${fqdn} → ${TUNNEL_CNAME}"
        else
            cf_api PATCH "/zones/${CF_ZONE_ID}/dns_records/${rec_id}" "$data" >/dev/null
            log "  Updated CNAME: ${fqdn} → ${TUNNEL_CNAME}"
        fi
    else
        cf_api POST "/zones/${CF_ZONE_ID}/dns_records" "$data" >/dev/null
        log "  Created CNAME: ${fqdn} → ${TUNNEL_CNAME}"
    fi
}

upsert_cname "${CF_DOMAIN}"
upsert_cname "api.${CF_DOMAIN}"
upsert_cname "mcp.${CF_DOMAIN}"

# ============================================================
# Step 6: Start Cloudflare Tunnel (systemd user service)
# ============================================================
log ""
log "=== Step 6: Start Cloudflare Tunnel ==="

mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/cloudflared-openinfra.service << EOF
[Unit]
Description=Cloudflare Tunnel for ${CF_DOMAIN}
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$(which cloudflared) tunnel --config ${TUNNEL_CONFIG} run ${TUNNEL_NAME}
Restart=always
RestartSec=5
Environment="NO_AUTOUPDATE=true"

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable cloudflared-openinfra.service
systemctl --user restart cloudflared-openinfra.service

# Enable linger so service persists after logout
loginctl enable-linger "$(whoami)" 2>/dev/null || true

sleep 3
if systemctl --user is-active --quiet cloudflared-openinfra.service; then
    log "Tunnel running as systemd user service"
else
    error "Tunnel service failed to start"
fi

# ============================================================
# Step 7: Verify
# ============================================================
log ""
log "=== Step 7: Verify deployment ==="

sleep 5

check_url() {
    local url="$1" label="$2"
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$url" 2>/dev/null) || status="000"
    if [[ "$status" =~ ^[23] ]]; then
        echo -e "  ${GREEN}✓${NC} ${label}: ${url} (${status})"
    else
        echo -e "  ${RED}✗${NC} ${label}: ${url} (${status})"
    fi
}

check_url "https://${CF_DOMAIN}" "Frontend"
check_url "https://api.${CF_DOMAIN}/docs" "API Docs"
check_url "https://mcp.${CF_DOMAIN}/health" "MCP Server"

log ""
log "=== Deployment Complete ==="
log "Frontend:   https://${CF_DOMAIN}"
log "API:        https://api.${CF_DOMAIN}"
log "MCP:        https://mcp.${CF_DOMAIN}"
log ""
log "Cloudflare Tunnel: ${TUNNEL_NAME} (${TUNNEL_ID})"
log "  Tunnel service: systemctl --user status cloudflared-openinfra"
log "  Docker services: cd infra && docker compose ps"
log "  SSL cert renew:  docker compose run --rm certbot renew"
