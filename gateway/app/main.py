"""Sona AI OS API Gateway - FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI

from app.middleware.cors import setup_cors
from app.routes import chat, health, models, providers

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("gateway.startup", service="sona-gateway")
    yield
    logger.info("gateway.shutdown", service="sona-gateway")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Sona AI OS Gateway",
        description="API Gateway for Sona AI OS services",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Setup middleware
    setup_cors(app)

    # Register routes
    app.include_router(health.router, tags=["health"])
    app.include_router(chat.router, prefix="/v1", tags=["chat"])
    app.include_router(models.router, prefix="/v1", tags=["models"])
    app.include_router(providers.router, prefix="/v1", tags=["providers"])

    return app


app = create_app()
