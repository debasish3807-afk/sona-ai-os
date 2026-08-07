"""Tests for MCP tool security."""

import pytest

from sona_security.infrastructure.mcp_security import MCPSecurity, MCPSecurityConfig


class TestMCPSecurity:
    def setup_method(self) -> None:
        self.mcp = MCPSecurity()

    @pytest.mark.asyncio
    async def test_allow_unregulated_tool(self) -> None:
        allowed, reason = await self.mcp.validate_tool_access("tool-a", "user-1", "session-1")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_deny_listed_tool(self) -> None:
        self.mcp.add_to_denylist("dangerous-tool")
        allowed, reason = await self.mcp.validate_tool_access(
            "dangerous-tool", "user-1", "session-1"
        )
        assert allowed is False
        assert "denied" in reason.lower()

    @pytest.mark.asyncio
    async def test_allowlist_mode(self) -> None:
        self.mcp.add_to_allowlist("safe-tool")
        allowed, _ = await self.mcp.validate_tool_access("not-in-list", "user-1", "session-1")
        assert allowed is False

    @pytest.mark.asyncio
    async def test_allowlist_allows_listed(self) -> None:
        self.mcp.add_to_allowlist("safe-tool")
        allowed, _ = await self.mcp.validate_tool_access("safe-tool", "user-1", "session-1")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_remove_from_denylist(self) -> None:
        self.mcp.add_to_denylist("tool-x")
        self.mcp.remove_from_denylist("tool-x")
        allowed, _ = await self.mcp.validate_tool_access("tool-x", "user-1", "session-1")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_remove_from_allowlist(self) -> None:
        self.mcp.add_to_allowlist("tool-x")
        self.mcp.add_to_allowlist("tool-y")
        self.mcp.remove_from_allowlist("tool-x")
        allowed, _ = await self.mcp.validate_tool_access("tool-x", "user-1", "session-1")
        assert allowed is False

    @pytest.mark.asyncio
    async def test_role_permission_check(self) -> None:
        self.mcp.set_tool_permissions("admin-tool", ["admin"])
        allowed, reason = await self.mcp.validate_tool_access(
            "admin-tool", "user-1", "session-1", user_roles=["user"]
        )
        assert allowed is False
        assert "insufficient" in reason.lower()

    @pytest.mark.asyncio
    async def test_role_permission_allowed(self) -> None:
        self.mcp.set_tool_permissions("admin-tool", ["admin"])
        allowed, _ = await self.mcp.validate_tool_access(
            "admin-tool", "admin-1", "session-1", user_roles=["admin"]
        )
        assert allowed is True

    @pytest.mark.asyncio
    async def test_session_call_limit(self) -> None:
        config = MCPSecurityConfig(max_calls_per_session=3)
        mcp = MCPSecurity(config=config)
        for _ in range(3):
            allowed, _ = await mcp.validate_tool_access("tool", "user-1", "sess-1")
            assert allowed is True
        allowed, reason = await mcp.validate_tool_access("tool", "user-1", "sess-1")
        assert allowed is False
        assert "limit" in reason.lower()

    @pytest.mark.asyncio
    async def test_session_isolation(self) -> None:
        config = MCPSecurityConfig(max_calls_per_session=2)
        mcp = MCPSecurity(config=config)
        for _ in range(2):
            await mcp.validate_tool_access("tool", "user-1", "sess-1")
        # Different session should work
        allowed, _ = await mcp.validate_tool_access("tool", "user-1", "sess-2")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_output_size_check(self) -> None:
        config = MCPSecurityConfig(max_output_size_bytes=100)
        mcp = MCPSecurity(config=config)
        await mcp.validate_tool_access("tool", "user-1", "sess-1")
        allowed, _ = await mcp.check_output_size("sess-1", 50)
        assert allowed is True
        allowed, reason = await mcp.check_output_size("sess-1", 60)
        assert allowed is False

    @pytest.mark.asyncio
    async def test_output_size_unknown_session(self) -> None:
        allowed, _ = await self.mcp.check_output_size("nonexistent", 10)
        assert allowed is False

    @pytest.mark.asyncio
    async def test_end_session(self) -> None:
        await self.mcp.validate_tool_access("tool", "user-1", "sess-1")
        result = await self.mcp.end_session("sess-1")
        assert result is True
        allowed, reason = await self.mcp.validate_tool_access("tool", "user-1", "sess-1")
        assert allowed is False
        assert "active" in reason.lower()

    @pytest.mark.asyncio
    async def test_end_nonexistent_session(self) -> None:
        result = await self.mcp.end_session("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_session_state(self) -> None:
        await self.mcp.validate_tool_access("tool-a", "user-1", "sess-1")
        state = await self.mcp.get_session_state("sess-1")
        assert state is not None
        assert state.call_count == 1
        assert "tool-a" in state.tools_used

    @pytest.mark.asyncio
    async def test_execution_log(self) -> None:
        await self.mcp.validate_tool_access("tool-a", "user-1", "sess-1")
        assert len(self.mcp.execution_log) == 1
        assert self.mcp.execution_log[0].tool_name == "tool-a"
        assert self.mcp.execution_log[0].allowed is True
