# SOSConn Production Checklist

This checklist is for validating SOSConn integration readiness on OpenInfra.

## Configuration

- [ ] Set `COPILOT_AUTH_HOST_PATH` in [infra/.env](infra/.env) to a persistent host folder.
- [ ] Ensure token file exists at `${COPILOT_AUTH_HOST_PATH}/token` with mode `600`.
- [ ] Set hazard feed URLs in [infra/.env](infra/.env):
  - `NCHMF_FEED_URL`
  - `VNDMS_FEED_URL`
  - `HAZARD_FEED_TIMEOUT`

## Service Health

- [ ] `docker compose ps` shows `llm-service`, `backend`, `frontend`, `celery-worker`, `celery-beat` as running.
- [ ] `GET http://127.0.0.1:8014/api/v1/ai/status` returns `"configured": true`.
- [ ] `GET /api/v1/emergency/sosconn/status` (with admin token) returns `"reachable": true`.

## Emergency Workflows

- [ ] Emergency events list loads on `/admin/emergency-center`.
- [ ] EOP draft generation works.
- [ ] Dispatch optimization works.
- [ ] Hazard map renders active hazards.
- [ ] Resolve event flow completes and creates/publishes after-action report.

## Scheduled Ingestion

- [ ] Celery beat schedules `ingest_nchmf_data`, `ingest_vndms_data`, and `ingest_hazard_feeds`.
- [ ] Celery logs do not show repeated ingest failures.
- [ ] Hazard ingestion produces non-zero records in normal operation.

## Suggested Validation Commands

```bash
cd infra

docker compose ps
curl -sS http://127.0.0.1:8014/api/v1/ai/status

docker compose logs celery-beat --tail 100
docker compose logs celery-worker --tail 200 | grep -Ei "hazard|ingest|error"
```
