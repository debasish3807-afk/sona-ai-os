"""FastAPI application factory.

Creates and configures the FastAPI application with all middleware,
routes, exception handlers, and production security stack.
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
from security.middleware import (
    AuditMiddleware,
    AuthMiddleware,
    CorrelationIDMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)


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

    Middleware executes in reverse registration order (last registered = outermost).
    Order: CorrelationID → SecurityHeaders → Auth → RateLimit → Audit → CORS → Request metadata.

    Args:
        app: FastAPI application instance.
        settings: Application settings.
    """
    from security.api_keys import APIKeyManager
    from security.audit import AuditLogger
    from security.rate_limit import RateLimiter

    # Security middleware stack (registered last = executes first)
    audit_logger = AuditLogger()
    rate_limiter = RateLimiter()
    key_manager = APIKeyManager()

    # Audit logging (innermost — captures response status)
    app.add_middleware(AuditMiddleware, audit_logger=audit_logger)

    # Rate limiting
    app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

    # Authentication (skip public paths: /health, /ping, /docs, /openapi.json)
    app.add_middleware(AuthMiddleware, key_manager=key_manager)

    # Security headers (HSTS, X-Frame-Options, etc.)
    app.add_middleware(SecurityHeadersMiddleware)

    # Correlation ID (outermost — generates/propagates trace ID)
    app.add_middleware(CorrelationIDMiddleware)

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
    async def add_request_metadata(request: Request, call_next):  # type: ignore[no-untyped-def]
        """Add request ID and response timing headers."""
        request_id = request.headers.get(HEADER_REQUEST_ID, str(uuid.uuid4()))

        start_time = time.perf_counter()
        response: Response = await call_next(request)
        process_time = time.perf_counter() - start_time

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
    api_router = create_api_router()
    app.include_router(api_router, prefix=settings.api_prefix)


# Application instance for uvicorn
app = create_app()
