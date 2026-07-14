"""Desktop Workspace API — unified endpoints for the AI workspace.

Provides endpoints for:
- Streaming AI chat (SSE)
- File browsing and content
- Memory operations
- Terminal execution
- Conversation management
- Settings
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/workspace", tags=["workspace"])

# ─── Schemas ─────────────────────────────────────────────────────────────────


class ChatMessage(BaseModel):
    """A message in a chat conversation."""

    role: str = "user"
    content: str


class ChatRequest(BaseModel):
    """Request for AI chat completion."""

    messages: list[ChatMessage]
    model: str = ""
    provider: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = True
    system_prompt: str = ""
    conversation_id: str = ""


class FileNode(BaseModel):
    """A file or directory node."""

    name: str
    path: str
    is_dir: bool
    size: int = 0
    extension: str = ""
    children: list[FileNode] | None = None


class TerminalRequest(BaseModel):
    """Request to execute a terminal command."""

    command: str
    cwd: str = ""
    timeout: int = 30


class MemoryEntry(BaseModel):
    """A memory entry."""

    content: str
    memory_type: str = "conversation"
    importance: float = 0.5
    tags: list[str] = Field(default_factory=list)


class ConversationSummary(BaseModel):
    """Summary of a conversation."""

    id: str
    title: str
    created_at: str
    message_count: int
    pinned: bool = False


class SettingsUpdate(BaseModel):
    """Settings update request."""

    provider: str = ""
    model: str = ""
    theme: str = ""
    temperature: float | None = None
    max_tokens: int | None = None
    research_depth: str = ""


# ─── Chat (SSE Streaming) ────────────────────────────────────────────────────


@router.post("/chat")
async def workspace_chat(request: ChatRequest) -> StreamingResponse:
    """Stream AI chat responses via Server-Sent Events."""
    from ai.ollama_provider import OllamaProvider
    from ai.schemas import AIMessage, AIRequest

    provider = OllamaProvider()
    ai_request = AIRequest(
        messages=[AIMessage(role=m.role, content=m.content) for m in request.messages],
        model=request.model or "llama3",
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        system_prompt=request.system_prompt,
    )

    async def event_stream():
        try:
            async for chunk in provider.stream(ai_request):
                data = json.dumps({"type": "chunk", "content": chunk})
                yield f"data: {data}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as exc:
            error_data = json.dumps({"type": "error", "message": str(exc)})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/complete")
async def workspace_chat_complete(request: ChatRequest) -> dict[str, Any]:
    """Non-streaming chat completion."""
    from ai.ollama_provider import OllamaProvider
    from ai.schemas import AIMessage, AIRequest

    provider = OllamaProvider()
    ai_request = AIRequest(
        messages=[AIMessage(role=m.role, content=m.content) for m in request.messages],
        model=request.model or "llama3",
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        system_prompt=request.system_prompt,
    )
    response = await provider.complete(ai_request)
    return {
        "content": response.content,
        "model": response.model,
        "provider": response.provider,
        "tokens_used": response.tokens_used,
        "latency_ms": response.latency_ms,
    }


# ─── File Explorer ────────────────────────────────────────────────────────────

WORKSPACE_ROOT = Path(os.environ.get("SONA_WORKSPACE", ".")).resolve()
ALLOWED_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".cfg",
    ".ini",
    ".html",
    ".css",
    ".scss",
    ".sql",
    ".sh",
    ".bash",
    ".dockerfile",
    ".env",
    ".gitignore",
    ".rs",
    ".go",
    ".java",
    ".kt",
    ".swift",
    ".c",
    ".cpp",
    ".h",
    ".rb",
    ".php",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico"}
MAX_FILE_SIZE = 1_000_000  # 1MB


@router.get("/files")
async def list_files(
    path: str = Query("", description="Relative path from workspace root"),
    depth: int = Query(1, description="Directory depth to return"),
) -> dict[str, Any]:
    """List files and directories in the workspace."""
    target = (WORKSPACE_ROOT / path).resolve()
    if not str(target).startswith(str(WORKSPACE_ROOT)):
        return {"error": "Path traversal denied", "nodes": []}

    if not target.exists():
        return {"error": "Path not found", "nodes": []}

    nodes = _scan_directory(target, depth=depth, current_depth=0)
    return {"path": path, "nodes": nodes}


@router.get("/files/content")
async def read_file_content(
    path: str = Query(..., description="Relative path to file"),
) -> dict[str, Any]:
    """Read file content with safety checks."""
    target = (WORKSPACE_ROOT / path).resolve()
    if not str(target).startswith(str(WORKSPACE_ROOT)):
        return {"error": "Path traversal denied"}

    if not target.is_file():
        return {"error": "Not a file"}

    if target.stat().st_size > MAX_FILE_SIZE:
        return {"error": "File too large", "size": target.stat().st_size}

    ext = target.suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return {"type": "image", "path": str(target.relative_to(WORKSPACE_ROOT)), "extension": ext}

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        return {
            "type": "text",
            "content": content,
            "path": str(target.relative_to(WORKSPACE_ROOT)),
            "extension": ext,
            "size": len(content),
        }
    except Exception as exc:
        return {"error": f"Cannot read file: {exc}"}


def _scan_directory(path: Path, depth: int, current_depth: int) -> list[dict[str, Any]]:
    """Recursively scan directory up to specified depth."""
    if current_depth >= depth:
        return []

    nodes: list[dict[str, Any]] = []
    try:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        for entry in entries:
            if entry.name.startswith(".") or entry.name == "__pycache__":
                continue
            if entry.name == "node_modules" or entry.name == ".git":
                continue

            node: dict[str, Any] = {
                "name": entry.name,
                "path": str(entry.relative_to(WORKSPACE_ROOT)),
                "is_dir": entry.is_dir(),
            }

            if entry.is_dir():
                if current_depth + 1 < depth:
                    node["children"] = _scan_directory(entry, depth, current_depth + 1)
            else:
                node["size"] = entry.stat().st_size
                node["extension"] = entry.suffix.lower()

            nodes.append(node)
    except PermissionError:
        pass

    return nodes


# ─── Terminal ─────────────────────────────────────────────────────────────────


@router.post("/terminal")
async def execute_terminal(request: TerminalRequest) -> StreamingResponse:
    """Execute a terminal command and stream output via SSE."""
    cwd = request.cwd or str(WORKSPACE_ROOT)
    target_cwd = Path(cwd).resolve()

    # Security: ensure cwd is within workspace
    if not str(target_cwd).startswith(str(WORKSPACE_ROOT)):

        async def denied():
            yield f"data: {json.dumps({'type': 'error', 'content': 'Access denied'})}\n\n"

        return StreamingResponse(denied(), media_type="text/event-stream")

    async def stream_output():
        try:
            proc = await asyncio.create_subprocess_shell(
                request.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(target_cwd),
            )

            async def read_stream(stream: asyncio.StreamReader, stream_type: str):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    text = line.decode("utf-8", errors="replace")
                    data = json.dumps({"type": stream_type, "content": text})
                    yield f"data: {data}\n\n"

            assert proc.stdout is not None
            assert proc.stderr is not None

            # Read stdout and stderr
            stdout_data = await asyncio.wait_for(proc.stdout.read(), timeout=request.timeout)
            stderr_data = await asyncio.wait_for(proc.stderr.read(), timeout=request.timeout)

            if stdout_data:
                text = stdout_data.decode("utf-8", errors="replace")
                yield f"data: {json.dumps({'type': 'stdout', 'content': text})}\n\n"
            if stderr_data:
                text = stderr_data.decode("utf-8", errors="replace")
                yield f"data: {json.dumps({'type': 'stderr', 'content': text})}\n\n"

            await proc.wait()
            yield f"data: {json.dumps({'type': 'exit', 'code': proc.returncode})}\n\n"

        except TimeoutError:
            yield f"data: {json.dumps({'type': 'error', 'content': 'Command timed out'})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"

    return StreamingResponse(stream_output(), media_type="text/event-stream")


# ─── Memory ───────────────────────────────────────────────────────────────────


@router.get("/memory")
async def list_memories(
    memory_type: str = Query("", description="Filter by type"),
    query: str = Query("", description="Search query"),
    limit: int = Query(50, description="Max results"),
) -> dict[str, Any]:
    """List or search memory entries."""
    from memory.default_manager import DefaultMemoryManager

    manager = DefaultMemoryManager()
    if query:
        results = await manager.search(query, memory_type=memory_type or None, limit=limit)
        return {
            "memories": [
                {"id": m.entry_id, "content": m.content, "type": m.memory_type} for m in results
            ],
            "count": len(results),
            "query": query,
        }
    # Without query, search with empty string returns recent
    results = await manager.search("", memory_type=memory_type or None, limit=limit)
    return {
        "memories": [
            {"id": m.entry_id, "content": m.content, "type": m.memory_type} for m in results
        ],
        "count": len(results),
    }


@router.post("/memory")
async def store_memory(entry: MemoryEntry) -> dict[str, Any]:
    """Store a new memory entry."""
    from memory.default_manager import DefaultMemoryManager
    from memory.default_manager import MemoryEntry as MemEntry

    manager = DefaultMemoryManager()
    mem_entry = MemEntry(
        content=entry.content,
        memory_type=entry.memory_type,
        importance=entry.importance,
        tags=entry.tags,
    )
    memory_id = await manager.store(mem_entry)
    return {"memory_id": memory_id, "stored": True}


@router.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str) -> dict[str, Any]:
    """Delete a memory entry."""
    from memory.default_manager import DefaultMemoryManager

    manager = DefaultMemoryManager()
    deleted = await manager.delete(memory_id)
    return {"deleted": deleted, "memory_id": memory_id}


# ─── Conversations ────────────────────────────────────────────────────────────

_conversations: dict[str, dict[str, Any]] = {}


@router.get("/conversations")
async def list_conversations() -> dict[str, Any]:
    """List all conversations."""
    summaries = [
        {
            "id": cid,
            "title": conv.get("title", "Untitled"),
            "created_at": conv.get("created_at", ""),
            "message_count": len(conv.get("messages", [])),
            "pinned": conv.get("pinned", False),
        }
        for cid, conv in _conversations.items()
    ]
    summaries.sort(key=lambda c: c.get("pinned", False), reverse=True)
    return {"conversations": summaries, "count": len(summaries)}


@router.post("/conversations")
async def create_conversation(title: str = "") -> dict[str, Any]:
    """Create a new conversation."""
    import uuid

    conv_id = str(uuid.uuid4())
    _conversations[conv_id] = {
        "title": title or "New Chat",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "messages": [],
        "pinned": False,
    }
    return {"id": conv_id, "title": _conversations[conv_id]["title"]}


@router.patch("/conversations/{conv_id}")
async def update_conversation(conv_id: str, title: str = "", pinned: bool | None = None) -> dict:
    """Update conversation metadata."""
    if conv_id not in _conversations:
        return {"error": "Not found"}
    if title:
        _conversations[conv_id]["title"] = title
    if pinned is not None:
        _conversations[conv_id]["pinned"] = pinned
    return {"updated": True, "id": conv_id}


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str) -> dict[str, Any]:
    """Delete a conversation."""
    if conv_id in _conversations:
        del _conversations[conv_id]
        return {"deleted": True}
    return {"deleted": False, "error": "Not found"}


# ─── Settings ─────────────────────────────────────────────────────────────────

_workspace_settings: dict[str, Any] = {
    "provider": "ollama",
    "model": "llama3",
    "theme": "dark",
    "temperature": 0.7,
    "max_tokens": 4096,
    "research_depth": "standard",
}


@router.get("/settings")
async def get_settings() -> dict[str, Any]:
    """Get current workspace settings."""
    return _workspace_settings


@router.patch("/settings")
async def update_settings(settings: SettingsUpdate) -> dict[str, Any]:
    """Update workspace settings."""
    if settings.provider:
        _workspace_settings["provider"] = settings.provider
    if settings.model:
        _workspace_settings["model"] = settings.model
    if settings.theme:
        _workspace_settings["theme"] = settings.theme
    if settings.temperature is not None:
        _workspace_settings["temperature"] = settings.temperature
    if settings.max_tokens is not None:
        _workspace_settings["max_tokens"] = settings.max_tokens
    if settings.research_depth:
        _workspace_settings["research_depth"] = settings.research_depth
    return {"updated": True, "settings": _workspace_settings}


# ─── Research ─────────────────────────────────────────────────────────────────


@router.post("/research")
async def workspace_research(query: str, offline: bool = False) -> StreamingResponse:
    """Run deep research with streaming progress."""
    from research_engine.engine import DeepResearchEngine

    engine = DeepResearchEngine()

    async def stream_research():
        yield f"data: {json.dumps({'type': 'status', 'content': 'Planning research...'})}\n\n"

        try:
            report = await engine.research(query, offline=offline)
            yield f"data: {json.dumps({'type': 'status', 'content': 'Research complete'})}\n\n"

            # Stream the report
            report_data = {
                "type": "report",
                "title": report.query,
                "summary": report.executive_summary,
                "confidence": report.confidence_score,
                "source_count": len(report.references),
                "references": [
                    {
                        "title": ref.title,
                        "url": ref.url or "",
                        "snippet": ref.text[:200],
                        "source_kind": ref.source_kind.value,
                    }
                    for ref in report.references[:20]
                ],
            }
            yield f"data: {json.dumps(report_data)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"

    return StreamingResponse(stream_research(), media_type="text/event-stream")
