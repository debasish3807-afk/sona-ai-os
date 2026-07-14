"""Tests for Plugin & MCP Ecosystem (Phase 21)."""

from __future__ import annotations

import pytest

from plugins.manager import PluginManager
from plugins.permissions import check_permission, validate_permissions
from plugins.sandbox import PluginSandbox
from plugins.schemas import (
    MCPPrompt,
    MCPResource,
    MCPTool,
    Permission,
    PluginInfo,
    PluginManifest,
    PluginStatus,
    PluginType,
)


def _make_manifest(
    id: str = "test-plugin",
    name: str = "Test Plugin",
    ptype: PluginType = PluginType.GENERAL,
    perms: list[Permission] | None = None,
) -> PluginManifest:
    return PluginManifest(
        id=id,
        name=name,
        version="1.0.0",
        plugin_type=ptype,
        permissions=perms or [],
    )


class TestSchemas:
    def test_plugin_type(self):
        assert PluginType.AI.value == "ai"
        assert PluginType.RESEARCH.value == "research"
        assert PluginType.GENERAL.value == "general"

    def test_plugin_status(self):
        assert PluginStatus.INSTALLED.value == "installed"
        assert PluginStatus.ENABLED.value == "enabled"

    def test_permission_enum(self):
        assert Permission.NETWORK.value == "network"
        assert Permission.TERMINAL.value == "terminal"

    def test_manifest_defaults(self):
        m = PluginManifest(id="x", name="X", version="1.0.0")
        assert m.plugin_type == PluginType.GENERAL
        assert m.permissions == []
        assert m.entry_point == "main.py"

    def test_mcp_tool(self):
        t = MCPTool(name="run", description="Run cmd")
        assert t.name == "run"

    def test_mcp_resource(self):
        r = MCPResource(uri="sona://mem", name="Memory")
        assert r.uri == "sona://mem"

    def test_mcp_prompt(self):
        p = MCPPrompt(name="review", description="Review code")
        assert p.name == "review"


class TestPermissions:
    def test_valid_permissions(self):
        manifest = _make_manifest(ptype=PluginType.AI, perms=[Permission.AI_COMPLETE])
        assert validate_permissions(manifest) == []

    def test_invalid_permissions(self):
        manifest = _make_manifest(ptype=PluginType.GENERAL, perms=[Permission.TERMINAL])
        violations = validate_permissions(manifest)
        assert len(violations) > 0

    def test_check_permission_granted(self):
        assert check_permission([Permission.NETWORK, Permission.TERMINAL], Permission.NETWORK)

    def test_check_permission_denied(self):
        assert not check_permission([Permission.NETWORK], Permission.TERMINAL)

    def test_research_permissions(self):
        manifest = _make_manifest(
            ptype=PluginType.RESEARCH, perms=[Permission.NETWORK, Permission.RESEARCH]
        )
        assert validate_permissions(manifest) == []


class TestPluginManager:
    def test_install(self):
        mgr = PluginManager()
        manifest = _make_manifest()
        info = mgr.install(manifest)
        assert info.status == PluginStatus.INSTALLED
        assert info.manifest.id == "test-plugin"

    def test_install_invalid_permissions(self):
        mgr = PluginManager()
        manifest = _make_manifest(perms=[Permission.TERMINAL])  # Not allowed for general
        info = mgr.install(manifest)
        assert info.status == PluginStatus.ERROR
        assert "Permission violations" in info.error

    def test_uninstall(self):
        mgr = PluginManager()
        mgr.install(_make_manifest(id="rm-me"))
        assert mgr.uninstall("rm-me") is True

    def test_uninstall_not_found(self):
        mgr = PluginManager()
        assert mgr.uninstall("fake") is False

    def test_enable(self):
        mgr = PluginManager()
        mgr.install(_make_manifest(id="en"))
        assert mgr.enable("en") is True
        assert mgr.get("en").status == PluginStatus.ENABLED

    def test_disable(self):
        mgr = PluginManager()
        mgr.install(_make_manifest(id="dis"))
        mgr.enable("dis")
        assert mgr.disable("dis") is True
        assert mgr.get("dis").status == PluginStatus.DISABLED

    def test_list_all(self):
        mgr = PluginManager()
        mgr.install(_make_manifest(id="a"))
        mgr.install(_make_manifest(id="b"))
        assert len(mgr.list_all()) == 2

    def test_list_enabled(self):
        mgr = PluginManager()
        mgr.install(_make_manifest(id="x"))
        mgr.install(_make_manifest(id="y"))
        mgr.enable("x")
        assert len(mgr.list_enabled()) == 1

    def test_status(self):
        mgr = PluginManager()
        mgr.install(_make_manifest())
        status = mgr.get_status()
        assert status["plugins_installed"] == 1


