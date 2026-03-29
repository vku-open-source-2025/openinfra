"""
Celery task: Auto-refresh DNS when WAN IP changes.

Uses autoip to detect public IP from the router,
then updates Cloudflare DNS A records via API.
"""

import os
import logging
import json
import urllib.request
import urllib.error
import sys

# Add autoip to path (mounted at /app/3rd_party in Docker)
_autoip_paths = [
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "3rd_party", "autoip"),  # local dev
    "/app/3rd_party/autoip",  # Docker
]
for _p in _autoip_paths:
    _abs = os.path.abspath(_p)
    if os.path.isdir(_abs) and _abs not in sys.path:
        sys.path.insert(0, _abs)

from app.celery_app import app

logger = logging.getLogger(__name__)


def _is_private_ip(ip: str) -> bool:
    """Check if IP is private/CGNAT (not routable on internet)."""
    parts = ip.split(".")
    if len(parts) != 4:
        return True
    first, second = int(parts[0]), int(parts[1])
    # 10.x.x.x (CGNAT / private)
    if first == 10:
        return True
    # 172.16-31.x.x
    if first == 172 and 16 <= second <= 31:
        return True
    # 192.168.x.x
    if first == 192 and second == 168:
        return True
    # 100.64-127.x.x (CGNAT RFC 6598)
    if first == 100 and 64 <= second <= 127:
        return True
    return False


def get_public_ip_from_internet() -> str | None:
    """Fallback: detect public IP via internet services."""
    import ssl
    ctx = ssl.create_default_context()
    for url in [
        "https://api.ipify.org",
        "https://ifconfig.me",
        "https://icanhazip.com",
        "https://checkip.amazonaws.com",
    ]:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                ip = resp.read().decode().strip()
                if ip and not _is_private_ip(ip):
                    return ip
        except Exception:
            continue
    return None


def get_wan_ip_from_router() -> str:
    """Detect WAN IP from router using autoip library.
    Falls back to internet detection if router returns private/CGNAT IP.
    """
    from autoip.routers.viettel_h646gm import ViettelH646GM

    host = os.getenv("AUTOIP_HOST", "192.168.1.1")
    port = int(os.getenv("AUTOIP_PORT", "1443"))
    username = os.getenv("AUTOIP_USERNAME", "admin")
    password = os.getenv("AUTOIP_PASSWORD", "user@123456")

    try:
        router = ViettelH646GM(
            host=host,
            port=port,
            username=username,
            password=password,
        )

        with router:
            ip = router.get_wan_ip()
            logger.info(f"Router WAN IP: {ip}")

            if _is_private_ip(ip):
                logger.info("Router IP is private/CGNAT, falling back to internet detection")
                public_ip = get_public_ip_from_internet()
                if public_ip:
                    logger.info(f"Public IP from internet: {public_ip}")
                    return public_ip
                logger.warning("Internet detection also failed, using router IP anyway")
            return ip
    except Exception as e:
        logger.warning(f"Router detection failed: {e}, trying internet detection")
        public_ip = get_public_ip_from_internet()
        if public_ip:
            return public_ip
        raise


def cloudflare_api(method: str, endpoint: str, data: dict = None) -> dict:
    """Call Cloudflare API."""
    token = os.getenv("CF_API_TOKEN", "")
    url = f"https://api.cloudflare.com/client/v4{endpoint}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        logger.error(f"Cloudflare API error {e.code}: {error_body}")
        raise


def get_dns_record(zone_id: str, fqdn: str) -> dict | None:
    """Get existing DNS A record."""
    result = cloudflare_api("GET", f"/zones/{zone_id}/dns_records?type=A&name={fqdn}")
    records = result.get("result", [])
    return records[0] if records else None


def upsert_dns_record(zone_id: str, fqdn: str, ip: str, proxied: bool = True) -> bool:
    """Create or update DNS A record."""
    record_data = {
        "type": "A",
        "name": fqdn,
        "content": ip,
        "ttl": 1,  # Auto
        "proxied": proxied,
    }

    existing = get_dns_record(zone_id, fqdn)

    if existing:
        if existing["content"] == ip:
            logger.info(f"  {fqdn}: already {ip}, skipping")
            return False
        result = cloudflare_api("PUT", f"/zones/{zone_id}/dns_records/{existing['id']}", record_data)
    else:
        result = cloudflare_api("POST", f"/zones/{zone_id}/dns_records", record_data)

    if result.get("success"):
        logger.info(f"  {fqdn}: updated to {ip}")
        return True
    else:
        logger.error(f"  {fqdn}: failed - {result.get('errors')}")
        return False


@app.task(name="auto_refresh_dns", bind=True, max_retries=3)
def auto_refresh_dns(self):
    """
    Detect WAN IP from router and update Cloudflare DNS records.
    Runs every hour via Celery Beat.
    """
    try:
        # Get config
        zone_id = os.getenv("CF_ZONE_ID", "")
        domain = os.getenv("CF_DOMAIN", "openinfra.space")
        records_str = os.getenv("CF_RECORDS", "@ api mcp")
        proxied = os.getenv("CF_PROXIED", "true").lower() == "true"

        if not zone_id:
            logger.error("CF_ZONE_ID not set, skipping DNS refresh")
            return {"status": "error", "message": "CF_ZONE_ID not configured"}

        # Detect IP from router
        wan_ip = get_wan_ip_from_router()

        if not wan_ip:
            logger.error("Could not detect WAN IP")
            return {"status": "error", "message": "IP detection failed"}

        # Update each record
        updated = 0
        skipped = 0
        failed = 0

        for record_name in records_str.split():
            fqdn = domain if record_name == "@" else f"{record_name}.{domain}"
            try:
                if upsert_dns_record(zone_id, fqdn, wan_ip, proxied):
                    updated += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.error(f"  {fqdn}: error - {e}")
                failed += 1

        result = {
            "status": "success",
            "wan_ip": wan_ip,
            "updated": updated,
            "skipped": skipped,
            "failed": failed,
        }
        logger.info(f"DNS refresh complete: {result}")
        return result

    except Exception as exc:
        logger.exception(f"DNS refresh failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
