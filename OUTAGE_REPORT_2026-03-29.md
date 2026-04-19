# Outage Report — OpenInfra Platform

**Date**: 2026-03-29  
**Duration**: ~4 days 18 hours (2026-03-24 ~13:54 UTC → 2026-03-29 ~12:23 UTC)  
**Impact**: Full platform outage — all public services unreachable  
**Trigger**: Network change (ISP/router reconfiguration)

---

## Timeline

| Time (UTC) | Event |
|---|---|
| 2026-03-24 13:53:58 | Network change occurs. Server loses connectivity. |
| 2026-03-24 13:53:58 | 9 containers with `restart: no` stop and do not recover: `mongo`, `redis`, `backend`, `celery-worker`, `celery-beat`, `zookeeper`, `kafka`, `iot-producer`, `iot-consumer`, `certbot` |
| 2026-03-24 13:53:58 | `nginx` (restart: unless-stopped) enters crash loop — upstream `backend:8000` unreachable |
| 2026-03-24 ~14:00 | Docker daemon detects: *"No non-localhost DNS nameservers are left in resolv.conf"* — repeated every ~60s |
| 2026-03-29 04:21 | Server reboots (manually or via power cycle). System uptime starts. |
| 2026-03-29 04:21:48 | 5 containers with `restart: always` or `restart: unless-stopped` auto-start: `frontend`, `mcp-server`, `mongo-express`, `datacollector-*`, `n8n` |
| 2026-03-29 04:21:48 | 9 containers with `restart: no` remain stopped — no auto-recovery |
| 2026-03-29 04:21:48 | `nginx` restarts but crash loops: `host not found in upstream "backend:8000"` |
| 2026-03-29 12:23 | Manual intervention: `docker compose up -d` restores all services |
| 2026-03-29 12:23:56 | Kafka fails to start: `KeeperErrorCode = NodeExists` (stale ZooKeeper ephemeral node) |
| 2026-03-29 12:23:38 | IoT consumer fails: `Connect call failed ('kafka', 29092)` — Kafka not ready |
| 2026-03-29 12:27 | Manual restart of Kafka + IoT consumer. All 14 services operational. |

---

## Root Cause Analysis

### Primary Cause: Missing Docker Restart Policies

**10 of 14 services** have no restart policy (`restart: no` — Docker default). When the network disruption caused container exits, these services never recovered — not after connectivity restored, not even after a full server reboot.

| Service | Restart Policy | Auto-Recovered? |
|---|---|---|
| mongo | **NOT SET** | No |
| redis | **NOT SET** | No |
| backend | **NOT SET** | No |
| celery-worker | **NOT SET** | No |
| celery-beat | **NOT SET** | No |
| zookeeper | **NOT SET** | No |
| kafka | **NOT SET** | No |
| iot-producer | **NOT SET** | No |
| iot-consumer | **NOT SET** | No |
| certbot | **NOT SET** | No |
| frontend | `always` | Yes |
| mcp-server | `unless-stopped` | Yes |
| mongo-express | `unless-stopped` | Yes |
| nginx | `unless-stopped` | Yes (but crash-looped due to backend dependency) |

### Secondary Cause: Hard Upstream Dependencies in Nginx

Nginx uses direct upstream references (`proxy_pass http://backend:8000`). When `backend` is not running, nginx refuses to start entirely — it cannot resolve the hostname at config parse time. This turns a backend outage into a total frontend outage.

### Contributing Cause: DNS Resolver Failure

Docker daemon logged repeatedly: `"No non-localhost DNS nameservers are left in resolv.conf"`. The network change likely disrupted `systemd-resolved`, which caused Docker's embedded DNS to lose upstream resolvers. This may have exacerbated container failures that depend on external network access.

### Tertiary: Kafka/ZooKeeper Stale State

After restart, Kafka failed with `KeeperErrorCode = NodeExists` — a stale ephemeral node from the previous broker session still existed in ZooKeeper. Required manual restart to clear.

---

## Impact Assessment

| Affected Service | Downtime |
|---|---|
| openinfra.space (frontend) | ~4 days 18h (nginx crash loop) |
| api.openinfra.space (API) | ~4 days 18h (backend down) |
| mcp.openinfra.space (MCP) | Partial — container was up but nginx couldn't proxy |
| IoT pipeline (Kafka/sensors) | ~4 days 18h |
| Celery tasks (ETL, monitoring) | ~4 days 18h |
| Cloudflare Tunnel | **Unaffected** — reconnected automatically with new IP |
| DNS records | **Unaffected** — CNAME → tunnel (IP-independent) |
| datacollector (contribution.*) | **Unaffected** — restart: unless-stopped, separate stack |

---

## Recommended Fixes

### 1. Add `restart: unless-stopped` to All Services (Critical)

The single most impactful fix. Every service in `docker-compose.yml` should have:

```yaml
restart: unless-stopped
```

Services that need it added: `mongo`, `redis`, `backend`, `celery-worker`, `celery-beat`, `zookeeper`, `kafka`, `iot-producer`, `iot-consumer`, `certbot`.

### 2. Use Nginx `resolver` Directive for Dynamic Upstreams

Replace hard upstream hostnames with a `resolver` + `set` pattern so nginx starts even when backends are down:

```nginx
resolver 127.0.0.11 valid=10s;  # Docker DNS
set $backend "backend:8000";
proxy_pass http://$backend;
```

This allows nginx to start without backends and retry DNS resolution dynamically.

### 3. Add Health Checks and Dependency Conditions

```yaml
backend:
  depends_on:
    mongo:
      condition: service_healthy
    redis:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3

nginx:
  depends_on:
    backend:
      condition: service_healthy
```

### 4. Configure Static DNS for Docker Daemon

Add to `/etc/docker/daemon.json`:
```json
{
  "dns": ["8.8.8.8", "1.1.1.1"]
}
```

This prevents Docker from losing DNS when `systemd-resolved` is disrupted.

### 5. Set Up a Monitoring/Alerting Mechanism

A simple uptime check (e.g., cron job that curls the site and sends a notification on failure) would have caught this outage within minutes instead of days.

---

## Current Status (Post-Recovery)

| Service | Status | Health |
|---|---|---|
| openinfra.space | ✅ HTTP 200 | Operational |
| api.openinfra.space/docs | ✅ HTTP 200 | Operational |
| Cloudflare Tunnel | ✅ 8 connections (Singapore edge) | Operational |
| All 14 Docker containers | ✅ Running | Operational |
| Public IP | 42.118.236.161 | New network |
| DNS (Cloudflare) | ✅ All 7 CNAMEs → tunnel | No changes needed |

---

*Report generated: 2026-03-29T12:30Z*  
*Team: VKU.OneLove*
