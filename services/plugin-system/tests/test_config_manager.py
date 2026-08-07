"""Tests for the plugin config manager."""

import pytest

from sona_plugins.infrastructure.plugin_config_manager import (
    ConfigValidationError,
    PluginConfigManager,
)


@pytest.fixture
def config_mgr() -> PluginConfigManager:
    return PluginConfigManager()


class TestConfigManagerLoad:
    """Tests for loading configuration."""

    def test_load_simple_config(self, config_mgr: PluginConfigManager) -> None:
        result = config_mgr.load_config("p1", {"key": "value"})
        assert result == {"key": "value"}

    def test_load_with_defaults(self, config_mgr: PluginConfigManager) -> None:
        config_mgr.register_schema("p1", {}, defaults={"port": 8080, "host": "localhost"})
        result = config_mgr.load_config("p1", {"port": 9090})
        assert result["port"] == 9090
        assert result["host"] == "localhost"

    def test_load_overrides_defaults(self, config_mgr: PluginConfigManager) -> None:
        config_mgr.register_schema("p1", {}, defaults={"port": 8080})
        result = config_mgr.load_config("p1", {"port": 3000})
        assert result["port"] == 3000


class TestConfigManagerValidation:
    """Tests for configuration validation."""

    def test_valid_config(self, config_mgr: PluginConfigManager) -> None:
        schema = {"port": {"type": "int", "required": True}}
        config_mgr.register_schema("p1", schema)
        result = config_mgr.load_config("p1", {"port": 8080})
        assert result["port"] == 8080

    def test_missing_required_raises(self, config_mgr: PluginConfigManager) -> None:
        schema = {"port": {"type": "int", "required": True}}
        config_mgr.register_schema("p1", schema)
        with pytest.raises(ConfigValidationError):
            config_mgr.load_config("p1", {})

    def test_wrong_type_raises(self, config_mgr: PluginConfigManager) -> None:
        schema = {"port": {"type": "int", "required": True}}
        config_mgr.register_schema("p1", schema)
        with pytest.raises(ConfigValidationError):
            config_mgr.load_config("p1", {"port": "not-an-int"})

    def test_optional_missing_ok(self, config_mgr: PluginConfigManager) -> None:
        schema = {"port": {"type": "int", "required": False}}
        config_mgr.register_schema("p1", schema)
        result = config_mgr.load_config("p1", {})
        assert result == {}

    def test_validation_error_fields(self, config_mgr: PluginConfigManager) -> None:
        schema = {"port": {"type": "int", "required": True}}
        config_mgr.register_schema("p1", schema)
        with pytest.raises(ConfigValidationError) as exc_info:
            config_mgr.load_config("p1", {})
        assert exc_info.value.plugin_id == "p1"
        assert len(exc_info.value.errors) > 0


class TestConfigManagerEnvInjection:
    """Tests for environment variable injection."""

    def test_env_var_resolved(
        self, config_mgr: PluginConfigManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TEST_API_KEY", "secret123")
        result = config_mgr.load_config("p1", {"api_key": "${TEST_API_KEY}"})
        assert result["api_key"] == "secret123"

    def test_env_var_not_set_keeps_original(self, config_mgr: PluginConfigManager) -> None:
        result = config_mgr.load_config("p1", {"api_key": "${NONEXISTENT_VAR}"})
        assert result["api_key"] == "${NONEXISTENT_VAR}"

    def test_non_env_strings_unchanged(self, config_mgr: PluginConfigManager) -> None:
        result = config_mgr.load_config("p1", {"name": "hello"})
        assert result["name"] == "hello"


class TestConfigManagerOperations:
    """Tests for get/update/remove operations."""

    def test_get_config(self, config_mgr: PluginConfigManager) -> None:
        config_mgr.load_config("p1", {"key": "value"})
        assert config_mgr.get_config("p1") == {"key": "value"}

    def test_get_config_empty(self, config_mgr: PluginConfigManager) -> None:
        assert config_mgr.get_config("nonexistent") == {}

    def test_get_value(self, config_mgr: PluginConfigManager) -> None:
        config_mgr.load_config("p1", {"port": 8080})
        assert config_mgr.get_value("p1", "port") == 8080

    def test_get_value_default(self, config_mgr: PluginConfigManager) -> None:
        assert config_mgr.get_value("p1", "missing", "default") == "default"

    def test_update_config(self, config_mgr: PluginConfigManager) -> None:
        config_mgr.load_config("p1", {"port": 8080})
        result = config_mgr.update_config("p1", {"port": 9090})
        assert result["port"] == 9090

    def test_remove_config(self, config_mgr: PluginConfigManager) -> None:
        config_mgr.load_config("p1", {"key": "value"})
        config_mgr.remove_config("p1")
        assert config_mgr.get_config("p1") == {}
