"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logging import setup_logging
from app.infrastructure.database.mongodb import db
from app.infrastructure.cache.redis_cache import cache
from app.api.v1.routers import api_router
from app.middleware.error_handler import error_handler_middleware
from app.middleware.logging_middleware import LoggingMiddleware

# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting application...")
    db.connect()
    try:
        await cache.get_client()  # Initialize Redis connection
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Continuing without cache.")

    # Initialize database indexes (only in development)
    if settings.DATABASE_NAME == "gis_db":
        try:
            from app.infrastructure.database.init_db import init_database

            await init_database()
        except Exception as e:
            logger.warning(f"Database initialization skipped: {e}")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    db.close()
    await cache.close()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan, version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.middleware("http")(error_handler_middleware)
app.add_middleware(LoggingMiddleware)

# API routes
app.include_router(api_router, prefix="/api/v1")

# AI Agent WebSocket router (separate from REST API)
from app.api.v1.routers.ai_agent import router as ai_agent_router
app.include_router(ai_agent_router, prefix="/api/v1")

# app.include_router(assets.router, prefix="/api/assets", tags=["Assets"])
# app.include_router(maintenance.router, prefix="/api/maintenance", tags=["Maintenance"])
# app.include_router(ingest.router, prefix="/api/ingest", tags=["Ingestion"])
# app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
# app.include_router(opendata.router, prefix="/api/opendata", tags=["Open Data (JSON-LD)"])
# app.include_router(iot.router, prefix="/api/iot", tags=["IoT Sensors"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Infrastructure Management System API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected" if db.client else "disconnected",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
