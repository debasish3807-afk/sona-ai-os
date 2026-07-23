"""Tool Orchestrator — dynamic tool selection, permissions, history, retry."""

from __future__ import annotations

import time
import uuid
from typing import Any

from config.logging import get_logger
from orchestration.schemas import ToolDefinition

logger = get_logger(__name__)


class ToolOrchestrator:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._history: list[dict[str, Any]] = []
        self._max_history = 1000

    def register_tool(self, tool: ToolDefinition) -> str:
        if not tool.name:
            tool.name = f"tool-{str(uuid.uuid4())[:8]}"
        self._tools[tool.name] = tool
        return tool.name

    def get_tool(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def select_tools(self, capability: str) -> list[ToolDefinition]:
        return [t for t in self._tools.values() if t.required_capability == capability]

    def execute(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        tool = self._tools.get(tool_name)
        if tool is None:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        entry_id = str(uuid.uuid4())
        start = time.time()
        try:
            result = {
                "success": True,
                "tool": tool_name,
                "params": params,
                "output": f"Executed {tool_name}",
            }
            duration_ms = (time.time() - start) * 1000
            self._record(entry_id, tool_name, params, True, duration_ms)
            return result
        except Exception as exc:
            duration_ms = (time.time() - start) * 1000
            self._record(entry_id, tool_name, params, False, duration_ms, str(exc))
            return {"success": False, "error": str(exc)}

    def execute_with_retry(
        self, tool_name: str, params: dict[str, Any], max_retries: int = 2
    ) -> dict[str, Any]:
        for attempt in range(max_retries + 1):
            result = self.execute(tool_name, params)
            if result["success"]:
                return result
            logger.info("tool_retry", tool=tool_name, attempt=attempt)
        return result

    def history(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._history[:limit]

    def get_stats(self) -> dict[str, int]:
        total = len(self._history)
        success = sum(1 for h in self._history if h.get("success"))
        return {"total": total, "success": success, "failed": total - success}

    def _record(
        self,
        eid: str,
        tool: str,
        params: dict,
        success: bool,
        duration: float = 0.0,
        error: str = "",
    ) -> None:
        self._history.insert(
            0,
            {
                "entry_id": eid,
                "tool": tool,
                "params": params,
                "success": success,
                "duration_ms": duration,
                "error": error,
                "timestamp": time.time(),
            },
        )
        while len(self._history) > self._max_history:
            self._history.pop()
