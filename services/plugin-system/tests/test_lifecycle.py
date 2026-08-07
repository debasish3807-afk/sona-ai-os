"""Tests for the plugin lifecycle state machine."""

from sona_plugins.domain.lifecycle import VALID_TRANSITIONS, PluginLifecycleState


class TestPluginLifecycleState:
    """Tests for PluginLifecycleState enum."""

    def test_all_states_defined(self) -> None:
        assert len(PluginLifecycleState) == 13

    def test_state_values(self) -> None:
        assert PluginLifecycleState.DISCOVERED == "discovered"
        assert PluginLifecycleState.INSTALLED == "installed"
        assert PluginLifecycleState.VERIFIED == "verified"
        assert PluginLifecycleState.LOADED == "loaded"
        assert PluginLifecycleState.INITIALIZED == "initialized"
        assert PluginLifecycleState.STARTED == "started"
        assert PluginLifecycleState.RUNNING == "running"
        assert PluginLifecycleState.STOPPING == "stopping"
        assert PluginLifecycleState.STOPPED == "stopped"
        assert PluginLifecycleState.UNLOADING == "unloading"
        assert PluginLifecycleState.UNLOADED == "unloaded"
        assert PluginLifecycleState.REMOVED == "removed"
        assert PluginLifecycleState.ERROR == "error"

    def test_states_are_str_enum(self) -> None:
        for state in PluginLifecycleState:
            assert isinstance(state, str)
            assert str(state) == state.value


class TestValidTransitions:
    """Tests for the VALID_TRANSITIONS state machine definition."""

    def test_all_states_have_transitions(self) -> None:
        for state in PluginLifecycleState:
            assert state in VALID_TRANSITIONS

    def test_discovered_transitions(self) -> None:
        assert PluginLifecycleState.INSTALLED in VALID_TRANSITIONS[PluginLifecycleState.DISCOVERED]
        assert PluginLifecycleState.REMOVED in VALID_TRANSITIONS[PluginLifecycleState.DISCOVERED]

    def test_installed_transitions(self) -> None:
        valid = VALID_TRANSITIONS[PluginLifecycleState.INSTALLED]
        assert PluginLifecycleState.VERIFIED in valid
        assert PluginLifecycleState.REMOVED in valid
        assert PluginLifecycleState.ERROR in valid

    def test_verified_transitions(self) -> None:
        valid = VALID_TRANSITIONS[PluginLifecycleState.VERIFIED]
        assert PluginLifecycleState.LOADED in valid
        assert PluginLifecycleState.REMOVED in valid

    def test_loaded_transitions(self) -> None:
        valid = VALID_TRANSITIONS[PluginLifecycleState.LOADED]
        assert PluginLifecycleState.INITIALIZED in valid
        assert PluginLifecycleState.UNLOADING in valid
        assert PluginLifecycleState.ERROR in valid

    def test_running_transitions(self) -> None:
        valid = VALID_TRANSITIONS[PluginLifecycleState.RUNNING]
        assert PluginLifecycleState.STOPPING in valid
        assert PluginLifecycleState.ERROR in valid

    def test_stopped_transitions(self) -> None:
        valid = VALID_TRANSITIONS[PluginLifecycleState.STOPPED]
        assert PluginLifecycleState.STARTED in valid
        assert PluginLifecycleState.UNLOADING in valid
        assert PluginLifecycleState.REMOVED in valid

    def test_removed_has_no_transitions(self) -> None:
        assert VALID_TRANSITIONS[PluginLifecycleState.REMOVED] == []

    def test_error_transitions(self) -> None:
        valid = VALID_TRANSITIONS[PluginLifecycleState.ERROR]
        assert PluginLifecycleState.STOPPED in valid
        assert PluginLifecycleState.REMOVED in valid

    def test_invalid_transition_discovered_to_running(self) -> None:
        assert (
            PluginLifecycleState.RUNNING not in VALID_TRANSITIONS[PluginLifecycleState.DISCOVERED]
        )

    def test_invalid_transition_running_to_discovered(self) -> None:
        assert (
            PluginLifecycleState.DISCOVERED not in VALID_TRANSITIONS[PluginLifecycleState.RUNNING]
        )

    def test_invalid_transition_removed_to_anything(self) -> None:
        for state in PluginLifecycleState:
            assert state not in VALID_TRANSITIONS[PluginLifecycleState.REMOVED]

    def test_stopping_only_goes_to_stopped(self) -> None:
        assert VALID_TRANSITIONS[PluginLifecycleState.STOPPING] == [PluginLifecycleState.STOPPED]

    def test_unloading_only_goes_to_unloaded(self) -> None:
        assert VALID_TRANSITIONS[PluginLifecycleState.UNLOADING] == [PluginLifecycleState.UNLOADED]

    def test_happy_path_transitions(self) -> None:
        """Verify a full happy-path lifecycle is possible."""
        path = [
            PluginLifecycleState.DISCOVERED,
            PluginLifecycleState.INSTALLED,
            PluginLifecycleState.VERIFIED,
            PluginLifecycleState.LOADED,
            PluginLifecycleState.INITIALIZED,
            PluginLifecycleState.STARTED,
            PluginLifecycleState.RUNNING,
            PluginLifecycleState.STOPPING,
            PluginLifecycleState.STOPPED,
            PluginLifecycleState.UNLOADING,
            PluginLifecycleState.UNLOADED,
            PluginLifecycleState.REMOVED,
        ]
        for i in range(len(path) - 1):
            assert path[i + 1] in VALID_TRANSITIONS[path[i]], (
                f"{path[i]} -> {path[i + 1]} should be valid"
            )
