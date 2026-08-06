"""Unit tests for MCP Integration abstract port interfaces.

Tests verify that port interfaces are correctly defined, enforce
abstractness, and that concrete implementations must satisfy all methods.
"""

import pytest
from application.ports import MCPManagerPort
from domain.models import (
    MCPServer,
    MCPTool,
    MCPTransport,
    ToolCallResult,
    ToolPermission,
)


class TestMCPManagerPort:
    """Tests for the MCPManagerPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify MCPManagerPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MCPManagerPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = MCPManagerPort.__abstractmethods__
        assert "register_server" in abstract_methods
        assert "discover_tools" in abstract_methods
        assert "call_tool" in abstract_methods
        assert "list_servers" in abstract_methods
        assert "health_check" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteMCPManager(MCPManagerPort):
            async def register_server(self, server: MCPServer) -> str:
                return server.server_id

            async def discover_tools(self, server_id: str) -> list[MCPTool]:
                return []

            async def call_tool(
                self, tool_name: str, arguments: dict, user_id: str
            ) -> ToolCallResult:
                return ToolCallResult(tool_name=tool_name, output=None, success=True)

            async def list_servers(self) -> list[MCPServer]:
                return []

            async def health_check(self, server_id: str) -> bool:
                return True

        manager = ConcreteMCPManager()
        assert isinstance(manager, MCPManagerPort)

    @pytest.mark.asyncio
    async def test_register_server_returns_id(self) -> None:
        """Test that a concrete register_server() returns a server ID."""

        class MockMCPManager(MCPManagerPort):
            async def register_server(self, server: MCPServer) -> str:
                return server.server_id

            async def discover_tools(self, server_id: str) -> list[MCPTool]:
                return []

            async def call_tool(
                self, tool_name: str, arguments: dict, user_id: str
            ) -> ToolCallResult:
                return ToolCallResult(tool_name=tool_name, output=None, success=True)

            async def list_servers(self) -> list[MCPServer]:
                return []

            async def health_check(self, server_id: str) -> bool:
                return True

        manager = MockMCPManager()
        server = MCPServer(
            server_id="srv-test",
            name="Test Server",
            transport=MCPTransport.STDIO,
            command="npx test-server",
        )
        result = await manager.register_server(server)
        assert result == "srv-test"

    @pytest.mark.asyncio
    async def test_discover_tools_returns_tool_list(self) -> None:
        """Test that discover_tools() returns a list of MCPTool."""

        class MockMCPManager(MCPManagerPort):
            async def register_server(self, server: MCPServer) -> str:
                return server.server_id

            async def discover_tools(self, server_id: str) -> list[MCPTool]:
                return [
                    MCPTool(
                        name="read_file",
                        description="Read a file",
                        input_schema={"type": "object"},
                        permissions=[ToolPermission.READ],
                        server_id=server_id,
                    ),
                ]

            async def call_tool(
                self, tool_name: str, arguments: dict, user_id: str
            ) -> ToolCallResult:
                return ToolCallResult(tool_name=tool_name, output=None, success=True)

            async def list_servers(self) -> list[MCPServer]:
                return []

            async def health_check(self, server_id: str) -> bool:
                return True

        manager = MockMCPManager()
        tools = await manager.discover_tools("srv-1")
        assert len(tools) == 1
        assert tools[0].name == "read_file"
        assert isinstance(tools[0], MCPTool)

    @pytest.mark.asyncio
    async def test_call_tool_returns_result(self) -> None:
        """Test that call_tool() returns a ToolCallResult."""

        class MockMCPManager(MCPManagerPort):
            async def register_server(self, server: MCPServer) -> str:
                return server.server_id

            async def discover_tools(self, server_id: str) -> list[MCPTool]:
                return []

            async def call_tool(
                self, tool_name: str, arguments: dict, user_id: str
            ) -> ToolCallResult:
                return ToolCallResult(
                    tool_name=tool_name,
                    output={"result": "success"},
                    success=True,
                    duration_ms=42.0,
                )

            async def list_servers(self) -> list[MCPServer]:
                return []

            async def health_check(self, server_id: str) -> bool:
                return True

        manager = MockMCPManager()
        result = await manager.call_tool(
            tool_name="search",
            arguments={"query": "test"},
            user_id="user-1",
        )
        assert result.tool_name == "search"
        assert result.success is True
        assert result.output == {"result": "success"}
        assert result.duration_ms == 42.0
        assert isinstance(result, ToolCallResult)

    @pytest.mark.asyncio
    async def test_list_servers_returns_server_list(self) -> None:
        """Test that list_servers() returns registered servers."""

        class MockMCPManager(MCPManagerPort):
            async def register_server(self, server: MCPServer) -> str:
                return server.server_id

            async def discover_tools(self, server_id: str) -> list[MCPTool]:
                return []

            async def call_tool(
                self, tool_name: str, arguments: dict, user_id: str
            ) -> ToolCallResult:
                return ToolCallResult(tool_name=tool_name, output=None, success=True)

            async def list_servers(self) -> list[MCPServer]:
                return [
                    MCPServer(
                        server_id="srv-1",
                        name="Server One",
                        transport=MCPTransport.STDIO,
                    ),
                    MCPServer(
                        server_id="srv-2",
                        name="Server Two",
                        transport=MCPTransport.SSE,
                        url="http://localhost:9090/sse",
                    ),
                ]

            async def health_check(self, server_id: str) -> bool:
                return True

        manager = MockMCPManager()
        servers = await manager.list_servers()
        assert len(servers) == 2
        assert all(isinstance(s, MCPServer) for s in servers)

    @pytest.mark.asyncio
    async def test_health_check_returns_bool(self) -> None:
        """Test that health_check() returns a boolean status."""

        class MockMCPManager(MCPManagerPort):
            async def register_server(self, server: MCPServer) -> str:
                return server.server_id

            async def discover_tools(self, server_id: str) -> list[MCPTool]:
                return []

            async def call_tool(
                self, tool_name: str, arguments: dict, user_id: str
            ) -> ToolCallResult:
                return ToolCallResult(tool_name=tool_name, output=None, success=True)

            async def list_servers(self) -> list[MCPServer]:
                return []

            async def health_check(self, server_id: str) -> bool:
                return server_id == "healthy-server"

        manager = MockMCPManager()
        assert await manager.health_check("healthy-server") is True
        assert await manager.health_check("dead-server") is False
