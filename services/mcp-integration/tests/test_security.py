"""Unit tests for MCP domain security primitives."""

from sona_mcp.domain.security import SecurityAction, ToolPolicy, UserPermissions


class TestSecurityAction:
    def test_allow_value(self) -> None:
        assert SecurityAction.ALLOW == "allow"

    def test_deny_value(self) -> None:
        assert SecurityAction.DENY == "deny"

    def test_count(self) -> None:
        assert len(SecurityAction) == 2

    def test_is_str(self) -> None:
        assert str(SecurityAction.ALLOW) == "allow"


class TestToolPolicy:
    def test_creation_minimal(self) -> None:
        policy = ToolPolicy(tool_pattern="*", action=SecurityAction.ALLOW)
        assert policy.tool_pattern == "*"
        assert policy.action == SecurityAction.ALLOW
        assert policy.reason == ""

    def test_creation_with_reason(self) -> None:
        policy = ToolPolicy(
            tool_pattern="admin_*",
            action=SecurityAction.DENY,
            reason="Admin tools restricted",
        )
        assert policy.tool_pattern == "admin_*"
        assert policy.action == SecurityAction.DENY
        assert policy.reason == "Admin tools restricted"

    def test_is_frozen(self) -> None:
        policy = ToolPolicy(tool_pattern="*", action=SecurityAction.ALLOW)
        try:
            policy.tool_pattern = "changed"  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except (TypeError, AttributeError):
            pass

    def test_glob_patterns(self) -> None:
        p1 = ToolPolicy(tool_pattern="read_*", action=SecurityAction.ALLOW)
        p2 = ToolPolicy(tool_pattern="write_*", action=SecurityAction.DENY)
        assert p1.tool_pattern == "read_*"
        assert p2.tool_pattern == "write_*"


class TestUserPermissions:
    def test_default_permissions(self) -> None:
        perms = UserPermissions(user_id="user-1")
        assert perms.user_id == "user-1"
        assert perms.allowed_permissions == {"read"}
        assert perms.denied_tools == set()
        assert perms.max_calls_per_minute == 60

    def test_custom_permissions(self) -> None:
        perms = UserPermissions(
            user_id="admin-1",
            allowed_permissions={"read", "write", "execute", "admin"},
            denied_tools={"dangerous_tool"},
            max_calls_per_minute=120,
        )
        assert "admin" in perms.allowed_permissions
        assert "dangerous_tool" in perms.denied_tools
        assert perms.max_calls_per_minute == 120

    def test_is_mutable(self) -> None:
        perms = UserPermissions(user_id="u1")
        perms.allowed_permissions.add("write")
        assert "write" in perms.allowed_permissions

    def test_denied_tools_mutable(self) -> None:
        perms = UserPermissions(user_id="u1")
        perms.denied_tools.add("bad_tool")
        assert "bad_tool" in perms.denied_tools

    def test_multiple_users_independent(self) -> None:
        p1 = UserPermissions(user_id="u1")
        p2 = UserPermissions(user_id="u2")
        p1.allowed_permissions.add("write")
        assert "write" not in p2.allowed_permissions
