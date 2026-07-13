"""Environment-specific configuration profiles."""

from __future__ import annotations

from config.logging import get_logger

logger = get_logger(__name__)


class EnvironmentProfile:
    """Environment-specific configuration profiles."""

    @staticmethod
    def development() -> dict[str, object]:
        """Development environment configuration."""
        return {
            "debug": True,
            "log_level": "DEBUG",
            "log_format": "text",
            "database_url": "sqlite:///data/sona-dev.db",
            "host": "127.0.0.1",
            "port": 8000,
            "reload": True,
            "cors_origins": ["*"],
            "rate_limit": 1000,
            "workers": 1,
        }

    @staticmethod
    def staging() -> dict[str, object]:
        """Staging environment configuration."""
        return {
            "debug": False,
            "log_level": "INFO",
            "log_format": "json",
            "database_url": "sqlite:///data/sona-staging.db",
            "host": "0.0.0.0",
            "port": 8000,
            "reload": False,
            "cors_origins": ["https://staging.sona-ai.io"],
            "rate_limit": 500,
            "workers": 2,
        }

    @staticmethod
    def production() -> dict[str, object]:
        """Production environment configuration."""
        return {
            "debug": False,
            "log_level": "WARNING",
            "log_format": "json",
            "database_url": "sqlite:///data/sona.db",
            "host": "0.0.0.0",
            "port": 8000,
            "reload": False,
            "cors_origins": ["https://sona-ai.io"],
            "rate_limit": 200,
            "workers": 4,
        }

    @staticmethod
    def get_profile(env_name: str) -> dict[str, object]:
        """Get configuration profile by environment name.

        Args:
            env_name: Environment name (development, staging, production).

        Returns:
            Configuration dictionary for the environment.
        """
        profiles = {
            "development": EnvironmentProfile.development,
            "staging": EnvironmentProfile.staging,
            "production": EnvironmentProfile.production,
        }
        factory = profiles.get(env_name.lower())
        if factory is None:
            logger.warning("unknown_profile", env=env_name)
            return EnvironmentProfile.development()
        return factory()
