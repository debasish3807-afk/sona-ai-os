"""Application lifespan management.

Handles startup and shutdown events for the FastAPI application.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config.logging import get_logger, setup_logging
from config.settings import get_settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events.

    Handles resource initialization on startup and cleanup on shutdown.

    Args:
        app: FastAPI application instance.

    Yields:
        None - application runs between startup and shutdown.
    """
    # === STARTUP ===
    settings = get_settings()
    setup_logging(settings)

    logger.info(
        "Application starting",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment.value,
        debug=settings.debug,
    )

    # Future: Initialize database connections
    # Future: Initialize cache connections
    # Future: Initialize AI providers
    # Future: Start background tasks

    logger.info("Application started successfully")

    yield

    # === SHUTDOWN ===
    logger.info("Application shutting down")

    # Future: Close database connections
    # Future: Close cache connections
    # Future: Cleanup AI provider sessions
    # Future: Cancel background tasks

    logger.info("Application shutdown complete")
