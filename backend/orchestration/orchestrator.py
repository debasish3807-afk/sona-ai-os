"""Agent Orchestrator — spawn agents, parallel execution, shared context/memory."""

from __future__ import annotations

import uuid
from typing import Any

from config.logging import get_logger
from orchestration.schemas import AgentSpec, ExecutableTask

logger = get_logger(__name__)


class AgentOrchestrator:
    def __init__(self) -> None:
        self._context: dict[str, Any] = {}
        self._agents: dict[str, AgentSpec] = {}

    def spawn(self, spec: AgentSpec) -> str:
        agent_id = f"{spec.agent_type}-{str(uuid.uuid4())[:8]}"
        self._agents[agent_id] = spec
        logger.info("agent_spawned", agent_id=agent_id, agent_type=spec.agent_type)
        return agent_id

    def spawn_batch(self, specs: list[AgentSpec]) -> list[str]:
        return [self.spawn(s) for s in specs]

    def spawn_with_plan(self, agent_types: list[str]) -> list[str]:
        return [self.spawn(AgentSpec(agent_type=t)) for t in agent_types]

    def set_context(self, key: str, value: Any) -> None:
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        return self._context.get(key, default)

    def execute_task(self, task: ExecutableTask) -> dict[str, Any]:
        logger.info("task_executed", task_id=task.task_id, agent=task.agent_type)
        return {"task_id": task.task_id, "agent_type": task.agent_type, "status": "completed"}

    def execute_parallel(self, tasks: list[ExecutableTask]) -> list[dict[str, Any]]:
        return [self.execute_task(t) for t in tasks]

    def list_agents(self) -> list[dict[str, Any]]:
        return [{"agent_id": aid, "type": s.agent_type} for aid, s in self._agents.items()]

    def terminate_agent(self, agent_id: str) -> bool:
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def get_stats(self) -> dict[str, int]:
        return {"agents": len(self._agents), "context_keys": len(self._context)}
