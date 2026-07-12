"""Tool API endpoints — public interface to the MCP tool system.

Endpoints:
    GET  /tools          — List all available tools with metadata
    POST /tools/run      — Execute a tool by name with parameters
    GET  /tools/status   — Tool system status and metrics
    GET  /mcp            — MCP server info and capabilities
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.logging import get_logger
from mcp.server import get_mcp_server

logger = get_logger(__name__)

router = APIRouter(tags=["tools"])


# --- Request/Response Schemas ---


class ToolRunRequest(BaseModel):
    """POST /tools/run request body."""

    tool: str = Field(..., description="Name of the tool to execute")
    params: dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    session_id: str | None = Field(default=None, description="Session ID for tracking")


class ToolRunResponse(BaseModel):
    """POST /tools/run response body."""

    success: bool
    tool: str
    output: str = ""
    error: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0


class ToolInfoResponse(BaseModel):
    """Single tool info in listing."""

    name: str
    description: str
    category: str
    dangerous: bool
    read_only: bool
    parameters: list[dict[str, Any]]


class ToolListResponse(BaseModel):
    """GET /tools response body."""

    success: bool = True
    tools: list[ToolInfoResponse]
    total: int


class ToolStatusResponse(BaseModel):
    """GET /tools/status response body."""

    success: bool = True
    initialized: bool
    tools_registered: int
    active_sessions: int
    total_executions: int
    safe_mode: bool
    workspace: str


class MCPInfoResponse(BaseModel):
    """GET /mcp response body."""

    success: bool = True
    protocol: str = "mcp"
    version: str = "1.0"
    server_name: str = "sona-ai-os"
    capabilities: list[str]
    tools_count: int
    status: str


# --- Endpoints ---


@router.get("/tools", response_model=ToolListResponse)
async def list_tools() -> ToolListResponse:
    """List all available tools with their metadata and parameters.

    Returns tool names, descriptions, categories, parameter definitions,
    and safety markers. Used by the AI Brain for tool selection.
    """
    mcp = get_mcp_server()
    schema = mcp.discover_tools()

    tools = [
        ToolInfoResponse(
            name=t["name"],
            description=t["description"],
            category=t["category"],
            dangerous=t["dangerous"],
            read_only=t["read_only"],
            parameters=t["parameters"],
        )
        for t in schema
    ]

    return ToolListResponse(tools=tools, total=len(tools))


@router.post("/tools/run", response_model=ToolRunResponse)
async def run_tool(request: ToolRunRequest) -> ToolRunResponse:
    """Execute a tool by name with the given parameters.

    The tool system validates permissions, enforces timeouts,
    and tracks execution in the session.

    Returns:
        ToolRunResponse with output or error details.
    """
    mcp = get_mcp_server()

    if not mcp.registry.has_tool(request.tool):
        raise HTTPException(status_code=404, detail=f"Tool not found: {request.tool}")

    result = await mcp.execute_tool(
        tool_name=request.tool,
        params=request.params,
        session_id=request.session_id,
    )

    return ToolRunResponse(
        success=result.success,
        tool=result.tool_name,
        output=result.output,
        error=result.error,
        data=result.data,
        duration_ms=result.duration_ms,
    )


@router.get("/tools/status", response_model=ToolStatusResponse)
async def tool_status() -> ToolStatusResponse:
    """Get tool system status and metrics.

    Returns registration count, active sessions, execution totals,
    and safety configuration.
    """
    mcp = get_mcp_server()
    status = mcp.get_status()

    return ToolStatusResponse(
        initialized=status["initialized"],
        tools_registered=status["tools_registered"],
        active_sessions=status["active_sessions"],
        total_executions=status["total_executions"],
        safe_mode=status["safe_mode"],
        workspace=status["workspace"],
    )


@router.get("/mcp", response_model=MCPInfoResponse)
async def mcp_info() -> MCPInfoResponse:
    """Get MCP server information and capabilities.

    Returns protocol version, server name, supported capabilities,
    and current operational status.
    """
    mcp = get_mcp_server()
    status = mcp.get_status()

    capabilities = [
        "tools/list",
        "tools/call",
        "tools/status",
        "sessions/create",
        "sessions/track",
    ]

    return MCPInfoResponse(
        capabilities=capabilities,
        tools_count=status["tools_registered"],
        status="running" if status["initialized"] else "stopped",
    )
