"""Multi-Agent Coordination & Autonomous Execution Fabric."""

from __future__ import annotations

from agents.agent_coordinator import AgentCoordinator
from agents.agent_executor import AgentExecutor
from agents.agent_factory import AgentFactory
from agents.agent_manager import AgentManager
from agents.agent_registry import AgentRegistry
from agents.concrete_agents import (
    AGENT_BY_TYPE,
    AutomationAgent,
    CodingAgent,
    MemoryAgent,
    PlannerAgent,
    ResearchAgent,
    ReviewAgent,
    create_agent,
)
from agents.messaging import AgentMessage, MessageBus, MessageType
from agents.orchestrator import AgentOrchestrator
from agents.task_queue import TaskQueue, TaskStatus

__all__ = [
    "AgentCoordinator",
    "AgentExecutor",
    "AgentFactory",
    "AgentManager",
    "AgentRegistry",
    "AgentOrchestrator",
    "TaskQueue",
    "TaskStatus",
    "MessageBus",
    "AgentMessage",
    "MessageType",
    "PlannerAgent",
    "CodingAgent",
    "ReviewAgent",
    "ResearchAgent",
    "MemoryAgent",
    "AutomationAgent",
    "AGENT_BY_TYPE",
    "create_agent",
]
