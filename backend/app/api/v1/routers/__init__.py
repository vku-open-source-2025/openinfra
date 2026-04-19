"""API v1 routers."""
from fastapi import APIRouter
from app.api.v1.routers import (
	assets,
	maintenance,
	ingest,
	auth,
	users,
	geo,
	iot,
	alerts,
	incidents,
	budgets,
	public,
	notifications,
	reports,
	linked_data,
	map_proxy,
	emergency,
	emergency_stream,
	eop,
	dispatch,
	resources,
	sitrep,
	hazards,
	geofences,
	after_action_reports,
)

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
# Sub-routers under /emergency/* MUST come before the base emergency router
# to prevent /{event_id} from swallowing paths like /emergency/eop
api_router.include_router(eop.router, prefix="/emergency/eop", tags=["Emergency EOP"])
api_router.include_router(
	dispatch.router,
	prefix="/emergency/dispatch",
	tags=["Emergency Dispatch"],
)
api_router.include_router(
	resources.router,
	prefix="/emergency/resources",
	tags=["Emergency Resources"],
)
api_router.include_router(
	sitrep.router,
	prefix="/emergency/sitrep",
	tags=["Emergency Sitrep"],
)
api_router.include_router(
	after_action_reports.router,
	prefix="/emergency/after-action",
	tags=["Emergency After Action"],
)
api_router.include_router(
	emergency_stream.router,
	prefix="/emergency/stream",
	tags=["Emergency Stream"],
)
api_router.include_router(emergency.router, prefix="/emergency", tags=["Emergency"])
api_router.include_router(
	hazards.router,
	prefix="/hazards",
	tags=["Hazards"],
)
api_router.include_router(
	geofences.router,
	prefix="/geofences",
	tags=["Geofences"],
)
api_router.include_router(budgets.router, prefix="/budgets", tags=["Budgets"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(public.router, prefix="/public", tags=["Public"])
api_router.include_router(linked_data.router, prefix="/ld", tags=["NGSI-LD"])
api_router.include_router(map_proxy.router, prefix="/map", tags=["Map Tiles"])
