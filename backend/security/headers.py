"""Security headers middleware.

Automatically adds production security headers to all responses:
X-Frame-Options, X-Content-Type-Options, Referrer-Policy,
Permissions-Policy, Content-Security-Policy, Strict-Transport-Security.
"""

from __future__ import annotations

import os

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

SECURITY_HEADERS_ENABLED = os.environ.get("SECURITY_HEADERS_ENABLED", "true").lower() == "true"

# Default security headers
SECURITY_HEADERS: dict[str, str] = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to all HTTP responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process request and add security headers to response."""
        response = await call_next(request)
        if SECURITY_HEADERS_ENABLED:
            for header, value in SECURITY_HEADERS.items():
                response.headers[header] = value
        return response
