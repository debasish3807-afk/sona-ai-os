"""Authentication middleware for the API Gateway."""

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()

# Paths that do not require authentication
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class AuthenticationMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    """Middleware that validates API keys on protected endpoints."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Check authentication for non-public paths."""
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Authentication logic placeholder - will integrate with security service
        logger.debug("auth.check", path=request.url.path, method=request.method)
        return await call_next(request)
