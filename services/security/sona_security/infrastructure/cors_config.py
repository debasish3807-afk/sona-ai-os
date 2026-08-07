"""CORS (Cross-Origin Resource Sharing) configuration.

Provides configurable CORS settings including allowed origins,
methods, headers, and credential support.
"""

from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger()


@dataclass
class CORSConfig:
    """CORS configuration settings."""

    allowed_origins: list[str] = field(default_factory=lambda: ["http://localhost:3000"])
    allowed_methods: list[str] = field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    )
    allowed_headers: list[str] = field(
        default_factory=lambda: [
            "Authorization",
            "Content-Type",
            "X-Request-ID",
            "X-API-Key",
        ]
    )
    exposed_headers: list[str] = field(
        default_factory=lambda: [
            "X-Request-ID",
            "X-RateLimit-Remaining",
            "X-RateLimit-Limit",
            "X-RateLimit-Reset",
        ]
    )
    allow_credentials: bool = True
    max_age: int = 3600  # preflight cache in seconds


class CORSManager:
    """CORS policy manager."""

    def __init__(self, config: CORSConfig | None = None) -> None:
        self._config = config or CORSConfig()

    @property
    def config(self) -> CORSConfig:
        """Access the CORS configuration."""
        return self._config

    def is_origin_allowed(self, origin: str) -> bool:
        """Check if an origin is allowed."""
        if "*" in self._config.allowed_origins:
            return True
        return origin in self._config.allowed_origins

    def is_method_allowed(self, method: str) -> bool:
        """Check if an HTTP method is allowed."""
        return method.upper() in self._config.allowed_methods

    def get_cors_headers(self, origin: str) -> dict[str, str]:
        """Get CORS response headers for a given origin."""
        headers: dict[str, str] = {}

        if self.is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin
        elif "*" in self._config.allowed_origins:
            headers["Access-Control-Allow-Origin"] = "*"

        if self._config.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"

        headers["Access-Control-Allow-Methods"] = ", ".join(self._config.allowed_methods)
        headers["Access-Control-Allow-Headers"] = ", ".join(self._config.allowed_headers)
        headers["Access-Control-Expose-Headers"] = ", ".join(self._config.exposed_headers)
        headers["Access-Control-Max-Age"] = str(self._config.max_age)

        return headers

    def add_origin(self, origin: str) -> None:
        """Add an allowed origin."""
        if origin not in self._config.allowed_origins:
            self._config.allowed_origins.append(origin)

    def remove_origin(self, origin: str) -> None:
        """Remove an allowed origin."""
        if origin in self._config.allowed_origins:
            self._config.allowed_origins.remove(origin)
