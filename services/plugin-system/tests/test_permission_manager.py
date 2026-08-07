"""Tests for the plugin permission manager."""

import pytest

from sona_plugins.domain.permissions import PluginPermission
from sona_plugins.infrastructure.plugin_permission_manager import (
    PermissionDeniedError,
    PluginPermissionManager,
)


@pytest.fixture
def manager() -> PluginPermissionManager:
    return PluginPermissionManager()


class TestPermissionManagerGrant:
    """Tests for granting permissions."""

    def test_grant_single(self, manager: PluginPermissionManager) -> None:
        manager.register("p1", frozenset({PluginPermission.NETWORK_HTTP}))
        manager.grant("p1", PluginPermission.NETWORK_HTTP)
        assert manager.has_permission("p1", PluginPermission.NETWORK_HTTP)

    def test_grant_all(self, manager: PluginPermissionManager) -> None:
        perms = frozenset({PluginPermission.NETWORK_HTTP, PluginPermission.DATABASE_READ})
        manager.register("p1", perms)
        manager.grant_all("p1", perms)
        assert manager.has_permission("p1", PluginPermission.NETWORK_HTTP)
        assert manager.has_permission("p1", PluginPermission.DATABASE_READ)

    def test_grant_without_register(self, manager: PluginPermissionManager) -> None:
        manager.grant("p1", PluginPermission.NETWORK_HTTP)
        assert manager.has_permission("p1", PluginPermission.NETWORK_HTTP)

    def test_has_permission_false(self, manager: PluginPermissionManager) -> None:
        manager.register("p1", frozenset())
        assert not manager.has_permission("p1", PluginPermission.NETWORK_HTTP)


class TestPermissionManagerRevoke:
    """Tests for revoking permissions."""

    def test_revoke_single(self, manager: PluginPermissionManager) -> None:
        manager.grant("p1", PluginPermission.NETWORK_HTTP)
        manager.revoke("p1", PluginPermission.NETWORK_HTTP)
        assert not manager.has_permission("p1", PluginPermission.NETWORK_HTTP)

    def test_revoke_all(self, manager: PluginPermissionManager) -> None:
        manager.grant("p1", PluginPermission.NETWORK_HTTP)
        manager.grant("p1", PluginPermission.DATABASE_READ)
        manager.revoke_all("p1")
        assert not manager.has_permission("p1", PluginPermission.NETWORK_HTTP)
        assert not manager.has_permission("p1", PluginPermission.DATABASE_READ)

    def test_revoke_nonexistent(self, manager: PluginPermissionManager) -> None:
        # Should not raise
        manager.revoke("p1", PluginPermission.NETWORK_HTTP)


class TestPermissionManagerCheck:
    """Tests for permission checking."""

    def test_check_granted_does_not_raise(self, manager: PluginPermissionManager) -> None:
        manager.grant("p1", PluginPermission.NETWORK_HTTP)
        manager.check_permission("p1", PluginPermission.NETWORK_HTTP)

    def test_check_denied_raises(self, manager: PluginPermissionManager) -> None:
        manager.register("p1", frozenset())
        with pytest.raises(PermissionDeniedError):
            manager.check_permission("p1", PluginPermission.NETWORK_HTTP)

    def test_permission_denied_error_fields(self, manager: PluginPermissionManager) -> None:
        manager.register("p1", frozenset())
        with pytest.raises(PermissionDeniedError) as exc_info:
            manager.check_permission("p1", PluginPermission.DATABASE_WRITE)
        assert exc_info.value.plugin_id == "p1"
        assert exc_info.value.permission == PluginPermission.DATABASE_WRITE


class TestPermissionManagerSatisfaction:
    """Tests for satisfaction checking."""

    def test_is_satisfied_true(self, manager: PluginPermissionManager) -> None:
        required = frozenset({PluginPermission.NETWORK_HTTP})
        manager.register("p1", required)
        manager.grant("p1", PluginPermission.NETWORK_HTTP)
        assert manager.is_satisfied("p1")

    def test_is_satisfied_false(self, manager: PluginPermissionManager) -> None:
        required = frozenset({PluginPermission.NETWORK_HTTP, PluginPermission.DATABASE_READ})
        manager.register("p1", required)
        manager.grant("p1", PluginPermission.NETWORK_HTTP)
        assert not manager.is_satisfied("p1")

    def test_missing_permissions(self, manager: PluginPermissionManager) -> None:
        required = frozenset({PluginPermission.NETWORK_HTTP, PluginPermission.DATABASE_READ})
        manager.register("p1", required)
        manager.grant("p1", PluginPermission.NETWORK_HTTP)
        missing = manager.missing_permissions("p1")
        assert PluginPermission.DATABASE_READ in missing

    def test_get_permission_set(self, manager: PluginPermissionManager) -> None:
        required = frozenset({PluginPermission.NETWORK_HTTP})
        manager.register("p1", required)
        manager.grant("p1", PluginPermission.NETWORK_HTTP)
        perm_set = manager.get_permission_set("p1")
        assert perm_set.is_satisfied()

    def test_get_granted(self, manager: PluginPermissionManager) -> None:
        manager.grant("p1", PluginPermission.NETWORK_HTTP)
        manager.grant("p1", PluginPermission.DATABASE_READ)
        granted = manager.get_granted("p1")
        assert PluginPermission.NETWORK_HTTP in granted
        assert PluginPermission.DATABASE_READ in granted

    def test_unregister(self, manager: PluginPermissionManager) -> None:
        manager.register("p1", frozenset({PluginPermission.NETWORK_HTTP}))
        manager.grant("p1", PluginPermission.NETWORK_HTTP)
        manager.unregister("p1")
        assert not manager.has_permission("p1", PluginPermission.NETWORK_HTTP)