class TestMCPProtocol:
    def test_register_tool(self):
        mgr = PluginManager()
        mgr.register_mcp_tool(MCPTool(name="test_tool"))
        assert len(mgr.list_mcp_tools()) == 1

    def test_register_resource(self):
        mgr = PluginManager()
        mgr.register_mcp_resource(MCPResource(uri="test://res"))
        assert len(mgr.list_mcp_resources()) == 1

    def test_register_prompt(self):
        mgr = PluginManager()
        mgr.register_mcp_prompt(MCPPrompt(name="test_prompt"))
        assert len(mgr.list_mcp_prompts()) == 1

    @pytest.mark.asyncio
    async def test_execute_tool(self):
        mgr = PluginManager()
        mgr.register_mcp_tool(MCPTool(name="terminal_exec", provider="terminal"))
        result = await mgr.execute_mcp_tool("terminal_exec", {"command": "echo hi"})
        assert "stdout" in result

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        mgr = PluginManager()
        result = await mgr.execute_mcp_tool("nonexistent", {})
        assert "error" in result


class TestSandbox:
    def test_validate_path_allowed(self):
        info = PluginInfo(manifest=_make_manifest(id="sb"))
        sandbox = PluginSandbox(info)
        assert sandbox.validate_path(sandbox.plugin_dir / "data.json") is True

    def test_validate_path_denied(self):
        info = PluginInfo(manifest=_make_manifest(id="sb"))
        sandbox = PluginSandbox(info)
        assert sandbox.validate_path("/etc/passwd") is False

    def test_has_permission(self):
        info = PluginInfo(manifest=_make_manifest(perms=[Permission.NETWORK]))
        sandbox = PluginSandbox(info)
        assert sandbox.has_permission(Permission.NETWORK) is True
        assert sandbox.has_permission(Permission.TERMINAL) is False

    @pytest.mark.asyncio
    async def test_execute_safe_code(self):
        info = PluginInfo(manifest=_make_manifest())
        sandbox = PluginSandbox(info)
        result = await sandbox.execute("result = {'answer': 42}")
        assert result.get("answer") == 42

    @pytest.mark.asyncio
    async def test_execute_error(self):
        info = PluginInfo(manifest=_make_manifest())
        sandbox = PluginSandbox(info)
        result = await sandbox.execute("raise ValueError('bad')")
        assert "error" in result


class TestPluginAPI:
    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from api.plugins import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_list_plugins(self, client):
        resp = client.get("/plugins")
        assert resp.status_code == 200
        assert "plugins" in resp.json()

    def test_install_plugin(self, client):
        resp = client.post(
            "/plugins/install",
            json={
                "id": "test-api",
                "name": "API Test",
                "version": "1.0.0",
                "plugin_type": "general",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["installed"] is True

    def test_plugin_status(self, client):
        resp = client.get("/plugins/status")
        assert resp.status_code == 200
        assert "mcp_tools" in resp.json()

    def test_mcp_tools(self, client):
        resp = client.get("/mcp/tools")
        assert resp.status_code == 200
        tools = resp.json()["tools"]
        assert len(tools) >= 3

    def test_mcp_resources(self, client):
        resp = client.get("/mcp/resources")
        assert resp.status_code == 200
        assert len(resp.json()["resources"]) >= 1

    def test_mcp_prompts(self, client):
        resp = client.get("/mcp/prompts")
        assert resp.status_code == 200
        assert len(resp.json()["prompts"]) >= 1

    def test_execute_mcp_tool(self, client):
        resp = client.post(
            "/mcp/tools/execute",
            json={"tool_name": "terminal_exec", "arguments": {"command": "echo mcp"}},
        )
        assert resp.status_code == 200
        assert "stdout" in resp.json()
