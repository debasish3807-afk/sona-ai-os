"""Plugin Manager — install, enable, disable, update plugins."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger
from plugins.permissions import validate_permissions
from plugins.sandbox import PLUGINS_DIR
from plugins.schemas import (
    MCPPrompt,
    MCPResource,
    MCPTool,
    PluginInfo,
    PluginManifest,
    PluginStatus,
)

logger = get_logger(__name__)


class PluginManager:
    """Central plugin lifecycle manager."""

    def __init__(self) -> None:
        self._plugins: dict[str, PluginInfo] = {}
        self._mcp_tools: list[MCPTool] = []
        self._mcp_resources: list[MCPResource] = []
        self._mcp_prompts: list[MCPPrompt] = []
        PLUGINS_DIR.mkdir(parents=True, exist_ok=True)

    # ─── Plugin CRUD ──────────────────────────────────────────────────

    def install(self, manifest: PluginManifest) -> PluginInfo:
        """Install a plugin from its manifest."""
        # Validate permissions
        violations = validate_permissions(manifest)
        if violations:
            info = PluginInfo(
                manifest=manifest,
                status=PluginStatus.ERROR,
                error=f"Permission violations: {violations}",
            )
            return info

        # Create plugin directory
        plugin_dir = PLUGINS_DIR / manifest.id
        plugin_dir.mkdir(parents=True, exist_ok=True)

        info = PluginInfo(
            manifest=manifest,
            status=PluginStatus.INSTALLED,
            installed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            path=str(plugin_dir),
        )
        self._plugins[manifest.id] = info
        logger.info("plugin_installed", id=manifest.id, name=manifest.name)
        return info

    def uninstall(self, plugin_id: str) -> bool:
        """Remove a plugin."""
        if plugin_id not in self._plugins:
            return False
        del self._plugins[plugin_id]
        logger.info("plugin_uninstalled", id=plugin_id)
        return True

    def enable(self, plugin_id: str) -> bool:
        """Enable a plugin."""
        info = self._plugins.get(plugin_id)
        if info is None:
            return False
        info.status = PluginStatus.ENABLED
        return True

    def disable(self, plugin_id: str) -> bool:
        """Disable a plugin."""
        info = self._plugins.get(plugin_id)
        if info is None:
            return False
        info.status = PluginStatus.DISABLED
        return True

    def get(self, plugin_id: str) -> PluginInfo | None:
        """Get plugin info."""
        return self._plugins.get(plugin_id)

    def list_all(self) -> list[PluginInfo]:
        """List all installed plugins."""
        return list(self._plugins.values())

    def list_enabled(self) -> list[PluginInfo]:
        """List enabled plugins only."""
        return [p for p in self._plugins.values() if p.status == PluginStatus.ENABLED]

    # ─── MCP ─────────────────────────────────────────────────────────

    def register_mcp_tool(self, tool: MCPTool) -> None:
        """Register an MCP tool."""
        self._mcp_tools.append(tool)

    def register_mcp_resource(self, resource: MCPResource) -> None:
        """Register an MCP resource."""
        self._mcp_resources.append(resource)

    def register_mcp_prompt(self, prompt: MCPPrompt) -> None:
        """Register an MCP prompt template."""
        self._mcp_prompts.append(prompt)

    def list_mcp_tools(self) -> list[MCPTool]:
        return self._mcp_tools

    def list_mcp_resources(self) -> list[MCPResource]:
        return self._mcp_resources

    def list_mcp_prompts(self) -> list[MCPPrompt]:
        return self._mcp_prompts

    async def execute_mcp_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute an MCP tool by name."""
        for tool in self._mcp_tools:
            if tool.name == tool_name:
                # Route to appropriate handler
                return await self._route_tool(tool, args)
        return {"error": f"Tool not found: {tool_name}"}

    async def _route_tool(self, tool: MCPTool, args: dict[str, Any]) -> dict[str, Any]:
        """Route tool execution to the correct subsystem."""
        provider = tool.provider
        if provider == "terminal":
            import asyncio

            cmd = args.get("command", "echo hello")
            proc = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            out, err = await proc.communicate()
            return {"stdout": out.decode(), "stderr": err.decode(), "code": proc.returncode}
        if provider == "memory":
            return {"stored": True, "content": args.get("content", "")}
        if provider == "research":
            return {"started": True, "query": args.get("query", "")}
        return {"executed": True, "tool": tool.name, "args": args}

    # ─── Status ───────────────────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        return {
            "plugins_installed": len(self._plugins),
            "plugins_enabled": len(self.list_enabled()),
            "mcp_tools": len(self._mcp_tools),
            "mcp_resources": len(self._mcp_resources),
            "mcp_prompts": len(self._mcp_prompts),
        }
