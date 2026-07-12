"""Version information endpoint."""

import platform
import sys
from typing import Any

from fastapi import APIRouter

from config.settings import get_settings
from core.constants import API_VERSION

router = APIRouter(tags=["system"])


@router.get(
    "/version",
    response_model=dict[str, Any],
    summary="Version Information",
    description="Returns application version and system details.",
)
async def get_version() -> dict[str, Any]:
    """Get application version information.

    Returns:
        Version details including app version, API version, and runtime info.
    """
    settings = get_settings()

    return {
        "app": {
            "name": settings.app_name,
            "version": settings.app_version,
            "description": settings.app_description,
            "api_version": API_VERSION,
        },
        "runtime": {
            "python_version": sys.version.split()[0],
            "platform": platform.system(),
            "architecture": platform.machine(),
        },
    }
