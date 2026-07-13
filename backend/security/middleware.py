"""Security middleware stack for FastAPI/Starlette.

Provides authentication, rate limiting, audit logging, correlation IDs,
and security headers as composable middleware classes.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from config.logging import get_logger
from security.api_keys import APIKeyManager
from security.audit import AuditAction, AuditLogger
from security.rate_limit import RateLimiter

logger = get_logger(__name__)

# Endpoints that bypass authentication
_PUBLIC_PATHS: set[str] = {"/health", "/ping", "/docs", "/openapi.json"}


class AuthMiddleware(BaseHTTPMiddleware):
    """Validates API keys on incoming requests.

    Supports two header formats:
      - Authorization: Bearer <key>
      - X-API-Key: <key>

    Skips authentication for public endpoints (/health, /ping, /docs, /openapi.json).
    Returns 401 JSON response on failure.
    """

    def __init__(self, app: Any, key_manager: APIKeyManager) -> None:
        super().__init__(app)
        self._key_manager = key_manager

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip auth for public paths
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        # Extract API key from headers
        api_key = self._extract_key(request)
        if api_key is None:
            logger.warning("Missing API key", path=request.url.path)
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid authentication credentials"},
            )

        # Validate the key
        record = self._key_manager.validate_key(api_key)
        if record is None:
            logger.warning("Invalid API key", path=request.url.path)
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired API key"},
            )

        # Attach user info to request state for downstream use
        request.state.user_id = record.user_id
        request.state.key_id = record.key_id
        request.state.scopes = record.scopes

        return await call_next(request)

    @staticmethod
    def _extract_key(request: Request) -> str | None:
        """Extract API key from Authorization or X-API-Key header."""
        # Try Authorization: Bearer <key>
        auth_header: str | None = request.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            return auth_header[7:].strip()

        # Try X-API-Key header
        api_key_header: str | None = request.headers.get("x-api-key")
        if api_key_header:
            return api_key_header.strip()

        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforces per-client rate limits based on IP address.

    Returns 429 Too Many Requests with Retry-After header when exceeded.
    Rate limit headers (X-RateLimit-*) are added to all responses.
    """

    def __init__(self, app: Any, rate_limiter: RateLimiter) -> None:
        super().__init__(app)
        self._limiter = rate_limiter

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = self._get_client_ip(request)
        category = self._get_category(request)

        allowed, headers = self._limiter.check(client_ip, category)

        if not allowed:
            logger.warning(
                "Rate limit exceeded",
                ip=client_ip,
                path=request.url.path,
                category=category,
            )
            error_response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please retry later."},
            )
            for key, value in headers.items():
                error_response.headers[key] = value
            return error_response

        response = await call_next(request)

        # Add rate limit headers to successful responses
        for key, value in headers.items():
            response.headers[key] = value

        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP, respecting X-Forwarded-For."""
        forwarded_for: str | None = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # First IP in the chain is the original client
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return str(request.client.host)
        return "unknown"

    @staticmethod
    def _get_category(request: Request) -> str:
        """Map request path to rate limit category."""
        path = request.url.path.lower()
        if "/auth/login" in path:
            return "login"
        if "/auth/register" in path:
            return "register"
        if "/chat" in path:
            return "chat"
        if "/tools" in path:
            return "tools"
        if "/documents" in path:
            return "documents"
        if "/admin" in path:
            return "admin"
        return "default"


class AuditMiddleware(BaseHTTPMiddleware):
    """Logs request metadata for auditing and compliance.

    Records method, path, response status code, and duration
    for every request.
    """

    def __init__(self, app: Any, audit_logger: AuditLogger) -> None:
        super().__init__(app)
        self._audit_logger = audit_logger

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Determine user info if available
        user_id: str = getattr(request.state, "user_id", "")
        client_ip = self._get_client_ip(request)

        self._audit_logger.log_action(
            action=AuditAction.TOOL_EXECUTION,
            user_id=user_id,
            ip_address=client_ip,
            status="success" if response.status_code < 400 else "failure",
            metadata={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )

        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP, respecting X-Forwarded-For."""
        forwarded_for: str | None = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return str(request.client.host)
        return "unknown"


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Adds a correlation ID to every request and response.

    If the incoming request has an X-Correlation-ID header, it is reused.
    Otherwise a new UUID4 is generated. The ID is attached to both
    request.state and the response header for tracing.
    """

    HEADER_NAME: str = "X-Correlation-ID"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Use existing correlation ID or generate a new one
        correlation_id: str = request.headers.get(self.HEADER_NAME.lower(), "") or str(uuid.uuid4())

        # Attach to request state for downstream access
        request.state.correlation_id = correlation_id

        response = await call_next(request)

        # Always include in response
        response.headers[self.HEADER_NAME] = correlation_id

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds standard security headers to all responses.

    Headers added:
      - X-Content-Type-Options: nosniff
      - X-Frame-Options: DENY
      - Strict-Transport-Security: max-age=31536000; includeSubDomains
      - X-XSS-Protection: 1; mode=block
    """

    _SECURITY_HEADERS: dict[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-XSS-Protection": "1; mode=block",
    }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        for header, value in self._SECURITY_HEADERS.items():
            response.headers[header] = value

        return response


__all__ = [
    "AuthMiddleware",
    "RateLimitMiddleware",
    "AuditMiddleware",
    "CorrelationIDMiddleware",
    "SecurityHeadersMiddleware",
]
