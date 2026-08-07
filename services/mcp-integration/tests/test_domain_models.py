"""Unit tests for MCP Integration domain models.

Tests verify that all domain models, enums, and dataclasses are correctly
defined, instantiate properly, and enforce immutability.
"""

from dataclasses import FrozenInstanceError

import pytest

from sona_mcp.domain.models import (
    MCPServer,
    MCPTool,
    MCPTransport,
    ToolCallResult,
    ToolPermission,
)


class TestMCPTransport:
    """Tests for the MCPTransport enum."""

    def test_all_transports_defined(self) -> None:
        """Verify all expected transport types are available."""
        assert MCPTransport.STDIO == "stdio"
        assert MCPTransport.SSE == "sse"
        assert MCPTransport.WEBSOCKET == "websocket"

    def test_transport_count(self) -> None:
        """Verify exactly 3 transport types exist."""
        assert len(MCPTransport) == 3

    def test_transport_is_str_enum(self) -> None:
        """Verify transports are usable as strings."""
        assert str(MCPTransport.STDIO) == "stdio"
        assert str(MCPTransport.SSE) == "sse"
        assert str(MCPTransport.WEBSOCKET) == "websocket"


class TestToolPermission:
    """Tests for the ToolPermission enum."""

    def test_all_permissions_defined(self) -> None:
        """Verify all expected permission levels are available."""
        assert ToolPermission.READ == "read"
        assert ToolPermission.WRITE == "write"
        assert ToolPermission.EXECUTE == "execute"
        assert ToolPermission.ADMIN == "admin"

    def test_permission_count(self) -> None:
        """Verify exactly 4 permission levels exist."""
        assert len(ToolPermission) == 4

    def test_permission_is_str_enum(self) -> None:
        """Verify permissions are usable as strings."""
        assert str(ToolPermission.READ) == "read"
        assert str(ToolPermission.ADMIN) == "admin"


class TestMCPTool:
    """Tests for the MCPTool frozen dataclass."""

    def test_creation(self) -> None:
        """Create a tool with all required fields."""
        tool = MCPTool(
            name="read_file",
            description="Read contents of a file",
            input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
            permissions=[ToolPermission.READ],
            server_id="server-1",
        )
        assert tool.name == "read_file"
        assert tool.description == "Read contents of a file"
        assert tool.input_schema == {"type": "object", "properties": {"path": {"type": "string"}}}
        assert tool.permissions == [ToolPermission.READ]
        assert tool.server_id == "server-1"

    def test_multiple_permissions(self) -> None:
        """Create a tool with multiple permissions."""
        tool = MCPTool(
            name="execute_command",
            description="Execute a shell command",
            input_schema={"type": "object", "properties": {"command": {"type": "string"}}},
            permissions=[ToolPermission.EXECUTE, ToolPermission.ADMIN],
            server_id="server-2",
        )
        assert len(tool.permissions) == 2
        assert ToolPermission.EXECUTE in tool.permissions
        assert ToolPermission.ADMIN in tool.permissions

    def test_is_frozen(self) -> None:
        """Verify MCPTool is immutable."""
        tool = MCPTool(
            name="test",
            description="test tool",
            input_schema={},
            permissions=[ToolPermission.READ],
            server_id="s1",
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            tool.name = "changed"  # type: ignore[misc]


class TestMCPServer:
    """Tests for the MCPServer frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        server = MCPServer(
            server_id="srv-1",
            name="File System Server",
            transport=MCPTransport.STDIO,
        )
        assert server.server_id == "srv-1"
        assert server.name == "File System Server"
        assert server.transport == MCPTransport.STDIO

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        server = MCPServer(
            server_id="srv-1",
            name="Test Server",
            transport=MCPTransport.STDIO,
        )
        assert server.command is None
        assert server.url is None
        assert server.tools == []

    def test_stdio_server_with_command(self) -> None:
        """Create a STDIO server with a command."""
        server = MCPServer(
            server_id="srv-fs",
            name="Filesystem MCP",
            transport=MCPTransport.STDIO,
            command="npx @modelcontextprotocol/server-filesystem /tmp",
        )
        assert server.command == "npx @modelcontextprotocol/server-filesystem /tmp"
        assert server.url is None

    def test_sse_server_with_url(self) -> None:
        """Create an SSE server with a URL."""
        server = MCPServer(
            server_id="srv-web",
            name="Web Search MCP",
            transport=MCPTransport.SSE,
            url="http://localhost:8080/sse",
        )
        assert server.url == "http://localhost:8080/sse"
        assert server.command is None

    def test_server_with_tools(self) -> None:
        """Create a server with pre-discovered tools."""
        tool = MCPTool(
            name="search",
            description="Search the web",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
            permissions=[ToolPermission.READ],
            server_id="srv-web",
        )
        server = MCPServer(
            server_id="srv-web",
            name="Web Search MCP",
            transport=MCPTransport.SSE,
            url="http://localhost:8080/sse",
            tools=[tool],
        )
        assert len(server.tools) == 1
        assert server.tools[0].name == "search"

    def test_is_frozen(self) -> None:
        """Verify MCPServer is immutable."""
        server = MCPServer(
            server_id="srv-1",
            name="Test",
            transport=MCPTransport.STDIO,
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            server.name = "changed"  # type: ignore[misc]


class TestToolCallResult:
    """Tests for the ToolCallResult frozen dataclass."""

    def test_successful_result(self) -> None:
        """Create a successful tool call result."""
        result = ToolCallResult(
            tool_name="read_file",
            output={"content": "hello world"},
            success=True,
        )
        assert result.tool_name == "read_file"
        assert result.output == {"content": "hello world"}
        assert result.success is True
        assert result.error is None
        assert result.duration_ms == 0.0

    def test_failed_result(self) -> None:
        """Create a failed tool call result."""
        result = ToolCallResult(
            tool_name="write_file",
            output=None,
            success=False,
            error="Permission denied: requires WRITE permission",
            duration_ms=5.2,
        )
        assert result.success is False
        assert result.error == "Permission denied: requires WRITE permission"
        assert result.output is None
        assert result.duration_ms == 5.2

    def test_with_duration(self) -> None:
        """Create a result with custom duration."""
        result = ToolCallResult(
            tool_name="execute_cmd",
            output="command output",
            success=True,
            duration_ms=1250.5,
        )
        assert result.duration_ms == 1250.5

    def test_is_frozen(self) -> None:
        """Verify ToolCallResult is immutable."""
        result = ToolCallResult(
            tool_name="test",
            output="data",
            success=True,
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            result.success = False  # type: ignore[misc]
