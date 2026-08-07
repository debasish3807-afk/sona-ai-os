"""Tests for the plugin permission model."""

import pytest

from sona_plugins.domain.permissions import PluginPermission, PluginPermissionSet


class TestPluginPermission:
    """Tests for PluginPermission enum."""

    def test_all_permissions_defined(self) -> None:
        assert len(PluginPermission) == 12

    def test_permission_values(self) -> None:
        assert PluginPermission.FILESYSTEM_READ == "filesystem.read"
        assert PluginPermission.FILESYSTEM_WRITE == "filesystem.write"
        assert PluginPermission.NETWORK_HTTP == "network.http"
        assert PluginPermission.NETWORK_WEBSOCKET == "network.websocket"
        assert PluginPermission.DATABASE_READ == "database.read"
        assert PluginPermission.DATABASE_WRITE == "database.write"
        assert PluginPermission.MEMORY_READ == "memory.read"
        assert PluginPermission.MEMORY_WRITE == "memory.write"
        assert PluginPermission.MCP_INVOKE == "mcp.invoke"
        assert PluginPermission.AGENT_EXECUTE == "agent.execute"
        assert PluginPermission.SYSTEM_METRICS == "system.metrics"
        assert PluginPermission.SYSTEM_CONFIG == "system.config"

    def test_permissions_are_str(self) -> None:
        for perm in PluginPermission:
            assert isinstance(perm, str)


class TestPluginPermissionSet:
    """Tests for PluginPermissionSet."""

    def test_empty_required_always_satisfied(self) -> None:
        ps = PluginPermissionSet(required=frozenset())
        assert ps.is_satisfied()
        assert ps.missing() == frozenset()

    def test_all_required_granted(self) -> None:
        required = frozenset({PluginPermission.NETWORK_HTTP, PluginPermission.DATABASE_READ})
        granted = frozenset({PluginPermission.NETWORK_HTTP, PluginPermission.DATABASE_READ})
        ps = PluginPermissionSet(required=required, granted=granted)
        assert ps.is_satisfied()
        assert ps.missing() == frozenset()

    def test_missing_permissions(self) -> None:
        required = frozenset({PluginPermission.NETWORK_HTTP, PluginPermission.DATABASE_READ})
        granted = frozenset({PluginPermission.NETWORK_HTTP})
        ps = PluginPermissionSet(required=required, granted=granted)
        assert not ps.is_satisfied()
        assert ps.missing() == frozenset({PluginPermission.DATABASE_READ})

    def test_no_grants(self) -> None:
        required = frozenset({PluginPermission.FILESYSTEM_READ})
        ps = PluginPermissionSet(required=required)
        assert not ps.is_satisfied()
        assert ps.missing() == required

    def test_extra_grants_ok(self) -> None:
        required = frozenset({PluginPermission.NETWORK_HTTP})
        granted = frozenset(
            {
                PluginPermission.NETWORK_HTTP,
                PluginPermission.NETWORK_WEBSOCKET,
                PluginPermission.DATABASE_READ,
            }
        )
        ps = PluginPermissionSet(required=required, granted=granted)
        assert ps.is_satisfied()
        assert ps.missing() == frozenset()

    def test_frozen_immutable(self) -> None:
        ps = PluginPermissionSet(
            required=frozenset({PluginPermission.NETWORK_HTTP}),
            granted=frozenset(),
        )
        with pytest.raises(AttributeError):
            ps.required = frozenset()  # type: ignore[misc]

    def test_multiple_missing(self) -> None:
        required = frozenset(
            {
                PluginPermission.FILESYSTEM_READ,
                PluginPermission.FILESYSTEM_WRITE,
                PluginPermission.NETWORK_HTTP,
            }
        )
        granted = frozenset({PluginPermission.NETWORK_HTTP})
        ps = PluginPermissionSet(required=required, granted=granted)
        missing = ps.missing()
        assert PluginPermission.FILESYSTEM_READ in missing
        assert PluginPermission.FILESYSTEM_WRITE in missing
        assert len(missing) == 2

    def test_empty_set_equality(self) -> None:
        ps1 = PluginPermissionSet(required=frozenset())
        ps2 = PluginPermissionSet(required=frozenset(), granted=frozenset())
        assert ps1 == ps2
