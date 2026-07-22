"""Automation actions — execute individual steps.

Provides secure execution of automation action types with
input validation, SSRF protection, and path traversal guards.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx

from automation.schemas import ActionStep, ActionType
from config.logging import get_logger

logger = get_logger(__name__)

# ─── Constants ───────────────────────────────────────────────────────────────

_WORKSPACE_ROOT = Path(os.environ.get("SONA_WORKSPACE", ".")).resolve()
_DEFAULT_WORKSPACE = str(_WORKSPACE_ROOT)

_PRIVATE_IP_PREFIXES = (
    "127.",
    "10.",
    "172.16.",
    "172.17.",
    "172.18.",
    "172.19.",
    "172.20.",
    "172.21.",
    "172.22.",
    "172.23.",
    "172.24.",
    "172.25.",
    "172.26.",
    "172.27.",
    "172.28.",
    "172.29.",
    "172.30.",
    "172.31.",
    "192.168.",
)
_CLOUD_METADATA_HOSTS = {
    "169.254.169.254",  # AWS / GCP / Azure metadata
    "metadata.google.internal",
    "metadata.internal",
    "100.100.100.200",  # Alibaba Cloud
}
_LOCAL_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",  # nosec B104 — used for SSRF protection
    "::1",
    "127.0.1.1",
}

_COMMAND_ALLOWLIST = [
    "ls",
    "cat",
    "head",
    "tail",
    "grep",
    "find",
    "wc",
    "echo",
    "pwd",
    "python",
    "python3",
    "pip",
    "node",
    "npm",
    "npx",
    "curl",
    "wget",
    "jq",
    "sed",
    "awk",
    "sort",
    "uniq",
    "diff",
    "mkdir",
    "cp",
    "mv",
    "rm",
    "touch",
    "chmod",
    "git",
    "make",
    "docker",
    "docker-compose",
    "ruff",
    "mypy",
    "pytest",
    "black",
    "isort",
]

# ─── Validation Helpers ──────────────────────────────────────────────────────


def _is_command_allowed(command: str) -> bool:
    """Check if a shell command's base executable is allowed."""
    if not command or not command.strip():
        return False
    base_cmd = command.strip().split()[0]
    return base_cmd in _COMMAND_ALLOWLIST


def _is_safe_url(url: str) -> bool:
    """Check that a URL does not point to an internal or private network.

    Prevents SSRF attacks by blocking private IP ranges, localhost,
    and cloud metadata endpoints.
    """
    from urllib.parse import urlparse

    if not url:
        return False

    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    # Block empty hostnames
    if not hostname:
        return False

    # Block localhost variants
    if hostname.lower() in _LOCAL_HOSTNAMES:
        return False

    # Block cloud metadata hosts
    if hostname.lower() in _CLOUD_METADATA_HOSTS:
        return False

    # Block private IP ranges by prefix
    if hostname.startswith(_PRIVATE_IP_PREFIXES):
        return False

    return True


def _is_safe_file_path(path: str) -> Path:
    """Validate a file path is safe and within the workspace.

    Args:
        path: The file path to validate.

    Returns:
        Resolved Path object.

    Raises:
        ValueError: If path escapes workspace or contains traversals.
    """
    p = Path(path)

    # Block path traversal components
    if ".." in p.parts:
        raise ValueError(f"Path traversal denied: {path}")

    resolved = p.resolve()
    try:
        resolved.relative_to(_WORKSPACE_ROOT)
        return resolved
    except ValueError:
        raise ValueError(f"Path outside workspace: {path}") from None


# ─── Action Executor ─────────────────────────────────────────────────────────


