"""Plugin & MCP API — plugin management and MCP protocol."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from config.logging import get_logger
from plugins.manager import PluginManager
from plugins.schemas import (
    MCPPrompt,
    MCPResource,
    MCPTool,
    Permission,
    PluginManifest,
    PluginType,
)

logger = get_logger(__name__)
router = APIRouter(tags=["plugins"])

_manager = PluginManager()

# Register built-in MCP tools
_manager.register_mcp_tool(
    MCPTool(
        name="terminal_exec",
        description="Execute shell command",
        provider="terminal",
        parameters={"command": "string"},
    )
)
_manager.register_mcp_tool(
    MCPTool(
        name="file_read",
        description="Read a file",
        provider="filesystem",
        parameters={"path": "string"},
    )
)
_manager.register_mcp_tool(
    MCPTool(
        name="memory_store",
        description="Store in memory",
        provider="memory",
        parameters={"content": "string"},
    )
)
_manager.register_mcp_tool(
    MCPTool(
        name="deep_research",
        description="Run deep research",
        provider="research",
        parameters={"query": "string"},
    )
)
_manager.register_mcp_tool(
    MCPTool(
        name="ocr_image",
        description="OCR an image",
        provider="vision",
        parameters={"image_base64": "string"},
    )
)
_manager.register_mcp_resource(
    MCPResource(uri="sona://memory", name="Memory", description="Access AI memory")
)
_manager.register_mcp_resource(
    MCPResource(uri="sona://knowledge", name="Knowledge Base", description="Search knowledge")
)
_manager.register_mcp_prompt(
    MCPPrompt(
        name="code_review",
        description="Review code for issues",
        arguments=[{"name": "code", "type": "string"}],
        template="Review this code for bugs and improvements:\n\n{{code}}",
    )
)
_manager.register_mcp_prompt(
    MCPPrompt(
        name="research_topic",
        description="Research a topic",
        arguments=[{"name": "topic", "type": "string"}],
        template="Research the following topic thoroughly:\n\n{{topic}}",
    )
)


class InstallRequest(BaseModel):
    id: str
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    plugin_type: str = "general"
    permissions: list[str] = Field(default_factory=list)


class MCPToolExecRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


# ─── Plugin Endpoints ─────────────────────────────────────────────────────


@router.get("/plugins")
async def list_plugins() -> dict[str, Any]:
    plugins = _manager.list_all()
    return {
        "plugins": [
            {
                "id": p.manifest.id,
                "name": p.manifest.name,
                "status": p.status.value,
                "version": p.manifest.version,
            }
            for p in plugins
        ],
        "count": len(plugins),
    }


@router.post("/plugins/install")
async def install_plugin(req: InstallRequest) -> dict[str, Any]:
    try:
        ptype = PluginType(req.plugin_type)
    except ValueError:
        ptype = PluginType.GENERAL
    perms = []
    for p in req.permissions:
        try:
            perms.append(Permission(p))
        except ValueError:
            pass
    manifest = PluginManifest(
        id=req.id,
        name=req.name,
        version=req.version,
        description=req.description,
        author=req.author,
        plugin_type=ptype,
        permissions=perms,
    )
    info = _manager.install(manifest)
    return {
        "installed": info.status.value != "error",
        "id": info.manifest.id,
        "status": info.status.value,
        "error": info.error,
    }


@router.post("/plugins/remove")
async def remove_plugin(plugin_id: str) -> dict[str, Any]:
    return {"removed": _manager.uninstall(plugin_id)}


@router.post("/plugins/enable")
async def enable_plugin(plugin_id: str) -> dict[str, Any]:
    return {"enabled": _manager.enable(plugin_id)}


@router.post("/plugins/disable")
async def disable_plugin(plugin_id: str) -> dict[str, Any]:
    return {"disabled": _manager.disable(plugin_id)}


@router.get("/plugins/status")
async def plugin_status() -> dict[str, Any]:
    return _manager.get_status()


# ─── MCP Endpoints ────────────────────────────────────────────────────────


@router.get("/mcp/tools")
async def list_mcp_tools() -> dict[str, Any]:
    tools = _manager.list_mcp_tools()
    return {
        "tools": [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in tools
        ]
    }


@router.get("/mcp/resources")
async def list_mcp_resources() -> dict[str, Any]:
    resources = _manager.list_mcp_resources()
    return {
        "resources": [
            {"uri": r.uri, "name": r.name, "description": r.description} for r in resources
        ]
    }


@router.get("/mcp/prompts")
async def list_mcp_prompts() -> dict[str, Any]:
    prompts = _manager.list_mcp_prompts()
    return {
        "prompts": [
            {"name": p.name, "description": p.description, "arguments": p.arguments}
            for p in prompts
        ]
    }


@router.post("/mcp/tools/execute")
async def execute_mcp_tool(req: MCPToolExecRequest) -> dict[str, Any]:
    return await _manager.execute_mcp_tool(req.tool_name, req.arguments)
