"""Secret management service.

Loads secrets from environment variables and validates required secrets
at startup. Never logs or exposes secret values.
"""

import os
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger()


@dataclass
class SecretConfig:
    """Configuration for secret management."""

    required_secrets: list[str] = field(default_factory=list)
    prefix: str = "SONA_"
    mask_character: str = "*"
    mask_visible_chars: int = 4


class SecretManager:
    """Secret management service."""

    def __init__(self, config: SecretConfig | None = None) -> None:
        self._config = config or SecretConfig()
        self._secrets: dict[str, str] = {}
        self._loaded: bool = False

    @property
    def is_loaded(self) -> bool:
        """Whether secrets have been loaded."""
        return self._loaded

    async def load_secrets(self, env_override: dict[str, str] | None = None) -> None:
        """Load secrets from environment variables.

        Args:
            env_override: Optional dictionary to use instead of os.environ.
        """
        env = env_override if env_override is not None else dict(os.environ)

        for key, value in env.items():
            if key.startswith(self._config.prefix):
                self._secrets[key] = value

        self._loaded = True
        logger.info(
            "secrets_loaded",
            count=len(self._secrets),
            prefix=self._config.prefix,
        )

    async def validate_required(self) -> tuple[bool, list[str]]:
        """Validate that all required secrets are present.

        Returns:
            Tuple of (all_present, missing_keys).
        """
        missing: list[str] = []
        for key in self._config.required_secrets:
            full_key = (
                f"{self._config.prefix}{key}" if not key.startswith(self._config.prefix) else key
            )
            if full_key not in self._secrets:
                missing.append(full_key)

        if missing:
            logger.error("missing_required_secrets", missing=missing)
            return (False, missing)

        return (True, [])

    def get_secret(self, key: str) -> str | None:
        """Get a secret value by key. Never logs the value."""
        full_key = f"{self._config.prefix}{key}" if not key.startswith(self._config.prefix) else key
        return self._secrets.get(full_key)

    def set_secret(self, key: str, value: str) -> None:
        """Set a secret value (for testing or rotation)."""
        full_key = f"{self._config.prefix}{key}" if not key.startswith(self._config.prefix) else key
        self._secrets[full_key] = value
        logger.info("secret_updated", key=self._mask_key(full_key))

    def has_secret(self, key: str) -> bool:
        """Check if a secret exists without revealing its value."""
        full_key = f"{self._config.prefix}{key}" if not key.startswith(self._config.prefix) else key
        return full_key in self._secrets

    def mask_value(self, value: str) -> str:
        """Mask a secret value for safe display."""
        if len(value) <= self._config.mask_visible_chars:
            return self._config.mask_character * len(value)
        visible = value[: self._config.mask_visible_chars]
        masked = self._config.mask_character * (len(value) - self._config.mask_visible_chars)
        return f"{visible}{masked}"

    def list_keys(self) -> list[str]:
        """List all loaded secret keys (not values)."""
        return list(self._secrets.keys())

    def _mask_key(self, key: str) -> str:
        """Mask a key for logging (show prefix only)."""
        if len(key) > 8:
            return key[:8] + "..."
        return key
