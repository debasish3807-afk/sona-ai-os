"""Environment-aware dependency mode for Memory OS.

Controls how Redis and Qdrant dependencies behave when unavailable:
- production: Raises explicit errors — no silent fallback to volatile storage
- development/test: Allows graceful mock fallback (existing behavior)

Configuration via SONA_DEPENDENCY_MODE environment variable.
"""

import os
from enum import StrEnum

import structlog

logger = structlog.get_logger()


class DependencyMode(StrEnum):
    """Dependency failure behavior mode."""

    PRODUCTION = "production"
    DEVELOPMENT = "development"
    TEST = "test"


class DependencyUnavailableError(Exception):
    """Raised when a required dependency is unavailable in production mode."""

    def __init__(self, service: str, url: str) -> None:
        self.service = service
        self.url = url
        super().__init__(
            f"{service} is unavailable at {url}. "
            f"In production mode, dependencies must be available. "
            f"Set SONA_DEPENDENCY_MODE=development to allow mock fallback."
        )


def get_dependency_mode() -> DependencyMode:
    """Get the current dependency mode from environment.

    Default: 'development' for backward compatibility.
    Set SONA_DEPENDENCY_MODE=production for strict behavior.
    """
    val = os.environ.get("SONA_DEPENDENCY_MODE", "development").lower()
    if val == "production":
        return DependencyMode.PRODUCTION
    if val == "test":
        return DependencyMode.TEST
    return DependencyMode.DEVELOPMENT


def is_strict_mode() -> bool:
    """Check if strict dependency mode is active (production)."""
    return get_dependency_mode() == DependencyMode.PRODUCTION


def check_dependency_available(
    service_name: str,
    url: str,
    is_connected: bool,
) -> None:
    """Raise if dependency unavailable in production mode.

    In development/test mode, logs a warning and returns (allows fallback).
    In production mode, raises DependencyUnavailableError.
    """
    if is_connected:
        return

    if is_strict_mode():
        raise DependencyUnavailableError(service=service_name, url=url)

    logger.warning(
        "dependency.fallback_allowed",
        service=service_name,
        url=url,
        mode=get_dependency_mode(),
        message=f"{service_name} unavailable — using mock fallback (non-production mode)",
    )
