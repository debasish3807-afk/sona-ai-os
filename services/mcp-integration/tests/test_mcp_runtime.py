"""Integration tests for MCPRuntime."""

import pytest

from sona_mcp.application.ports import MCPManagerPort
from sona_mcp.domain.models import MCPServer, MCPTool, MCPTransport, ToolPermission
from sona_mcp.domain.security import SecurityAction, ToolPolicy, UserPermissions
from sona_mcp.infrastructure.builtin_tools import BUILTIN_SERVER
from sona_mcp.infrastructure.di import create_mcp_runtime, create_mcp_runtime_with_builtins


class TestMCPRuntimeInterface:
    def test_implements_port(self) -> None:
        runtime = create_mcp_runtime()
        assert isinstance(runtime, MCPManagerPort)


class TestMCPRuntimeServerManagement:
    @pytest.mark.asyncio
    async def test_register_server(self) -> None:
        runtime = create_mcp_runtime()
        server_id = await runtime.register_server(BUILTIN_SERVER)
        assert server_id == "builtin"

    @pytest.mark.asyncio
    async def test_list_servers(self) -> None:
        runtime = create_mcp_runtime()
        await runtime.register_server(BUILTIN_SERVER)
        servers = await runtime.list_servers()
        assert len(servers) == 1
        assert servers[0].server_id == "builtin"

    @pytest.mark.asyncio
    async def test_register_multiple_servers(self) -> None:
        runtime = create_mcp_runtime()
        await runtime.register_server(BUILTIN_SERVER)
        custom = MCPServer(
            server_id="custom",
            name="Custom",
            transport=MCPTransport.STDIO,
            tools=[],
        )
        await runtime.register_server(custom)
        servers = await runtime.list_servers()
        assert len(servers) == 2


class TestMCPRuntimeToolDiscovery:
    @pytest.mark.asyncio
    async def test_discover_tools(self) -> None:
        runtime = create_mcp_runtime()
        await runtime.register_server(BUILTIN_SERVER)
        tools = await runtime.discover_tools("builtin")
        assert len(tools) == 5

    @pytest.mark.asyncio
    async def test_discover_nonexistent_server(self) -> None:
        runtime = create_mcp_runtime()
        tools = await runtime.discover_tools("missing")
        assert tools == []


class TestMCPRuntimeToolInvocation:
    @pytest.mark.asyncio
    async def test_call_echo_tool(self) -> None:
        runtime = await create_mcp_runtime_with_builtins()
        result = await runtime.call_tool("echo", {"message": "hello"}, "user-1")
        assert result.success is True
        assert result.output == {"message": "hello"}

    @pytest.mark.asyncio
    async def test_call_calculate_tool(self) -> None:
        runtime = await create_mcp_runtime_with_builtins()
        result = await runtime.call_tool("calculate", {"expression": "2 + 2"}, "user-1")
        assert result.success is True
        assert result.output["result"] == 4

    @pytest.mark.asyncio
    async def test_call_read_file_tool(self) -> None:
        runtime = await create_mcp_runtime_with_builtins()
        result = await runtime.call_tool("read_file", {"path": "/tmp/hello.txt"}, "user-1")
        assert result.success is True
        assert result.output["content"] == "Hello, World!"

    @pytest.mark.asyncio
    async def test_call_current_time_tool(self) -> None:
        runtime = await create_mcp_runtime_with_builtins()
        result = await runtime.call_tool("current_time", {}, "user-1")
        assert result.success is True
        assert "unix" in result.output

    @pytest.mark.asyncio
    async def test_call_web_fetch_tool(self) -> None:
        runtime = await create_mcp_runtime_with_builtins()
        result = await runtime.call_tool("web_fetch", {"url": "https://example.com"}, "user-1")
        assert result.success is True
        assert result.output["status"] == 200

    @pytest.mark.asyncio
    async def test_call_nonexistent_tool(self) -> None:
        runtime = await create_mcp_runtime_with_builtins()
        result = await runtime.call_tool("missing_tool", {}, "user-1")
        assert result.success is False
        assert "not found" in (result.error or "")


class TestMCPRuntimeSecurity:
    @pytest.mark.asyncio
    async def test_denied_by_permission(self) -> None:
        runtime = await create_mcp_runtime_with_builtins()
        # Register a tool that requires ADMIN permission
        admin_tool = MCPTool(
            name="admin_action",
            description="Admin only",
            input_schema={},
            permissions=[ToolPermission.ADMIN],
            server_id="builtin",
        )
        await runtime.registry.register(admin_tool)
        runtime._invocation.register_handler(
            "admin_action",
            lambda args: {"done": True},  # noqa: ARG005
        )

        # Default user has only READ
        result = await runtime.call_tool("admin_action", {}, "user-1")
        assert result.success is False
        assert "permission" in (result.error or "").lower()

    @pytest.mark.asyncio
    async def test_allowed_with_permission(self) -> None:
        runtime = await create_mcp_runtime_with_builtins()
        runtime.security_manager.set_user_permissions(
            UserPermissions(
                user_id="admin-user",
                allowed_permissions={"read", "write", "execute", "admin"},
            )
        )
        result = await runtime.call_tool("echo", {"message": "hi"}, "admin-user")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_denied_by_policy(self) -> None:
        runtime = await create_mcp_runtime_with_builtins()
        runtime.security_manager.add_policy(
            ToolPolicy(tool_pattern="read_*", action=SecurityAction.DENY)
        )
        result = await runtime.call_tool("read_file", {"path": "/tmp/hello.txt"}, "user-1")
        assert result.success is False
        assert "denied" in (result.error or "").lower()


class TestMCPRuntimeCircuitBreaker:
    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self) -> None:
        runtime = await create_mcp_runtime_with_builtins()
        # Register a failing tool
        failing_tool = MCPTool(
            name="failing",
            description="Always fails",
            input_schema={},
            permissions=[ToolPermission.READ],
            server_id="builtin",
        )
        await runtime.registry.register(failing_tool)

        async def fail_handler(args: dict) -> dict:
            raise RuntimeError("boom")

        runtime._invocation.register_handler("failing", fail_handler)

        # Trigger failures to open the circuit
        for _ in range(5):
            await runtime.call_tool("failing", {}, "user-1")

        # Circuit should be open now
        result = await runtime.call_tool("failing", {}, "user-1")
        assert result.success is False
        assert "circuit breaker" in (result.error or "").lower()


class TestMCPRuntimeHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_connected(self) -> None:
        runtime = await create_mcp_runtime_with_builtins()
        assert await runtime.health_check("builtin") is True

    @pytest.mark.asyncio
    async def test_health_check_missing(self) -> None:
        runtime = create_mcp_runtime()
        assert await runtime.health_check("missing") is False


class TestMCPRuntimeMetrics:
    @pytest.mark.asyncio
    async def test_metrics_recorded(self) -> None:
        runtime = await create_mcp_runtime_with_builtins()
        await runtime.call_tool("echo", {"message": "a"}, "u1")
        await runtime.call_tool("echo", {"message": "b"}, "u1")
        assert runtime.metrics.total_invocations >= 2

    @pytest.mark.asyncio
    async def test_server_metrics_recorded(self) -> None:
        runtime = await create_mcp_runtime_with_builtins()
        await runtime.call_tool("echo", {"message": "x"}, "u1")
        stats = runtime.metrics.get_server_stats("builtin")
        assert stats is not None
        assert stats.total_calls >= 1
