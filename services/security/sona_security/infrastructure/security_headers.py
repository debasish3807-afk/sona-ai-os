"""Security headers configuration.

Provides security-related HTTP headers including HSTS, CSP,
X-Content-Type-Options, X-Frame-Options, and X-Request-ID.
"""

import os
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger()


@dataclass
class SecurityHeadersConfig:
    """Configuration for security headers."""

    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False
    frame_options: str = "DENY"
    content_type_nosniff: bool = True
    xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    csp_directives: dict[str, str] = field(
        default_factory=lambda: {
            "default-src": "'self'",
            "script-src": "'self'",
            "style-src": "'self' 'unsafe-inline'",
            "img-src": "'self' data:",
            "font-src": "'self'",
            "connect-src": "'self'",
            "frame-ancestors": "'none'",
        }
    )
    permissions_policy: str = "geolocation=(), microphone=(), camera=()"
    add_request_id: bool = True


class SecurityHeaders:
    """Security headers provider."""

    def __init__(self, config: SecurityHeadersConfig | None = None) -> None:
        self._config = config or SecurityHeadersConfig()

    def get_headers(self, request_id: str | None = None) -> dict[str, str]:
        """Get all security headers as a dictionary."""
        headers: dict[str, str] = {}

        # HSTS
        hsts_value = f"max-age={self._config.hsts_max_age}"
        if self._config.hsts_include_subdomains:
            hsts_value += "; includeSubDomains"
        if self._config.hsts_preload:
            hsts_value += "; preload"
        headers["Strict-Transport-Security"] = hsts_value

        # X-Frame-Options
        headers["X-Frame-Options"] = self._config.frame_options

        # X-Content-Type-Options
        if self._config.content_type_nosniff:
            headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection
        headers["X-XSS-Protection"] = self._config.xss_protection

        # Referrer-Policy
        headers["Referrer-Policy"] = self._config.referrer_policy

        # Content-Security-Policy
        csp_parts = [f"{key} {value}" for key, value in self._config.csp_directives.items()]
        headers["Content-Security-Policy"] = "; ".join(csp_parts)

        # Permissions-Policy
        headers["Permissions-Policy"] = self._config.permissions_policy

        # X-Request-ID
        if self._config.add_request_id:
            rid = request_id or self._generate_request_id()
            headers["X-Request-ID"] = rid

        return headers

    def _generate_request_id(self) -> str:
        """Generate a unique request ID."""
        return os.urandom(16).hex()
