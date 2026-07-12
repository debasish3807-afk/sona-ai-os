"""Configuration registry and validation."""

from dataclasses import dataclass, field
from typing import Any

from config.settings import Environment, Settings, get_settings


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration derived from settings.

    Provides a clean interface for accessing validated configuration
    throughout the application without coupling to env var names.
    """

    name: str
    version: str
    description: str
    environment: Environment
    debug: bool
    api_prefix: str
    docs_enabled: bool
    cors_origins: tuple[str, ...]
    log_level: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "AppConfig":
        """Create AppConfig from Settings instance.

        Args:
            settings: Optional settings instance. Uses cached singleton if None.

        Returns:
            Immutable AppConfig instance.
        """
        if settings is None:
            settings = get_settings()

        return cls(
            name=settings.app_name,
            version=settings.app_version,
            description=settings.app_description,
            environment=settings.environment,
            debug=settings.debug,
            api_prefix=settings.api_prefix,
            docs_enabled=not settings.is_production,
            cors_origins=tuple(settings.cors_origins),
            log_level=settings.log_level,
            metadata={
                "host": settings.host,
                "port": settings.port,
                "workers": settings.workers,
            },
        )

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == Environment.DEVELOPMENT
