"""Unit tests for ToolInvocationEngine."""

import pytest

from sona_mcp.domain.models import MCPTool, ToolPermission
from sona_mcp.domain.security import UserPermissions
from sona_mcp.infrastructure.metrics import MCPMetrics
from sona_mcp.infrastructure.security_manager import SecurityManager
from sona_mcp.infrastructure.tool_invocation import ToolInvocationEngine
from sona_mcp.infrastructure.tool_registry import ToolRegistry


async def _echo_handler(args: dict) -> dict:
    return {"echo": args.get("message", "")}


async def _slow_handler(args: dict) -> dict:
    import asyncio

    await asyncio.sleep(5.0)
    return {"done": True}


async def _error_handler(args: dict) -> dict:
    raise RuntimeError("Tool exploded!")


def _setup() -> tuple[ToolInvocationEngine, ToolRegistry, SecurityManager]:
    registry = ToolRegistry()
    security = SecurityManager()
    metrics = MCPMetrics()
    engine = ToolInvocationEngine(registry=registry, security_manager=security, metrics=metrics)
    return engine, registry, security


class TestToolInvocationSuccess:
    @pytest.mark.asyncio
    async def test_successful_invocation(self) -> None:
        engine, registry, security = _setup()
        tool = MCPTool(
            name="echo",
            description="Echo",
            input_schema={},
            permissions=[ToolPermission.READ],
            server_id="s1",
        )
        await registry.register(tool)
        engine.register_handler("echo", _echo_handler)

        result = await engine.invoke("echo", {"message": "hi"}, "user-1")
        assert result.success is True
        assert result.output == {"echo": "hi"}
        assert result.duration_ms > 0

    @pytest.mark.asyncio
    async def test_invocation_records_metrics(self) -> None:
        engine, registry, _ = _setup()
        tool = MCPTool(
            name="echo",
            description="Echo",
            input_schema={},
            permissions=[ToolPermission.READ],
            server_id="s1",
        )
        await registry.register(tool)
        engine.register_handler("echo", _echo_handler)

        await engine.invoke("echo", {"message": "test"}, "user-1")
        # Metrics are recorded internally

    @pytest.mark.asyncio
    async def test_invocation_emits_event(self) -> None:
        engine, registry, _ = _setup()
        tool = MCPTool(
            name="echo",
            description="Echo",
            input_schema={},
            permissions=[ToolPermission.READ],
            server_id="s1",
        )
        await registry.register(tool)
        engine.register_handler("echo", _echo_handler)

        await engine.invoke("echo", {}, "user-1")
        events = engine.events
        assert len(events) == 1
        assert events[0].tool_name == "echo"


class TestToolInvocationPermissions:
    @pytest.mark.asyncio
    async def test_denied_by_missing_permission(self) -> None:
        engine, registry, security = _setup()
        tool = MCPTool(
            name="admin_tool",
            description="Admin",
            input_schema={},
            permissions=[ToolPermission.ADMIN],
            server_id="s1",
        )
        await registry.register(tool)
        engine.register_handler("admin_tool", _echo_handler)

        # User only has 'read' permission by default
        result = await engine.invoke("admin_tool", {}, "user-1")
        assert result.success is False
        assert "lacks required permission" in (result.error or "")

    @pytest.mark.asyncio
    async def test_allowed_with_correct_permission(self) -> None:
        engine, registry, security = _setup()
        tool = MCPTool(
            name="writer",
            description="Write",
            input_schema={},
            permissions=[ToolPermission.WRITE],
            server_id="s1",
        )
        await registry.register(tool)
        engine.register_handler("writer", _echo_handler)

        security.set_user_permissions(
            UserPermissions(
                user_id="user-1",
                allowed_permissions={"read", "write"},
            )
        )
        result = await engine.invoke("writer", {"message": "data"}, "user-1")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_denied_tool_in_user_denied_list(self) -> None:
        engine, registry, security = _setup()
        tool = MCPTool(
            name="forbidden",
            description="Forbidden",
            input_schema={},
            permissions=[ToolPermission.READ],
            server_id="s1",
        )
        await registry.register(tool)
        engine.register_handler("forbidden", _echo_handler)

        security.set_user_permissions(
            UserPermissions(
                user_id="user-1",
                denied_tools={"forbidden"},
            )
        )
        result = await engine.invoke("forbidden", {}, "user-1")
        assert result.success is False
        assert "denied" in (result.error or "").lower()


class TestToolInvocationValidation:
    @pytest.mark.asyncio
    async def test_tool_not_found(self) -> None:
        engine, _, _ = _setup()
        result = await engine.invoke("missing_tool", {}, "user-1")
        assert result.success is False
        assert "not found" in (result.error or "")

    @pytest.mark.asyncio
    async def test_missing_required_field(self) -> None:
        engine, registry, _ = _setup()
        tool = MCPTool(
            name="need_path",
            description="Needs path",
            input_schema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            permissions=[ToolPermission.READ],
            server_id="s1",
        )
        await registry.register(tool)
        engine.register_handler("need_path", _echo_handler)

        result = await engine.invoke("need_path", {}, "user-1")
        assert result.success is False
        assert "required" in (result.error or "").lower()

    @pytest.mark.asyncio
    async def test_wrong_type_field(self) -> None:
        engine, registry, _ = _setup()
        tool = MCPTool(
            name="typed",
            description="Typed",
            input_schema={
                "type": "object",
                "properties": {"count": {"type": "integer"}},
            },
            permissions=[ToolPermission.READ],
            server_id="s1",
        )
        await registry.register(tool)
        engine.register_handler("typed", _echo_handler)

        result = await engine.invoke("typed", {"count": "not_int"}, "user-1")
        assert result.success is False
        assert "type" in (result.error or "").lower()


class TestToolInvocationTimeout:
    @pytest.mark.asyncio
    async def test_timeout_handling(self) -> None:
        engine, registry, _ = _setup()
        tool = MCPTool(
            name="slow",
            description="Slow",
            input_schema={},
            permissions=[ToolPermission.READ],
            server_id="s1",
        )
        await registry.register(tool)
        engine.register_handler("slow", _slow_handler)

        result = await engine.invoke("slow", {}, "user-1", timeout=0.01)
        assert result.success is False
        assert "timed out" in (result.error or "")


class TestToolInvocationErrors:
    @pytest.mark.asyncio
    async def test_handler_exception(self) -> None:
        engine, registry, _ = _setup()
        tool = MCPTool(
            name="broken",
            description="Broken",
            input_schema={},
            permissions=[ToolPermission.READ],
            server_id="s1",
        )
        await registry.register(tool)
        engine.register_handler("broken", _error_handler)

        result = await engine.invoke("broken", {}, "user-1")
        assert result.success is False
        assert "exploded" in (result.error or "")

    @pytest.mark.asyncio
    async def test_no_handler_registered(self) -> None:
        engine, registry, _ = _setup()
        tool = MCPTool(
            name="no_handler",
            description="No handler",
            input_schema={},
            permissions=[ToolPermission.READ],
            server_id="s1",
        )
        await registry.register(tool)

        result = await engine.invoke("no_handler", {}, "user-1")
        assert result.success is False
        assert "handler" in (result.error or "").lower()