async def execute_action(step: ActionStep, context: dict[str, Any]) -> dict[str, Any]:
    """Execute a single automation action. Returns result dict."""
    action_map = {
        ActionType.AI_CHAT: _action_ai_chat,
        ActionType.DEEP_RESEARCH: _action_research,
        ActionType.OCR: _action_ocr,
        ActionType.MEMORY_STORE: _action_memory,
        ActionType.FILE_CREATE: _action_file_create,
        ActionType.FILE_READ: _action_file_read,
        ActionType.FILE_WRITE: _action_file_write,
        ActionType.TERMINAL: _action_terminal,
        ActionType.GITHUB: _action_github,
        ActionType.HTTP_REQUEST: _action_http,
        ActionType.NOTIFICATION: _action_notify,
    }

    handler = action_map.get(step.action_type)
    if handler is None:
        return {"error": f"Unknown action: {step.action_type}"}

    try:
        return await handler(step.params, context)
    except Exception as exc:
        logger.error("action_failed", action=step.action_type.value, error=str(exc))
        return {"error": str(exc)}


# ─── Action Implementations ──────────────────────────────────────────────────


async def _action_ai_chat(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    from ai.ollama_provider import OllamaProvider
    from ai.schemas import AIMessage, AIRequest

    provider = OllamaProvider()
    messages = [AIMessage(role="user", content=params.get("message", ""))]
    req = AIRequest(messages=messages, model=params.get("model", ""))
    resp = await provider.complete(req)
    return {"content": resp.content, "model": resp.model}


async def _action_research(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    from research_engine.engine import DeepResearchEngine

    engine = DeepResearchEngine()
    report = await engine.research(params.get("query", ""), offline=params.get("offline", False))
    return {"summary": report.executive_summary, "confidence": report.confidence_score}


async def _action_ocr(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    import base64

    from vision.engine import VisionEngine

    engine = VisionEngine()
    data = base64.b64decode(params.get("image_base64", ""))
    result = engine.ocr_from_bytes(data, params.get("filename", "image.png"))
    return {"text": result.text, "confidence": result.confidence}


async def _action_memory(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    from memory.default_manager import DefaultMemoryManager, MemoryEntry

    mgr = DefaultMemoryManager()
    entry = MemoryEntry(
        content=params.get("content", ""), memory_type=params.get("type", "conversation")
    )
    mid = await mgr.store(entry)
    return {"memory_id": mid}


async def _action_file_create(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    path = _is_safe_file_path(params.get("path", ""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(params.get("content", ""), encoding="utf-8")
    return {"created": str(path)}


async def _action_file_read(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    path = _is_safe_file_path(params.get("path", ""))
    if not path.exists():
        return {"error": "File not found"}
    return {"content": path.read_text(encoding="utf-8", errors="replace")[:10000]}


async def _action_file_write(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    path = _is_safe_file_path(params.get("path", ""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(params.get("content", ""), encoding="utf-8")
    return {"written": str(path), "size": len(params.get("content", ""))}


async def _action_terminal(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    import asyncio

    cmd = params.get("command", "echo hello")

    # Validate the command against allowlist
    if not _is_command_allowed(cmd):
        return {"error": f"Command '{cmd.split()[0] if cmd.strip() else ''}' is not allowed"}

    timeout = params.get("timeout", 30)
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return {
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "exit_code": proc.returncode,
        }
    except TimeoutError:
        proc.kill()
        return {"error": "Command timed out"}


async def _action_github(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    url = f"https://api.github.com/search/repositories?q={params.get('query', '')}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])[:5]
            return {
                "results": [{"name": i["full_name"], "stars": i["stargazers_count"]} for i in items]
            }
    return {"error": "GitHub search failed"}


async def _action_http(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    method = params.get("method", "GET").upper()
    url = params.get("url", "")
    if not url:
        return {"error": "No URL provided"}

    # SSRF protection — block private/internal hosts
    if not _is_safe_url(url):
        logger.warning("ssrf_blocked_url", url=url)
        return {"error": "URL blocked: requests to private/internal networks are not allowed"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(method, url, json=params.get("body"))
        return {"status": resp.status_code, "body": resp.text[:5000]}


async def _action_notify(params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    message = params.get("message", "Automation complete")
    logger.info("automation_notification", message=message)
    return {"notified": True, "message": message}
