"""Main FastAPI application module for FreshTrace."""

from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.history import router as history_router
from app.api.routes.verify import router as verify_router
from app.config import get_settings
from app.core.logging import logger
from app.database.session import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Initializing FreshTrace database tables...")
    init_db()
    logger.info("FreshTrace backend started successfully.")
    yield
    logger.info("FreshTrace backend shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description="FreshTrace - AI Answer Freshness Verification System. Detects potentially outdated, inaccurate, or unsupported claims inside AI-generated answers.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(health_router)
app.include_router(verify_router)
app.include_router(history_router)


@app.get("/", tags=["General"])
def root() -> Dict[str, str]:
    """Root endpoint welcoming API users and providing docs location."""
    return {
        "message": "Welcome to FreshTrace API - AI Answer Freshness Verification System",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "version": settings.APP_VERSION,
    }
