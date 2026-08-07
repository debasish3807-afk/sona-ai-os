"""Tests for the plugin lifecycle manager."""

import pytest

from sona_plugins.domain.lifecycle import PluginLifecycleState
from sona_plugins.infrastructure.plugin_lifecycle import (
    InvalidTransitionError,
    PluginLifecycleManager,
)


@pytest.fixture
def manager() -> PluginLifecycleManager:
    return PluginLifecycleManager()


class TestLifecycleManagerRegister:
    """Tests for plugin registration."""

    def test_register_default_state(self, manager: PluginLifecycleManager) -> None:
        manager.register("plugin-a")
        assert manager.get_state("plugin-a") == PluginLifecycleState.DISCOVERED

    def test_register_custom_state(self, manager: PluginLifecycleManager) -> None:
        manager.register("plugin-b", PluginLifecycleState.INSTALLED)
        assert manager.get_state("plugin-b") == PluginLifecycleState.INSTALLED

    def test_get_state_unregistered(self, manager: PluginLifecycleManager) -> None:
        assert manager.get_state("nonexistent") is None

    def test_unregister(self, manager: PluginLifecycleManager) -> None:
        manager.register("plugin-a")
        manager.unregister("plugin-a")
        assert manager.get_state("plugin-a") is None


class TestLifecycleManagerTransitions:
    """Tests for state transitions."""

    def test_valid_transition(self, manager: PluginLifecycleManager) -> None:
        manager.register("p1")
        manager.transition("p1", PluginLifecycleState.INSTALLED)
        assert manager.get_state("p1") == PluginLifecycleState.INSTALLED

    def test_invalid_transition_raises(self, manager: PluginLifecycleManager) -> None:
        manager.register("p1")
        with pytest.raises(InvalidTransitionError):
            manager.transition("p1", PluginLifecycleState.RUNNING)

    def test_transition_unregistered_raises(self, manager: PluginLifecycleManager) -> None:
        with pytest.raises(ValueError, match="not registered"):
            manager.transition("unknown", PluginLifecycleState.INSTALLED)

    def test_full_lifecycle_path(self, manager: PluginLifecycleManager) -> None:
        manager.register("p1")
        manager.transition("p1", PluginLifecycleState.INSTALLED)
        manager.transition("p1", PluginLifecycleState.VERIFIED)
        manager.transition("p1", PluginLifecycleState.LOADED)
        manager.transition("p1", PluginLifecycleState.INITIALIZED)
        manager.transition("p1", PluginLifecycleState.STARTED)
        manager.transition("p1", PluginLifecycleState.RUNNING)
        assert manager.get_state("p1") == PluginLifecycleState.RUNNING

    def test_error_transition(self, manager: PluginLifecycleManager) -> None:
        manager.register("p1")
        manager.transition("p1", PluginLifecycleState.INSTALLED)
        manager.transition("p1", PluginLifecycleState.ERROR)
        assert manager.get_state("p1") == PluginLifecycleState.ERROR

    def test_error_recovery(self, manager: PluginLifecycleManager) -> None:
        manager.register("p1")
        manager.transition("p1", PluginLifecycleState.INSTALLED)
        manager.transition("p1", PluginLifecycleState.ERROR)
        manager.transition("p1", PluginLifecycleState.STOPPED)
        assert manager.get_state("p1") == PluginLifecycleState.STOPPED

    def test_can_transition_true(self, manager: PluginLifecycleManager) -> None:
        manager.register("p1")
        assert manager.can_transition("p1", PluginLifecycleState.INSTALLED) is True

    def test_can_transition_false(self, manager: PluginLifecycleManager) -> None:
        manager.register("p1")
        assert manager.can_transition("p1", PluginLifecycleState.RUNNING) is False

    def test_can_transition_unregistered(self, manager: PluginLifecycleManager) -> None:
        assert manager.can_transition("unknown", PluginLifecycleState.INSTALLED) is False


class TestLifecycleManagerHistory:
    """Tests for transition history."""

    def test_history_recorded(self, manager: PluginLifecycleManager) -> None:
        manager.register("p1")
        manager.transition("p1", PluginLifecycleState.INSTALLED)
        history = manager.get_history("p1")
        assert len(history) == 1
        assert history[0].from_state == PluginLifecycleState.DISCOVERED
        assert history[0].to_state == PluginLifecycleState.INSTALLED

    def test_multiple_transitions_recorded(self, manager: PluginLifecycleManager) -> None:
        manager.register("p1")
        manager.transition("p1", PluginLifecycleState.INSTALLED)
        manager.transition("p1", PluginLifecycleState.VERIFIED)
        history = manager.get_history("p1")
        assert len(history) == 2

    def test_history_empty_after_register(self, manager: PluginLifecycleManager) -> None:
        manager.register("p1")
        assert manager.get_history("p1") == []

    def test_history_includes_reason(self, manager: PluginLifecycleManager) -> None:
        manager.register("p1")
        manager.transition("p1", PluginLifecycleState.INSTALLED, reason="auto-install")
        history = manager.get_history("p1")
        assert history[0].reason == "auto-install"


class TestLifecycleManagerEvents:
    """Tests for domain event emission."""

    def test_running_emits_activated(self, manager: PluginLifecycleManager) -> None:
        manager.register("p1")
        manager.transition("p1", PluginLifecycleState.INSTALLED)
        manager.transition("p1", PluginLifecycleState.VERIFIED)
        manager.transition("p1", PluginLifecycleState.LOADED)
        manager.transition("p1", PluginLifecycleState.INITIALIZED)
        manager.transition("p1", PluginLifecycleState.STARTED)
        manager.transition("p1", PluginLifecycleState.RUNNING)
        events = manager.drain_events()
        assert any(e.plugin_id == "p1" for e in events)

    def test_error_emits_failed(self, manager: PluginLifecycleManager) -> None:
        manager.register("p1")
        manager.transition("p1", PluginLifecycleState.INSTALLED)
        manager.transition("p1", PluginLifecycleState.ERROR, reason="crash")
        events = manager.drain_events()
        assert len(events) >= 1

    def test_drain_clears_events(self, manager: PluginLifecycleManager) -> None:
        manager.register("p1")
        manager.transition("p1", PluginLifecycleState.INSTALLED)
        manager.transition("p1", PluginLifecycleState.ERROR)
        manager.drain_events()
        assert manager.drain_events() == []

    def test_get_all_states(self, manager: PluginLifecycleManager) -> None:
        manager.register("p1")
        manager.register("p2", PluginLifecycleState.INSTALLED)
        states = manager.get_all_states()
        assert states["p1"] == PluginLifecycleState.DISCOVERED
        assert states["p2"] == PluginLifecycleState.INSTALLED
