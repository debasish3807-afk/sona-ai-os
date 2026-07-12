"""Application lifespan management.

Handles startup and shutdown events for the FastAPI application,
including AI Brain initialization.
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
    Initializes the AI Brain with all providers.

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

    # Initialize AI Brain (providers, memory, routing)
    from brain.orchestrator import initialize_brain

    try:
        await initialize_brain()
        logger.info("AI Brain initialized successfully")
    except Exception as exc:
        logger.error("AI Brain initialization failed", error=str(exc))
        # Don't fail startup — Brain can initialize lazily

    logger.info("Application started successfully")

    yield

    # === SHUTDOWN ===
    logger.info("Application shutting down")

    # Shutdown AI Brain
    from brain.orchestrator import shutdown_brain

    try:
        await shutdown_brain()
        logger.info("AI Brain shut down successfully")
    except Exception as exc:
        logger.warning("AI Brain shutdown error", error=str(exc))

    logger.info("Application shutdown complete")
