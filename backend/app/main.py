"""FastAPI application factory.

Creates and configures the FastAPI application with all middleware,
routes, and exception handlers.
"""

import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from api.router import create_api_router
from app.lifespan import lifespan
from config.settings import Settings, get_settings
from core.constants import HEADER_API_VERSION, HEADER_REQUEST_ID, HEADER_RESPONSE_TIME
from core.exceptions import register_exception_handlers


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    This is the application factory. It creates a new FastAPI instance
    with all middleware, routes, and handlers configured.

    Args:
        settings: Optional settings override. Uses cached singleton if None.

    Returns:
        Configured FastAPI application.
    """
    if settings is None:
        settings = get_settings()

    # Create FastAPI instance
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        docs_url=settings.docs_url if not settings.is_production else None,
        redoc_url=settings.redoc_url if not settings.is_production else None,
        openapi_url=settings.openapi_url if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Register middleware
    _register_middleware(app, settings)

    # Register exception handlers
    register_exception_handlers(app)

    # Register routes
    _register_routes(app, settings)

    return app


def _register_middleware(app: FastAPI, settings: Settings) -> None:
    """Register all middleware on the application.

    Args:
        app: FastAPI application instance.
        settings: Application settings.
    """
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Request ID and timing middleware
    @app.middleware("http")
    async def add_request_metadata(request: Request, call_next: object) -> Response:
        """Add request ID and response timing headers."""
        # Generate or extract request ID
        request_id = request.headers.get(HEADER_REQUEST_ID, str(uuid.uuid4()))

        # Track response time
        start_time = time.perf_counter()
        response: Response = await call_next(request)  # type: ignore[misc]
        process_time = time.perf_counter() - start_time

        # Add response headers
        response.headers[HEADER_REQUEST_ID] = request_id
        response.headers[HEADER_RESPONSE_TIME] = f"{process_time:.4f}s"
        response.headers[HEADER_API_VERSION] = settings.app_version

        return response


def _register_routes(app: FastAPI, settings: Settings) -> None:
    """Register all API routes.

    Args:
        app: FastAPI application instance.
        settings: Application settings.
    """
    # API v1 routes
    api_router = create_api_router()
    app.include_router(api_router, prefix=settings.api_prefix)


# Application instance for uvicorn
app = create_app()
