"""Unit tests for SecurityManager."""

from sona_mcp.domain.security import SecurityAction, ToolPolicy, UserPermissions
from sona_mcp.infrastructure.security_manager import SecurityManager


class TestSecurityManagerPolicies:
    def test_add_policy(self) -> None:
        mgr = SecurityManager()
        mgr.add_policy(ToolPolicy(tool_pattern="*", action=SecurityAction.ALLOW))
        assert mgr.policy_count == 1

    def test_add_multiple_policies(self) -> None:
        mgr = SecurityManager()
        mgr.add_policy(ToolPolicy(tool_pattern="read_*", action=SecurityAction.ALLOW))
        mgr.add_policy(ToolPolicy(tool_pattern="write_*", action=SecurityAction.DENY))
        assert mgr.policy_count == 2

    def test_remove_policy(self) -> None:
        mgr = SecurityManager()
        mgr.add_policy(ToolPolicy(tool_pattern="bad_*", action=SecurityAction.DENY))
        result = mgr.remove_policy("bad_*")
        assert result is True
        assert mgr.policy_count == 0

    def test_remove_nonexistent_policy(self) -> None:
        mgr = SecurityManager()
        result = mgr.remove_policy("missing_*")
        assert result is False

    def test_clear_policies(self) -> None:
        mgr = SecurityManager()
        mgr.add_policy(ToolPolicy(tool_pattern="*", action=SecurityAction.ALLOW))
        mgr.clear_policies()
        assert mgr.policy_count == 0


class TestSecurityManagerEvaluateAccess:
    def test_default_allows_all(self) -> None:
        mgr = SecurityManager()
        assert mgr.evaluate_tool_access("user-1", "any_tool") is True

    def test_deny_policy_blocks(self) -> None:
        mgr = SecurityManager()
        mgr.add_policy(ToolPolicy(tool_pattern="admin_*", action=SecurityAction.DENY))
        assert mgr.evaluate_tool_access("user-1", "admin_tool") is False
        assert mgr.evaluate_tool_access("user-1", "read_file") is True

    def test_allow_policy_permits(self) -> None:
        mgr = SecurityManager()
        mgr.add_policy(ToolPolicy(tool_pattern="read_*", action=SecurityAction.ALLOW))
        assert mgr.evaluate_tool_access("user-1", "read_file") is True

    def test_first_matching_policy_wins(self) -> None:
        mgr = SecurityManager()
        mgr.add_policy(ToolPolicy(tool_pattern="*", action=SecurityAction.DENY))
        mgr.add_policy(ToolPolicy(tool_pattern="safe_*", action=SecurityAction.ALLOW))
        # First policy matches everything, so safe_tool is denied
        assert mgr.evaluate_tool_access("user-1", "safe_tool") is False

    def test_user_denied_tools(self) -> None:
        mgr = SecurityManager()
        mgr.set_user_permissions(
            UserPermissions(
                user_id="user-1",
                denied_tools={"blocked_tool"},
            )
        )
        assert mgr.evaluate_tool_access("user-1", "blocked_tool") is False
        assert mgr.evaluate_tool_access("user-1", "other_tool") is True

    def test_glob_pattern_matching(self) -> None:
        mgr = SecurityManager()
        mgr.add_policy(ToolPolicy(tool_pattern="file_*", action=SecurityAction.DENY))
        assert mgr.evaluate_tool_access("u1", "file_read") is False
        assert mgr.evaluate_tool_access("u1", "file_write") is False
        assert mgr.evaluate_tool_access("u1", "network_fetch") is True


class TestSecurityManagerPermissions:
    def test_get_default_permissions(self) -> None:
        mgr = SecurityManager()
        perms = mgr.get_user_permissions("new_user")
        assert perms.user_id == "new_user"
        assert perms.allowed_permissions == {"read"}

    def test_set_permissions(self) -> None:
        mgr = SecurityManager()
        mgr.set_user_permissions(
            UserPermissions(
                user_id="admin",
                allowed_permissions={"read", "write", "admin"},
            )
        )
        perms = mgr.get_user_permissions("admin")
        assert "admin" in perms.allowed_permissions

    def test_has_permission(self) -> None:
        mgr = SecurityManager()
        mgr.set_user_permissions(
            UserPermissions(
                user_id="u1",
                allowed_permissions={"read", "write"},
            )
        )
        assert mgr.has_permission("u1", "read") is True
        assert mgr.has_permission("u1", "write") is True
        assert mgr.has_permission("u1", "admin") is False

    def test_has_permission_default_user(self) -> None:
        mgr = SecurityManager()
        assert mgr.has_permission("new_user", "read") is True
        assert mgr.has_permission("new_user", "write") is False


class TestSecurityManagerRateLimit:
    def test_within_limit(self) -> None:
        mgr = SecurityManager()
        assert mgr.check_rate_limit("user-1") is True

    def test_exceed_limit(self) -> None:
        mgr = SecurityManager()
        mgr.set_user_permissions(UserPermissions(user_id="user-1", max_calls_per_minute=3))
        mgr.record_call("user-1")
        mgr.record_call("user-1")
        mgr.record_call("user-1")
        assert mgr.check_rate_limit("user-1") is False

    def test_clear_rate_limits(self) -> None:
        mgr = SecurityManager()
        mgr.set_user_permissions(UserPermissions(user_id="user-1", max_calls_per_minute=2))
        mgr.record_call("user-1")
        mgr.record_call("user-1")
        assert mgr.check_rate_limit("user-1") is False
        mgr.clear_rate_limits()
        assert mgr.check_rate_limit("user-1") is True

    def test_rate_limit_independent_users(self) -> None:
        mgr = SecurityManager()
        mgr.set_user_permissions(UserPermissions(user_id="u1", max_calls_per_minute=1))
        mgr.record_call("u1")
        assert mgr.check_rate_limit("u1") is False
        assert mgr.check_rate_limit("u2") is True
