"""API v1 routers."""
from fastapi import APIRouter
from app.api.v1.routers import assets, maintenance, ingest, auth, users, geo, iot, alerts, incidents, budgets, public, notifications, reports, linked_data

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
api_router.include_router(geo.router, prefix="/geo", tags=["Geospatial"])
api_router.include_router(iot.router, prefix="/iot", tags=["IoT"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["Budgets"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(public.router, prefix="/public", tags=["Public"])
api_router.include_router(linked_data.router, prefix="/ld", tags=["Linked Data (JSON-LD)"])
