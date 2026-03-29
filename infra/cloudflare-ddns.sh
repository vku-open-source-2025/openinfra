#!/bin/bash
# Cloudflare DDNS Updater for openinfra.space
# Tự detect public IP và cập nhật DNS A records trên Cloudflare
#
# Usage:
#   ./cloudflare-ddns.sh              # Update all records
#   ./cloudflare-ddns.sh --check      # Chỉ kiểm tra, không update
#   ./cloudflare-ddns.sh --cron       # Silent mode cho crontab
#
# Crontab (mỗi 5 phút):
#   */5 * * * * /home/bobaonhan123/openinfra/infra/cloudflare-ddns.sh --cron >> /var/log/cloudflare-ddns.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load config from .env.cloudflare
ENV_FILE="${SCRIPT_DIR}/.env.cloudflare"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: Missing $ENV_FILE"
    echo "Create it with:"
    echo "  CF_API_TOKEN=your_api_token"
    echo "  CF_ZONE_ID=your_zone_id"
    echo "  CF_RECORDS=\"@ api mcp\""
    echo "  CF_DOMAIN=openinfra.space"
    echo "  CF_PROXIED=true"
    exit 1
fi
source "$ENV_FILE"

# Defaults
CF_DOMAIN="${CF_DOMAIN:-openinfra.space}"
CF_PROXIED="${CF_PROXIED:-true}"
CF_RECORDS="${CF_RECORDS:-@ api mcp}"
CF_TTL="${CF_TTL:-1}"  # 1 = Auto

MODE="${1:-}"
QUIET=false
CHECK_ONLY=false

if [[ "$MODE" == "--cron" ]]; then
    QUIET=true
elif [[ "$MODE" == "--check" ]]; then
    CHECK_ONLY=true
fi

log() {
    if [[ "$QUIET" == false ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    fi
}

log_always() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# ========== Detect public IP ==========
get_public_ip() {
    local ip=""
    # Try multiple services for reliability
    for service in \
        "https://api.ipify.org" \
        "https://ifconfig.me" \
        "https://icanhazip.com" \
        "https://checkip.amazonaws.com"; do
        ip=$(curl -s --max-time 5 "$service" 2>/dev/null | tr -d '[:space:]')
        if [[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "$ip"
            return 0
        fi
    done
    return 1
}

# ========== Cloudflare API helpers ==========
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
            -H "Authorization: Bearer ${CF_API_TOKEN}" \
            -H "Content-Type: application/json"
    fi
}

# Get DNS record ID by name
get_record_id() {
    local fqdn="$1"
    cf_api GET "/zones/${CF_ZONE_ID}/dns_records?type=A&name=${fqdn}" | \
        python3 -c "import sys,json; r=json.load(sys.stdin); print(r['result'][0]['id'] if r['result'] else '')" 2>/dev/null
}

# Get current DNS IP
get_record_ip() {
    local fqdn="$1"
    cf_api GET "/zones/${CF_ZONE_ID}/dns_records?type=A&name=${fqdn}" | \
        python3 -c "import sys,json; r=json.load(sys.stdin); print(r['result'][0]['content'] if r['result'] else '')" 2>/dev/null
}

# Create or update DNS record
upsert_record() {
    local name="$1" ip="$2"
    local fqdn
    
    if [[ "$name" == "@" ]]; then
        fqdn="${CF_DOMAIN}"
    else
        fqdn="${name}.${CF_DOMAIN}"
    fi
    
    local record_id
    record_id=$(get_record_id "$fqdn")
    
    local data
    data=$(python3 -c "
import json
print(json.dumps({
    'type': 'A',
    'name': '$fqdn',
    'content': '$ip',
    'ttl': ${CF_TTL},
    'proxied': ${CF_PROXIED}
}))
")
    
    local result
    if [[ -n "$record_id" ]]; then
        # Update existing
        result=$(cf_api PUT "/zones/${CF_ZONE_ID}/dns_records/${record_id}" "$data")
    else
        # Create new
        result=$(cf_api POST "/zones/${CF_ZONE_ID}/dns_records" "$data")
    fi
    
    local success
    success=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
    
    if [[ "$success" == "True" ]]; then
        return 0
    else
        local errors
        errors=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('errors', []))" 2>/dev/null)
        log "  ERROR: $errors"
        return 1
    fi
}

# ========== Main ==========

# Detect IP
CURRENT_IP=$(get_public_ip) || {
    log_always "ERROR: Cannot detect public IP"
    exit 1
}

log "Public IP: ${CURRENT_IP}"

# Check/update each record
UPDATED=0
SKIPPED=0
FAILED=0

for record in $CF_RECORDS; do
    if [[ "$record" == "@" ]]; then
        fqdn="${CF_DOMAIN}"
    else
        fqdn="${record}.${CF_DOMAIN}"
    fi
    
    # Get current DNS value
    dns_ip=$(get_record_ip "$fqdn")
    
    if [[ "$CHECK_ONLY" == true ]]; then
        if [[ -z "$dns_ip" ]]; then
            log "  ${fqdn}: NOT SET (need: ${CURRENT_IP})"
        elif [[ "$dns_ip" == "$CURRENT_IP" ]]; then
            log "  ${fqdn}: ${dns_ip} ✓"
        else
            log "  ${fqdn}: ${dns_ip} → needs update to ${CURRENT_IP}"
        fi
        continue
    fi
    
    if [[ "$dns_ip" == "$CURRENT_IP" ]]; then
        log "  ${fqdn}: already ${CURRENT_IP} ✓"
        ((SKIPPED++))
        continue
    fi
    
    if [[ -z "$dns_ip" ]]; then
        log "  ${fqdn}: creating → ${CURRENT_IP}"
    else
        log "  ${fqdn}: ${dns_ip} → ${CURRENT_IP}"
    fi
    
    if upsert_record "$record" "$CURRENT_IP"; then
        log "  ${fqdn}: updated ✓"
        ((UPDATED++))
    else
        log_always "  ${fqdn}: FAILED ✗"
        ((FAILED++))
    fi
done

if [[ "$CHECK_ONLY" == false ]]; then
    if [[ $UPDATED -gt 0 ]]; then
        log_always "Updated ${UPDATED} record(s), skipped ${SKIPPED}, failed ${FAILED}"
    elif [[ "$QUIET" == false ]]; then
        log "All ${SKIPPED} record(s) already up to date"
    fi
fi
