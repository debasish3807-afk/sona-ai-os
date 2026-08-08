"""Authentication middleware for the API Gateway.

Enforces JWT Bearer token authentication on all protected endpoints.
Uses the security service's validate_token() which verifies:
- HMAC-SHA256 signature
- Token expiration
- Token revocation status
"""

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from sona_security.infrastructure.jwt_service import JWTConfig, JWTService

logger = structlog.get_logger()

# Paths that do not require authentication (health/infra endpoints)
PUBLIC_PATHS: set[str] = {
    "/health",
    "/ready",
    "/health/detailed",
    "/docs",
    "/openapi.json",
    "/redoc",
}

# Prefixes that are public (health variants with trailing slashes etc.)
PUBLIC_PREFIXES: tuple[str, ...] = ("/health",)


def _is_public_path(path: str) -> bool:
    """Check if a request path is public (no auth required)."""
    if path in PUBLIC_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


def _create_jwt_service() -> JWTService:
    """Create a JWTService from environment configuration."""
    import os

    secret = os.environ.get("SONA_JWT_SECRET", "dev-secret-change-in-production")
    return JWTService(JWTConfig(secret=secret))


# Module-level JWT service instance
_jwt_service: JWTService | None = None


def _get_jwt_service() -> JWTService:
    """Get or create the JWT service singleton."""
    global _jwt_service  # noqa: PLW0603
    if _jwt_service is None:
        _jwt_service = _create_jwt_service()
    return _jwt_service


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces JWT Bearer token authentication.

    Public endpoints (health, docs) are accessible without authentication.
    All other endpoints require a valid Authorization: Bearer <JWT> header.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Authenticate requests to protected endpoints."""
        path = request.url.path

        # Allow public endpoints without authentication
        if _is_public_path(path):
            return await call_next(request)

        # Extract Authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header:
            logger.warning("auth.missing_header", path=path, method=request.method)
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing Authorization header"},
            )

        # Validate Bearer token format
        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning("auth.malformed_header", path=path)
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid Authorization header format. Expected: Bearer <token>"},
            )

        token = parts[1]

        # Validate token using secure validation (signature + expiry + revocation)
        try:
            jwt_service = _get_jwt_service()
            claims = jwt_service.validate_token(token)

            if claims is None:
                logger.warning("auth.invalid_token", path=path, method=request.method)
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or expired token"},
                )

            # Attach user claims to request state for downstream use
            request.state.user_id = str(claims.get("sub", ""))
            request.state.roles = claims.get("roles", [])
            request.state.token_claims = claims

            logger.debug(
                "auth.authenticated",
                path=path,
                user_id=request.state.user_id,
            )

        except Exception as exc:
            logger.error("auth.middleware_error", path=path, error=str(exc))
            return JSONResponse(
                status_code=500,
                content={"detail": "Authentication service error"},
            )

        return await call_next(request)
