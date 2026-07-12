"""API router factory — assembles all route modules."""

from fastapi import APIRouter

from api.chat import router as chat_router
from api.health import router as health_router
from api.tools import router as tools_router
from api.version import router as version_router


def create_api_router() -> APIRouter:
    """Create and configure the main API router.

    Assembles all sub-routers into a unified API router
    with proper prefixing and tagging.

    Returns:
        Configured APIRouter instance.
    """
    api_router = APIRouter()

    # Health and system routes
    api_router.include_router(health_router)
    api_router.include_router(version_router)

    # AI Brain chat routes
    api_router.include_router(chat_router)

    # MCP Tool system routes
    api_router.include_router(tools_router)

    return api_router
