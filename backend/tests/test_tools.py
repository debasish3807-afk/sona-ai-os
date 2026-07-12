"""Tool system tests — validates base, registry, permissions, executor, and all tools."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestToolBase:
    """Test base tool types and interfaces."""

    def test_tool_category_enum(self):
        from tools.base import ToolCategory

        assert ToolCategory.FILESYSTEM == "filesystem"
        assert ToolCategory.TERMINAL == "terminal"
        assert ToolCategory.GIT == "git"
        assert ToolCategory.GITHUB == "github"
        assert ToolCategory.BROWSER == "browser"
        assert ToolCategory.PYTHON == "python"
        assert ToolCategory.DATABASE == "database"

    def test_tool_result_creation(self):
        from tools.base import ToolResult

        result = ToolResult(success=True, output="hello", data={"key": "val"})
        assert result.success is True
        assert result.output == "hello"
        assert result.data == {"key": "val"}
        assert result.error is None

    def test_tool_metadata(self):
        from tools.base import ToolCategory, ToolMetadata, ToolParam

        meta = ToolMetadata(
            name="test_tool",
            description="A test tool",
            category=ToolCategory.FILESYSTEM,
            parameters=[ToolParam("path", "string", "File path")],
            dangerous=True,
        )
        assert meta.name == "test_tool"
        assert meta.dangerous is True
        assert len(meta.parameters) == 1


class TestToolRegistry:
    """Test tool registry operations."""

    def test_register_and_get(self):
        from tools.filesystem_tool import FileReadTool
        from tools.permissions import ToolPermissions
        from tools.registry import ToolRegistry

        registry = ToolRegistry()
        perms = ToolPermissions()
        tool = FileReadTool(perms)
        registry.register(tool)

        assert registry.has_tool("file_read")
        assert registry.get("file_read") is tool
        assert registry.tool_count == 1

    def test_list_by_category(self):
        from tools.base import ToolCategory
        from tools.filesystem_tool import register_filesystem_tools
        from tools.permissions import ToolPermissions
        from tools.registry import ToolRegistry

        registry = ToolRegistry()
        perms = ToolPermissions()
        for tool in register_filesystem_tools(perms):
            registry.register(tool)

        fs_tools = registry.list_by_category(ToolCategory.FILESYSTEM)
        assert len(fs_tools) == 9

    def test_to_schema(self):
        from tools.filesystem_tool import FileReadTool
        from tools.permissions import ToolPermissions
        from tools.registry import ToolRegistry

        registry = ToolRegistry()
        perms = ToolPermissions()
        registry.register(FileReadTool(perms))

        schema = registry.to_schema()
        assert len(schema) == 1
        assert schema[0]["name"] == "file_read"
        assert schema[0]["category"] == "filesystem"
        assert len(schema[0]["parameters"]) > 0


class TestPermissions:
    """Test tool permission system."""

    def test_path_within_workspace(self):
        from tools.permissions import ToolPermissions

        perms = ToolPermissions(workspace_root="/tmp/test_workspace")
        assert perms.is_path_allowed("/tmp/test_workspace/file.txt") is True
        assert perms.is_path_allowed("/etc/passwd") is False

    def test_command_allowlist(self):
        from tools.permissions import ToolPermissions

        perms = ToolPermissions()
        assert perms.is_command_allowed("ls -la") is True
        assert perms.is_command_allowed("git status") is True
        assert perms.is_command_allowed("sudo rm -rf /") is False

    def test_command_denylist(self):
        from tools.permissions import ToolPermissions

        perms = ToolPermissions()
        assert perms.is_command_allowed("shutdown now") is False
        assert perms.is_command_allowed("reboot") is False
        assert perms.is_command_allowed("kill -9 1") is False

    def test_truncate_output(self):
        from tools.permissions import ToolPermissions

        perms = ToolPermissions(max_output_length=100)
        short = perms.truncate_output("hello")
        assert short == "hello"

        long_text = "x" * 200
        truncated = perms.truncate_output(long_text)
        assert len(truncated) < 200
        assert "truncated" in truncated


class TestToolExecutor:
    """Test tool executor with permission checks."""

    def test_tool_not_found(self):
        from tools.executor import ToolExecutor
        from tools.permissions import ToolPermissions
        from tools.registry import ToolRegistry

        registry = ToolRegistry()
        perms = ToolPermissions()
        executor = ToolExecutor(registry, perms)

        import asyncio

        result = asyncio.run(executor.run("nonexistent_tool"))
        assert result.success is False
        assert "not found" in result.error

    def test_dangerous_tool_in_safe_mode(self):
        from tools.executor import ToolExecutor
        from tools.filesystem_tool import FileWriteTool
        from tools.permissions import ToolPermissions
        from tools.registry import ToolRegistry

        registry = ToolRegistry()
        perms = ToolPermissions(safe_mode=True)
        registry.register(FileWriteTool(perms))
        executor = ToolExecutor(registry, perms)

        import asyncio

        result = asyncio.run(executor.run("file_write", path="/tmp/x", content="hi"))
        assert result.success is False
        assert "confirmation" in result.error.lower() or "dangerous" in result.error.lower()


class TestFilesystemTools:
    """Test filesystem tool implementations."""

    def test_file_read(self):
        import asyncio

        from tools.filesystem_tool import FileReadTool
        from tools.permissions import ToolPermissions

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line1\nline2\nline3\n")
            path = f.name

        try:
            perms = ToolPermissions(workspace_root=str(Path(path).parent))
            tool = FileReadTool(perms)
            result = asyncio.run(tool.execute(path=path))
            assert result.success is True
            assert "line1" in result.output
            assert result.data["total_lines"] == 3
        finally:
            os.unlink(path)

    def test_file_read_outside_workspace(self):
        import asyncio

        from tools.filesystem_tool import FileReadTool
        from tools.permissions import ToolPermissions

        perms = ToolPermissions(workspace_root="/tmp/isolated_workspace_xyz")
        tool = FileReadTool(perms)
        result = asyncio.run(tool.execute(path="/etc/hostname"))
        assert result.success is False
        assert "Access denied" in result.error

    def test_list_dir(self):
        import asyncio

        from tools.filesystem_tool import ListDirTool
        from tools.permissions import ToolPermissions

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "file1.txt").touch()
            Path(tmpdir, "file2.py").touch()
            Path(tmpdir, "subdir").mkdir()

            perms = ToolPermissions(workspace_root=tmpdir)
            tool = ListDirTool(perms)
            result = asyncio.run(tool.execute(path=tmpdir))
            assert result.success is True
            assert "file1.txt" in result.output
            assert "subdir/" in result.output

    def test_file_search(self):
        import asyncio

        from tools.filesystem_tool import FileSearchTool
        from tools.permissions import ToolPermissions

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.py").touch()
            Path(tmpdir, "test.txt").touch()
            Path(tmpdir, "sub").mkdir()
            Path(tmpdir, "sub", "deep.py").touch()

            perms = ToolPermissions(workspace_root=tmpdir)
            tool = FileSearchTool(perms)
            result = asyncio.run(tool.execute(pattern="*.py", directory=tmpdir))
            assert result.success is True
            assert result.data["count"] == 2


class TestTerminalTool:
    """Test terminal tool."""

    def test_echo_command(self):
        import asyncio

        from tools.permissions import ToolPermissions
        from tools.terminal_tool import TerminalTool

        perms = ToolPermissions(workspace_root="/tmp")
        tool = TerminalTool(perms)
        result = asyncio.run(tool.execute(command="echo hello world", cwd="/tmp"))
        assert result.success is True
        assert "hello world" in result.output

    def test_denied_command(self):
        import asyncio

        from tools.permissions import ToolPermissions
        from tools.terminal_tool import TerminalTool

        perms = ToolPermissions(workspace_root="/tmp")
        tool = TerminalTool(perms)
        result = asyncio.run(tool.execute(command="sudo ls", cwd="/tmp"))
        assert result.success is False
        assert "not permitted" in result.error.lower()

    def test_exit_code_capture(self):
        import asyncio

        from tools.permissions import ToolPermissions
        from tools.terminal_tool import TerminalTool

        perms = ToolPermissions(workspace_root="/tmp")
        tool = TerminalTool(perms)
        result = asyncio.run(tool.execute(command="ls /nonexistent_path_xyz", cwd="/tmp"))
        assert result.success is False
        assert result.data["exit_code"] != 0


class TestGitTool:
    """Test git tool."""

    def test_git_status_not_a_repo(self):
        import asyncio

        from tools.git_tool import GitStatusTool
        from tools.permissions import ToolPermissions

        with tempfile.TemporaryDirectory() as tmpdir:
            perms = ToolPermissions(workspace_root=tmpdir)
            tool = GitStatusTool(perms)
            result = asyncio.run(tool.execute(repo_path=tmpdir))
            assert result.success is False
            assert "Not a git repository" in result.error


class TestMCPServer:
    """Test MCP server initialization and discovery."""

    def test_server_initialization(self):
        from mcp.server import MCPServer
        from tools.permissions import ToolPermissions

        perms = ToolPermissions()
        server = MCPServer(perms)
        server.initialize()

        assert server.is_initialized is True
        assert server.registry.tool_count > 20  # We have 28+ tools

    def test_tool_discovery(self):
        from mcp.server import MCPServer
        from tools.permissions import ToolPermissions

        perms = ToolPermissions()
        server = MCPServer(perms)
        server.initialize()

        tools = server.discover_tools()
        assert len(tools) > 20
        names = [t["name"] for t in tools]
        assert "file_read" in names
        assert "terminal_exec" in names
        assert "git_status" in names
        assert "github_repo_info" in names
        assert "browser_fetch" in names
        assert "python_exec" in names
        assert "db_query" in names

    def test_server_status(self):
        from mcp.server import MCPServer
        from tools.permissions import ToolPermissions

        perms = ToolPermissions()
        server = MCPServer(perms)
        server.initialize()

        status = server.get_status()
        assert status["initialized"] is True
        assert status["tools_registered"] > 20
        assert status["safe_mode"] is True


class TestMCPSession:
    """Test MCP session management."""

    def test_session_create(self):
        from mcp.session import MCPSessionManager

        mgr = MCPSessionManager()
        session = mgr.create_session()
        assert session.session_id is not None
        assert session.status.value == "active"
        assert mgr.active_count == 1

    def test_session_record_execution(self):
        from mcp.session import MCPSession

        session = MCPSession()
        session.record_execution("file_read", True, 5.0)
        session.record_execution("terminal_exec", False, 100.0)
        assert session.execution_count == 2
        assert len(session.history) == 2

    def test_session_close(self):
        from mcp.session import MCPSessionManager

        mgr = MCPSessionManager()
        session = mgr.create_session()
        mgr.close_session(session.session_id)
        assert session.status.value == "closed"

    def test_get_or_create(self):
        from mcp.session import MCPSessionManager

        mgr = MCPSessionManager()
        s1 = mgr.get_or_create(None)
        s2 = mgr.get_or_create(s1.session_id)
        assert s1.session_id == s2.session_id

        s3 = mgr.get_or_create("nonexistent-id")
        assert s3.session_id != s1.session_id


class TestDatabaseTool:
    """Test database tool."""

    def test_create_and_query(self):
        import asyncio

        from tools.database_tool import DatabaseQueryTool
        from tools.permissions import ToolPermissions

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            perms = ToolPermissions(workspace_root=tmpdir, safe_mode=False)
            tool = DatabaseQueryTool(perms)

            # Create table
            result = asyncio.run(
                tool.execute(
                    database=db_path, query="CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
                )
            )
            assert result.success is True

            # Insert
            result = asyncio.run(
                tool.execute(database=db_path, query="INSERT INTO users (name) VALUES ('Alice')")
            )
            assert result.success is True

            # Select
            result = asyncio.run(tool.execute(database=db_path, query="SELECT * FROM users"))
            assert result.success is True
            assert "Alice" in result.output


class TestPythonTool:
    """Test Python sandbox execution."""

    def test_simple_execution(self):
        import asyncio

        from tools.permissions import ToolPermissions
        from tools.python_tool import PythonExecTool

        perms = ToolPermissions(safe_mode=False)
        tool = PythonExecTool(perms)
        result = asyncio.run(tool.execute(code="print('hello from sandbox')"))
        assert result.success is True
        assert "hello from sandbox" in result.output

    def test_blocked_module(self):
        import asyncio

        from tools.permissions import ToolPermissions
        from tools.python_tool import PythonExecTool

        perms = ToolPermissions(safe_mode=False)
        tool = PythonExecTool(perms)
        result = asyncio.run(tool.execute(code="import subprocess"))
        assert result.success is False
        assert "Blocked" in result.error

    def test_exception_capture(self):
        import asyncio

        from tools.permissions import ToolPermissions
        from tools.python_tool import PythonExecTool

        perms = ToolPermissions(safe_mode=False)
        tool = PythonExecTool(perms)
        result = asyncio.run(tool.execute(code="raise ValueError('test error')"))
        assert result.success is False
        assert "ValueError" in result.error
