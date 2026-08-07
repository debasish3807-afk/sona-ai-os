"""Plugin configuration manager — load, validate, and manage plugin configs."""

from __future__ import annotations

import os
from typing import Any

import structlog

logger = structlog.get_logger()


class ConfigValidationError(Exception):
    """Raised when plugin configuration validation fails."""

    def __init__(self, plugin_id: str, errors: list[str]) -> None:
        self.plugin_id = plugin_id
        self.errors = errors
        super().__init__(f"Configuration validation failed for '{plugin_id}': {'; '.join(errors)}")


class PluginConfigManager:
    """Manages plugin configuration loading, validation, and environment injection.

    Supports:
    - Per-plugin configuration settings
    - Schema validation
    - Environment variable injection (${ENV_VAR} syntax)
    - Default values
    """

    def __init__(self) -> None:
        self._configs: dict[str, dict[str, Any]] = {}
        self._schemas: dict[str, dict[str, Any]] = {}
        self._defaults: dict[str, dict[str, Any]] = {}

    def register_schema(
        self,
        plugin_id: str,
        schema: dict[str, Any],
        defaults: dict[str, Any] | None = None,
    ) -> None:
        """Register a configuration schema for a plugin.

        Schema format: {"key": {"type": "str"|"int"|"float"|"bool", "required": bool}}
        """
        self._schemas[plugin_id] = schema
        if defaults:
            self._defaults[plugin_id] = defaults
        logger.info("config_schema_registered", plugin_id=plugin_id)

    def load_config(self, plugin_id: str, config: dict[str, Any]) -> dict[str, Any]:
        """Load and process configuration for a plugin.

        Applies defaults, resolves environment variables, and validates.

        Returns:
            The processed configuration dictionary.

        Raises:
            ConfigValidationError: If validation fails.
        """
        # Start with defaults
        merged = dict(self._defaults.get(plugin_id, {}))
        merged.update(config)

        # Resolve environment variables
        resolved = self._resolve_env_vars(merged)

        # Validate against schema
        errors = self._validate(plugin_id, resolved)
        if errors:
            raise ConfigValidationError(plugin_id, errors)

        self._configs[plugin_id] = resolved
        logger.info("config_loaded", plugin_id=plugin_id)
        return resolved

    def get_config(self, plugin_id: str) -> dict[str, Any]:
        """Get the current configuration for a plugin."""
        return dict(self._configs.get(plugin_id, {}))

    def get_value(self, plugin_id: str, key: str, default: Any = None) -> Any:
        """Get a specific configuration value."""
        config = self._configs.get(plugin_id, {})
        return config.get(key, default)

    def update_config(self, plugin_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update specific configuration values for a plugin."""
        current = self._configs.get(plugin_id, {})
        current.update(updates)

        # Re-validate
        errors = self._validate(plugin_id, current)
        if errors:
            raise ConfigValidationError(plugin_id, errors)

        self._configs[plugin_id] = current
        logger.info("config_updated", plugin_id=plugin_id, keys=list(updates.keys()))
        return dict(current)

    def remove_config(self, plugin_id: str) -> None:
        """Remove all configuration for a plugin."""
        self._configs.pop(plugin_id, None)
        self._schemas.pop(plugin_id, None)
        self._defaults.pop(plugin_id, None)

    def _resolve_env_vars(self, config: dict[str, Any]) -> dict[str, Any]:
        """Resolve ${ENV_VAR} patterns in string values."""
        resolved: dict[str, Any] = {}
        for key, value in config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                resolved[key] = os.environ.get(env_var, value)
            else:
                resolved[key] = value
        return resolved

    def _validate(self, plugin_id: str, config: dict[str, Any]) -> list[str]:
        """Validate configuration against the registered schema."""
        schema = self._schemas.get(plugin_id)
        if not schema:
            return []

        errors: list[str] = []
        for key, spec in schema.items():
            required = spec.get("required", False)
            expected_type = spec.get("type", "str")

            if required and key not in config:
                errors.append(f"Missing required key: {key}")
                continue

            if key in config:
                value = config[key]
                if not self._check_type(value, expected_type):
                    errors.append(
                        f"Key '{key}' expected type '{expected_type}', got '{type(value).__name__}'"
                    )

        return errors

    def _check_type(self, value: Any, expected: str) -> bool:
        """Check if a value matches the expected type string."""
        type_map: dict[str, type] = {
            "str": str,
            "int": int,
            "float": (int, float),  # type: ignore[dict-item]
            "bool": bool,
            "list": list,
            "dict": dict,
        }
        expected_type = type_map.get(expected)
        if expected_type is None:
            return True
        return isinstance(value, expected_type)
