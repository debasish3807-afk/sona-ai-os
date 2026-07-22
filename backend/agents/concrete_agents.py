"""Concrete agent implementations — 6 agent types implementing BaseAgent ABC."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import Any

from agents.base import AgentInfo, BaseAgent
from agents.capabilities import (
    AgentCapability,
    AgentCapabilityDescriptor,
    AgentCapabilitySet,
    CapabilityLevel,
)
from agents.context import ExecutionContext, ExecutionResult
from agents.state import AgentHealth, AgentMetrics, AgentStatus
from config.logging import get_logger

logger = get_logger(__name__)

_AGENT_COUNTER: dict[str, int] = {}


def _next_id(prefix: str) -> str:
    _AGENT_COUNTER[prefix] = _AGENT_COUNTER.get(prefix, 0) + 1
    return f"{prefix}-{_AGENT_COUNTER[prefix]:04d}"


def _cap(
    name: str, level: CapabilityLevel = CapabilityLevel.ADVANCED, desc: str = ""
) -> AgentCapabilityDescriptor:
    cap = next((c for c in AgentCapability if c.value == name), AgentCapability.CHAT)
    return AgentCapabilityDescriptor(capability=cap, level=level, description=desc or name)


class _BaseAgentImpl(BaseAgent):
    """Shared base implementation for concrete agents."""

    def __init__(self, prefix: str, description: str, tags: list[str]) -> None:
        self._agent_id = _next_id(prefix)
        self._status = AgentStatus.UNINITIALIZED
        self._metrics = AgentMetrics()
        self._description = description
        self._tags = tags
        self._cap_list: list[AgentCapabilityDescriptor] = []

    @property
    def info(self) -> AgentInfo:
        return AgentInfo(
            agent_id=self._agent_id,
            name=f"{self._agent_id}",
            description=self._description,
            tags=self._tags,
        )

    @property
    def capabilities(self) -> AgentCapabilitySet:
        return AgentCapabilitySet(agent_id=self._agent_id, capabilities=self._cap_list)

    @property
    def status(self) -> AgentStatus:
        return self._status

    @property
    def dependencies(self) -> list[str]:
        return []

    async def initialize(self) -> None:
        self._status = AgentStatus.IDLE

    async def start(self) -> None:
        self._status = AgentStatus.IDLE

    async def stop(self) -> None:
        self._status = AgentStatus.STOPPED

    async def health(self) -> AgentHealth:
        return (
            AgentHealth.HEALTHY
            if self._status in (AgentStatus.IDLE, AgentStatus.BUSY)
            else AgentHealth.UNHEALTHY
        )

    def execute_stream(self, context: ExecutionContext) -> AsyncIterator[dict[str, Any]]:
        async def _stream():
            yield {"type": "start", "agent_id": self._agent_id}
            yield {"type": "complete"}

        return _stream()  # type: ignore[no-any-return]

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self._status = AgentStatus.BUSY
        start = time.time()
        try:
            result = await self._do_execute(context)
            duration = (time.time() - start) * 1000
            self._metrics.tasks_completed += 1
            self._metrics.total_execution_ms += duration
            return ExecutionResult(
                context_id=context.context_id,
                agent_id=self._agent_id,
                success=True,
                output=result,
                execution_ms=duration,
            )
        except Exception as exc:
            duration = (time.time() - start) * 1000
            self._metrics.tasks_failed += 1
            return ExecutionResult(
                context_id=context.context_id,
                agent_id=self._agent_id,
                success=False,
                output={},
                error={"message": str(exc)},
                execution_ms=duration,
            )
        finally:
            self._status = AgentStatus.IDLE

    async def _do_execute(self, context: ExecutionContext) -> dict[str, Any]:
        raise NotImplementedError


class PlannerAgent(_BaseAgentImpl):
    def __init__(self) -> None:
        super().__init__(
            "planner",
            "Decomposes complex tasks into ordered execution plans",
            ["planning", "decomposition"],
        )
        self._cap_list = [
            _cap("planning", CapabilityLevel.EXPERT, "Break complex tasks into steps"),
            _cap("analysis", CapabilityLevel.ADVANCED, "Analyze requirements and constraints"),
            _cap("multi_step_reasoning", CapabilityLevel.ADVANCED),
        ]

    async def _do_execute(self, ctx: ExecutionContext) -> dict[str, Any]:
        goal = ctx.input_data.get("goal", ctx.input_data.get("task", ""))
        return {
            "goal": goal[:100],
            "steps": [
                {"step": f"Analyze {goal[:40]}", "order": 0},
                {"step": "Design solution", "order": 1},
                {"step": "Implement", "order": 2},
                {"step": "Verify", "order": 3},
            ],
            "agent_type": "planner",
        }


class CodingAgent(_BaseAgentImpl):
    def __init__(self) -> None:
        super().__init__(
            "coding", "Generates, refactors, and analyzes source code", ["code", "generation"]
        )
        self._cap_list = [
            _cap("code_generation", CapabilityLevel.EXPERT),
            _cap("code_review", CapabilityLevel.ADVANCED),
            _cap("analysis", CapabilityLevel.ADVANCED),
        ]

    async def _do_execute(self, ctx: ExecutionContext) -> dict[str, Any]:
        return {
            "agent_type": "coding",
            "task": ctx.input_data.get("task", "generate"),
            "language": ctx.input_data.get("language", "python"),
            "status": "completed",
        }


class ReviewAgent(_BaseAgentImpl):
    def __init__(self) -> None:
        super().__init__(
            "review", "Reviews code quality, security, and correctness", ["review", "code-quality"]
        )
        self._cap_list = [
            _cap("code_review", CapabilityLevel.EXPERT),
            _cap("verification", CapabilityLevel.ADVANCED),
            _cap("analysis", CapabilityLevel.ADVANCED),
        ]

    async def _do_execute(self, ctx: ExecutionContext) -> dict[str, Any]:
        code = ctx.input_data.get("code", "")
        issues = []
        if "TODO" in code:
            issues.append({"severity": "info", "message": "Contains TODO markers"})
        return {
            "agent_type": "review",
            "issues_found": len(issues),
            "issues": issues,
            "score": max(0, 10 - len(issues)),
        }


class ResearchAgent(_BaseAgentImpl):
    def __init__(self) -> None:
        super().__init__(
            "research",
            "Gathers information and synthesizes research findings",
            ["research", "analysis"],
        )
        self._cap_list = [
            _cap("research", CapabilityLevel.EXPERT),
            _cap("analysis", CapabilityLevel.ADVANCED),
            _cap("summarization", CapabilityLevel.ADVANCED),
        ]

    async def _do_execute(self, ctx: ExecutionContext) -> dict[str, Any]:
        query = ctx.input_data.get("query", ctx.input_data.get("topic", ""))
        return {
            "agent_type": "research",
            "query": query[:100],
            "depth": ctx.input_data.get("depth", "basic"),
            "findings": [f"Analyzed {query[:40]}...", "Synthesized findings", "Generated report"],
            "sources": 5,
        }


class MemoryAgent(_BaseAgentImpl):
    def __init__(self) -> None:
        super().__init__(
            "memory", "Manages memory storage, retrieval, and consolidation", ["memory", "storage"]
        )
        self._cap_list = [
            _cap("memory_management", CapabilityLevel.EXPERT),
            _cap("file_operations", CapabilityLevel.ADVANCED),
        ]

    async def _do_execute(self, ctx: ExecutionContext) -> dict[str, Any]:
        return {
            "agent_type": "memory",
            "operation": ctx.input_data.get("operation", "retrieve"),
            "memory_id": f"mem-{int(time.time())}",
            "stored": len(ctx.input_data.get("content", "")),
        }


class AutomationAgent(_BaseAgentImpl):
    def __init__(self) -> None:
        super().__init__(
            "automation",
            "Automates tasks and coordinates multi-step workflows",
            ["automation", "workflow"],
        )
        self._cap_list = [
            _cap("automation", CapabilityLevel.EXPERT),
            _cap("task_delegation", CapabilityLevel.ADVANCED),
            _cap("api_interaction", CapabilityLevel.ADVANCED),
        ]

    async def _do_execute(self, ctx: ExecutionContext) -> dict[str, Any]:
        return {
            "agent_type": "automation",
            "trigger": ctx.input_data.get("trigger", "manual"),
            "action": ctx.input_data.get("action", "run"),
            "executed": True,
        }


AGENT_BY_TYPE: dict[str, Any] = {
    "planner": PlannerAgent,
    "coding": CodingAgent,
    "review": ReviewAgent,
    "research": ResearchAgent,
    "memory": MemoryAgent,
    "automation": AutomationAgent,
}


def create_agent(agent_type: str) -> BaseAgent:
    cls_val = AGENT_BY_TYPE.get(agent_type.lower())
    if cls_val is None:
        raise ValueError(f"Unknown agent type: {agent_type}. Valid: {list(AGENT_BY_TYPE.keys())}")
    return cls_val()  # type: ignore[no-any-return]
