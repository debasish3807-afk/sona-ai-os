"""Tests for plugin domain events."""

import pytest

from sona_plugins.domain.events import (
    PluginActivatedEvent,
    PluginDeactivatedEvent,
    PluginExecutedEvent,
    PluginFailedEvent,
    PluginInstalledEvent,
)


class TestPluginInstalledEvent:
    """Tests for PluginInstalledEvent."""

    def test_creation_with_defaults(self) -> None:
        event = PluginInstalledEvent()
        assert event.plugin_id == ""
        assert event.name == ""
        assert event.version == ""

    def test_creation_with_values(self) -> None:
        event = PluginInstalledEvent(plugin_id="test-plugin", name="Test Plugin", version="1.0.0")
        assert event.plugin_id == "test-plugin"
        assert event.name == "Test Plugin"
        assert event.version == "1.0.0"

    def test_has_event_id(self) -> None:
        event = PluginInstalledEvent(plugin_id="test")
        assert event.event_id is not None

    def test_has_occurred_at(self) -> None:
        event = PluginInstalledEvent(plugin_id="test")
        assert event.occurred_at is not None

    def test_is_frozen(self) -> None:
        event = PluginInstalledEvent(plugin_id="test")
        with pytest.raises(AttributeError):
            event.plugin_id = "changed"  # type: ignore[misc]


class TestPluginActivatedEvent:
    """Tests for PluginActivatedEvent."""

    def test_creation(self) -> None:
        event = PluginActivatedEvent(plugin_id="my-plugin")
        assert event.plugin_id == "my-plugin"

    def test_default_plugin_id(self) -> None:
        event = PluginActivatedEvent()
        assert event.plugin_id == ""


class TestPluginDeactivatedEvent:
    """Tests for PluginDeactivatedEvent."""

    def test_creation(self) -> None:
        event = PluginDeactivatedEvent(plugin_id="my-plugin", reason="user request")
        assert event.plugin_id == "my-plugin"
        assert event.reason == "user request"

    def test_defaults(self) -> None:
        event = PluginDeactivatedEvent()
        assert event.plugin_id == ""
        assert event.reason == ""


class TestPluginFailedEvent:
    """Tests for PluginFailedEvent."""

    def test_creation(self) -> None:
        event = PluginFailedEvent(
            plugin_id="bad-plugin", error="Connection refused", state="running"
        )
        assert event.plugin_id == "bad-plugin"
        assert event.error == "Connection refused"
        assert event.state == "running"

    def test_defaults(self) -> None:
        event = PluginFailedEvent()
        assert event.plugin_id == ""
        assert event.error == ""
        assert event.state == ""


class TestPluginExecutedEvent:
    """Tests for PluginExecutedEvent."""

    def test_creation_success(self) -> None:
        event = PluginExecutedEvent(
            plugin_id="echo",
            action="execute",
            duration_ms=15.5,
            success=True,
        )
        assert event.plugin_id == "echo"
        assert event.action == "execute"
        assert event.duration_ms == 15.5
        assert event.success is True

    def test_creation_failure(self) -> None:
        event = PluginExecutedEvent(
            plugin_id="echo",
            action="execute",
            duration_ms=100.0,
            success=False,
        )
        assert event.success is False

    def test_defaults(self) -> None:
        event = PluginExecutedEvent()
        assert event.plugin_id == ""
        assert event.action == ""
        assert event.duration_ms == 0.0
        assert event.success is True

    def test_frozen(self) -> None:
        event = PluginExecutedEvent(plugin_id="test")
        with pytest.raises(AttributeError):
            event.success = False  # type: ignore[misc]
