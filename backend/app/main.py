from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.mongodb import db
from app.routers import assets, maintenance, ingest, opendata, iot
import app.routers.auth as auth

app = FastAPI(title=settings.PROJECT_NAME)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    db.connect()

@app.on_event("shutdown")
async def shutdown_db_client():
    db.close()

app.include_router(assets.router, prefix="/api/assets", tags=["Assets"])
app.include_router(maintenance.router, prefix="/api/maintenance", tags=["Maintenance"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["Ingestion"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(opendata.router, prefix="/api/opendata", tags=["Open Data (JSON-LD)"])
app.include_router(iot.router, prefix="/api/iot", tags=["IoT Sensors"])

@app.get("/")
async def root():
    return {"message": "Infrastructure Management System API"}
