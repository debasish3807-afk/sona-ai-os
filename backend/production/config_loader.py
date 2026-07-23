"""Configuration loader — validates settings at startup and provides typed config access."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from config.logging import get_logger
from config.settings import Settings, get_settings

logger = get_logger(__name__)

_REQUIRED_ENV_VARS: list[str] = []


@dataclass
class ConfigLoadResult:
    success: bool
    settings: Settings | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    loaded_vars: dict[str, str] = field(default_factory=dict)


_CRITICAL_VARS = {
    "JWT_SECRET": "JWT authentication secret — generate with: python -c 'import secrets; print(secrets.token_hex(32))'",
    "ENCRYPTION_KEY": "Encryption master key — required for Fernet encryption@rest",
}

_OPTIONAL_VARS = {
    "DATABASE_URL": "Database connection string (default: sqlite:///data/sona.db)",
    "REDIS_URL": "Redis connection string (falls back to in-memory cache)",
    "QDRANT_URL": "Qdrant vector database URL (falls back to in-memory vectors)",
    "OLLAMA_URL": "Ollama local AI URL (default: http://localhost:11434)",
    "GEMINI_API_KEY": "Google Gemini API key for cloud AI provider",
}


class ConfigLoader:
    """Loads and validates configuration at application startup."""

    def __init__(self) -> None:
        self._loaded = False
        self._result: ConfigLoadResult | None = None

    def load(self) -> ConfigLoadResult:
        if self._loaded and self._result:
            return self._result

        errors: list[str] = []
        warnings: list[str] = []
        loaded: dict[str, str] = {}

        for var_name, hint in _CRITICAL_VARS.items():
            val = os.environ.get(var_name)
            if not val:
                errors.append(f"{var_name} is not set — {hint}")
            else:
                loaded[var_name] = "***"

        for var_name, hint in _OPTIONAL_VARS.items():
            val = os.environ.get(var_name)
            if val:
                loaded[var_name] = "***"
            else:
                warnings.append(f"{var_name} not set — {hint}")

        settings: Settings | None = None
        try:
            settings = get_settings()
            loaded["APP_ENV"] = settings.environment.value
            loaded["APP_VERSION"] = settings.app_version
        except Exception as exc:
            errors.append(f"Failed to load settings: {exc}")

        self._result = ConfigLoadResult(
            success=len(errors) == 0,
            settings=settings,
            errors=errors,
            warnings=warnings,
            loaded_vars=loaded,
        )
        self._loaded = True

        if errors:
            logger.error("config_validation_failed", errors=errors)
        if warnings:
            logger.warning("config_warnings", warnings=warnings)

        return self._result
