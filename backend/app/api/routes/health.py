"""Health check and provider status endpoint."""

from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Check API operational status, database connectivity, and credential configuration."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "database_connected": db_ok,
        "providers": {
            "bifrost": {
                "configured": settings.is_bifrost_configured,
                "base_url": settings.BIFROST_BASE_URL,
                "model": settings.AI_MODEL,
                "provider": settings.AI_PROVIDER,
            },
            "tavily": {
                "configured": settings.is_tavily_configured,
                "base_url": settings.TAVILY_BASE_URL,
            },
        },
    }
