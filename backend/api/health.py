"""Health check endpoint."""

import time
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from config.settings import get_settings
from core.constants import STATUS_HEALTHY

router = APIRouter(tags=["health"])

# Track application start time
_start_time: float = time.time()


@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Health Check",
    description="Returns the current health status of the application.",
)
async def health_check() -> Dict[str, Any]:
    """Perform application health check.

    Returns:
        Health status with uptime and environment info.
    """
    settings = get_settings()
    uptime_seconds = time.time() - _start_time

    return {
        "status": STATUS_HEALTHY,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(uptime_seconds, 2),
        "environment": settings.environment.value,
        "version": settings.app_version,
        "checks": {
            "app": STATUS_HEALTHY,
        },
    }


@router.get(
    "/ping",
    summary="Ping",
    description="Simple liveness probe.",
)
async def ping() -> Dict[str, str]:
    """Simple liveness probe.

    Returns:
        Pong response.
    """
    return {"status": "pong"}
