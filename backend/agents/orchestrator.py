"""Agent orchestrator — bridges concrete agents with coordinator, executor, and task queue."""

from __future__ import annotations

from typing import Any

from agents.agent_coordinator import AgentCoordinator
from agents.agent_executor import AgentExecutor
from agents.agent_factory import AgentFactory
from agents.agent_lifecycle import AgentLifecycle
from agents.agent_manager import AgentManager
from agents.agent_negotiator import AgentNegotiator
from agents.agent_registry import AgentRegistry as ConcreteAgentRegistry
from agents.agent_scheduler import AgentScheduler
from agents.agent_supervisor import AgentSupervisor
from agents.concrete_agents import AGENT_BY_TYPE
from agents.messaging import AgentMessage, MessageBus
from agents.schemas import (
    Agent,
    AgentType,
)
from agents.task_queue import TaskQueue
from config.logging import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    """Central orchestrator for the multi-agent system."""

    def __init__(self) -> None:
        self._lifecycle = AgentLifecycle()
        self._agent_registry = ConcreteAgentRegistry()
        self._factory = AgentFactory()
        self._scheduler = AgentScheduler()
        self._negotiator = AgentNegotiator()
        self._supervisor = AgentSupervisor()
        self._executor = AgentExecutor(self._lifecycle)
        self._coordinator = AgentCoordinator(
            registry=self._agent_registry,
            scheduler=self._scheduler,
            negotiator=self._negotiator,
        )
        self._manager = AgentManager(
            registry=self._agent_registry,
            factory=self._factory,
            coordinator=self._coordinator,
            executor=self._executor,
            supervisor=self._supervisor,
        )
        self._task_queue = TaskQueue()
        self._message_bus = MessageBus()
        self._initialized = False

    @property
    def task_queue(self) -> TaskQueue:
        return self._task_queue

    @property
    def message_bus(self) -> MessageBus:
        return self._message_bus

    async def initialize(self) -> None:
        """Initialize orchestrator and create default agents."""
        if self._initialized:
            return
        for agent_type_str, agent_cls in AGENT_BY_TYPE.items():
            agent_instance = agent_cls()
            await agent_instance.initialize()
            await agent_instance.start()
            self._agent_registry.register(Agent(name=agent_type_str, agent_type=AgentType.CUSTOM))
        self._initialized = True
        logger.info("orchestrator_initialized")

    async def create_agent(self, name: str, agent_type_str: str) -> Agent:
        agent_type = AgentType(agent_type_str)
        return await self._manager.create_agent(name, agent_type)

    async def submit_task(
        self,
        agent_type: str,
        description: str,
        payload: dict[str, Any] | None = None,
        priority: int = 50,
    ) -> str:
        return self._task_queue.enqueue(agent_type, description, payload, priority)

    async def execute_next(self) -> dict[str, Any] | None:
        task = self._task_queue.dequeue()
        if task is None:
            return None
        self._task_queue.assign(task.task_id, task.agent_type)
        self._task_queue.complete(
            task.task_id, {"status": "completed", "agent_type": task.agent_type}
        )
        return {"task_id": task.task_id, "status": "completed", "agent_type": task.agent_type}

    async def get_agents(self) -> list[dict[str, Any]]:
        agents_out: list[dict[str, Any]] = []
        agents = self._agent_registry.list_all()
        for a in agents:
            if a is not None:
                agents_out.append(
                    {
                        "agent_id": a.agent_id,
                        "name": a.name,
                        "type": a.agent_type.value
                        if hasattr(a.agent_type, "value")
                        else str(a.agent_type),
                        "state": a.state.value if hasattr(a.state, "value") else str(a.state),
                    }
                )
        return agents_out

    async def get_stats(self) -> dict[str, Any]:
        return {
            "agents": len(self._agent_registry.list_all()),
            "tasks": self._task_queue.get_stats(),
            "messages": self._message_bus.get_stats(),
        }

    async def send_message(self, sender: str, recipient: str, payload: dict[str, Any]) -> str:
        msg = AgentMessage(sender_id=sender, recipient_id=recipient, payload=payload)
        return await self._message_bus.send(msg)

    async def shutdown(self) -> None:
        self._initialized = False
