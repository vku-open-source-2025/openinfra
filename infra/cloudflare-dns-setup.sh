#!/bin/bash
# ============================================================
# Cloudflare DNS Setup Script
# Registers/updates A records for openinfra.space subdomains
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load config
ENV_FILE="${SCRIPT_DIR}/.env.cloudflare"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: Missing $ENV_FILE — copy from .env.cloudflare.example"
    exit 1
fi
source "$ENV_FILE"

CF_DOMAIN="${CF_DOMAIN:-openinfra.space}"
CF_RECORDS="${CF_RECORDS:-@ api mcp}"
CF_PROXIED="${CF_PROXIED:-true}"
CF_TTL="${CF_TTL:-1}"

# ============================================================
# Helpers
# ============================================================
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

get_record() {
    local fqdn="$1"
    cf_api GET "/zones/${CF_ZONE_ID}/dns_records?type=A&name=${fqdn}"
}

upsert_record() {
    local name="$1" ip="$2"
    local fqdn
    [[ "$name" == "@" ]] && fqdn="${CF_DOMAIN}" || fqdn="${name}.${CF_DOMAIN}"

    local proxied_py
    [[ "${CF_PROXIED}" == "true" ]] && proxied_py="True" || proxied_py="False"

    local data
    data=$(python3 -c "
import json
print(json.dumps({
    'type': 'A',
    'name': '$fqdn',
    'content': '$ip',
    'ttl': ${CF_TTL},
    'proxied': ${proxied_py}
}))
")

    local existing_id
    existing_id=$(get_record "$fqdn" | python3 -c "
import sys, json
r = json.load(sys.stdin)
print(r['result'][0]['id'] if r.get('result') else '')
" 2>/dev/null)

    local result
    if [[ -n "$existing_id" ]]; then
        result=$(cf_api PUT "/zones/${CF_ZONE_ID}/dns_records/${existing_id}" "$data")
        echo "  Updated ${fqdn} → ${ip}"
    else
        result=$(cf_api POST "/zones/${CF_ZONE_ID}/dns_records" "$data")
        echo "  Created ${fqdn} → ${ip}"
    fi

    local success
    success=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
    [[ "$success" == "True" ]] && return 0 || { echo "  FAILED: $(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('errors', []))" 2>/dev/null)"; return 1; }
}

# ============================================================
# Main
# ============================================================
IP="${1:-}"

if [[ -z "$IP" ]]; then
    echo "Usage: $0 <IP_ADDRESS>"
    echo ""
    echo "Detect IP automatically from router:"
    echo "  cd 3rd_party/autoip && python -m autoip"
    echo ""
    echo "Or detect from internet:"
    echo "  $0 \$(curl -s https://api.ipify.org)"
    exit 1
fi

echo "=== Cloudflare DNS Setup ==="
echo "Domain:  ${CF_DOMAIN}"
echo "IP:      ${IP}"
echo "Proxied: ${CF_PROXIED}"
echo "Records: ${CF_RECORDS}"
echo ""

for record in $CF_RECORDS; do
    upsert_record "$record" "$IP"
done

echo ""
echo "Done. DNS propagation may take a few minutes."
echo "Verify: dig +short openinfra.space"
