"""Application lifespan management.

Handles startup and shutdown events for the FastAPI application,
including DI container initialization and AI Brain setup.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config.logging import get_logger, setup_logging
from config.settings import get_settings

logger = get_logger(__name__)

_SHUTDOWN_TIMEOUT = 30  # seconds


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events.

    Handles resource initialization on startup and cleanup on shutdown.
    Initializes the DI container and AI Brain with all providers.

    Critical failures in DI container or AI Brain initialization
    are re-raised so the application fails to start in a broken state.

    Args:
        app: FastAPI application instance.

    Yields:
        None - application runs between startup and shutdown.

    Raises:
        RuntimeError: If DI container or AI Brain initialization fails.
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

    # Initialize DI Container (all subsystems)
    from core.container import get_container
    from core.service_registration import register_all_services

    try:
        container = get_container()
        await container.initialize()
        register_all_services(container)
        logger.info("DI Container initialized successfully")
    except Exception as exc:
        logger.error("Container initialization failed", error=str(exc))
        logger.info("Application startup aborted due to container initialization failure")
        raise RuntimeError(f"DI Container initialization failed: {exc}") from exc

    # Initialize AI Brain (providers, memory, routing)
    from brain.orchestrator import initialize_brain

    try:
        await initialize_brain()
        logger.info("AI Brain initialized successfully")
    except Exception as exc:
        logger.error("AI Brain initialization failed", error=str(exc))
        logger.info("Application startup aborted due to AI Brain initialization failure")
        raise RuntimeError(f"AI Brain initialization failed: {exc}") from exc

    logger.info("Application started successfully")

    yield

    # === SHUTDOWN ===
    logger.info("Application shutting down")

    # Shutdown DI Container with timeout
    try:
        container = get_container()
        await asyncio.wait_for(container.shutdown(), timeout=_SHUTDOWN_TIMEOUT)
        logger.info("DI Container shut down successfully")
    except TimeoutError:
        logger.warning("Container shutdown timed out after %ds", _SHUTDOWN_TIMEOUT)
    except Exception as exc:
        logger.warning("Container shutdown error", error=str(exc))

    # Shutdown AI Brain with timeout
    from brain.orchestrator import shutdown_brain

    try:
        await asyncio.wait_for(shutdown_brain(), timeout=_SHUTDOWN_TIMEOUT)
        logger.info("AI Brain shut down successfully")
    except TimeoutError:
        logger.warning("AI Brain shutdown timed out after %ds", _SHUTDOWN_TIMEOUT)
    except Exception as exc:
        logger.warning("AI Brain shutdown error", error=str(exc))

    logger.info("Application shutdown complete")
