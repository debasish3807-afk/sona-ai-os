"""Multi-Agent Framework for Sona AI OS.

Provides a production-ready multi-agent system with:
- Agent lifecycle management
- Task routing and execution
- Inter-agent communication
- Multi-agent coordination
- Workflow engine
- Plugin architecture for custom agents
"""

from agents.base import AgentInfo, BaseAgent
from agents.capabilities import (
    AgentCapability,
    AgentCapabilityDescriptor,
    AgentCapabilitySet,
    CapabilityLevel,
    CapabilityRequirement,
)
from agents.communication import (
    AgentMessage,
    MessageBus,
    MessagePriority,
    MessageType,
)
from agents.context import (
    AgentTool,
    ExecutionContext,
    ExecutionResult,
)
from agents.coordinator import (
    AgentCoordinator,
    CoordinationMode,
    CoordinationPlan,
    DelegationRequest,
    DelegationResult,
    DelegationStatus,
)
from agents.events import AgentEvent, AgentEvents
from agents.exceptions import (
    AgentCapabilityError,
    AgentCommunicationError,
    AgentDependencyError,
    AgentError,
    AgentExecutionError,
    AgentInitializationError,
    AgentNotFoundError,
    AgentTimeoutError,
    CoordinationError,
    WorkflowError,
)
from agents.executor import (
    AgentExecutor,
    ExecutionJob,
    ExecutionPriority,
    ExecutionStatus,
)
from agents.factory import AgentFactory
from agents.lifecycle import (
    AgentLifecycleManager,
    DependencyNode,
    LifecycleResult,
)
from agents.manager import AgentManager, AgentManagerConfig
from agents.planner import (
    ExecutionPlan,
    PlanStatus,
    PlanStep,
    StepType,
    TaskPlanner,
)
from agents.registry import AgentEntry, AgentRegistry
from agents.router import (
    AgentRouter,
    RouteDecision,
    RouteOutcome,
    RouteRule,
    RouteStrategy,
)
from agents.state import (
    AgentHealth,
    AgentMetrics,
    AgentState,
    AgentStateManager,
    AgentStatus,
)
from agents.verifier import (
    ResultVerifier,
    VerificationCheck,
    VerificationReport,
    VerificationStatus,
    VerificationType,
)
from agents.workflow import (
    StepStatus,
    WorkflowDefinition,
    WorkflowEngine,
    WorkflowExecution,
    WorkflowStatus,
    WorkflowStep,
)

# Agent implementations
from agents.general_agent import GeneralAgent
from agents.coding_agent import CodingAgent
from agents.research_agent import ResearchAgent
from agents.memory_agent import MemoryAgent
from agents.planner_agent import PlannerAgent
from agents.automation_agent import AutomationAgent
from agents.security_agent import SecurityAgent
from agents.android_agent import AndroidAgent
from agents.web_agent import WebAgent
from agents.vision_agent import VisionAgent
from agents.voice_agent import VoiceAgent

__all__ = [
    # Base
    "AgentInfo",
    "BaseAgent",
    # Capabilities
    "AgentCapability",
    "AgentCapabilityDescriptor",
    "AgentCapabilitySet",
    "CapabilityLevel",
    "CapabilityRequirement",
    # Communication
    "AgentMessage",
    "MessageBus",
    "MessagePriority",
    "MessageType",
    # Context
    "AgentTool",
    "ExecutionContext",
    "ExecutionResult",
    # Coordinator
    "AgentCoordinator",
    "CoordinationMode",
    "CoordinationPlan",
    "DelegationRequest",
    "DelegationResult",
    "DelegationStatus",
    # Events
    "AgentEvent",
    "AgentEvents",
    # Exceptions
    "AgentCapabilityError",
    "AgentCommunicationError",
    "AgentDependencyError",
    "AgentError",
    "AgentExecutionError",
    "AgentInitializationError",
    "AgentNotFoundError",
    "AgentTimeoutError",
    "CoordinationError",
    "WorkflowError",
    # Executor
    "AgentExecutor",
    "ExecutionJob",
    "ExecutionPriority",
    "ExecutionStatus",
    # Factory
    "AgentFactory",
    # Lifecycle
    "AgentLifecycleManager",
    "DependencyNode",
    "LifecycleResult",
    # Manager
    "AgentManager",
    "AgentManagerConfig",
    # Planner
    "ExecutionPlan",
    "PlanStatus",
    "PlanStep",
    "StepType",
    "TaskPlanner",
    # Registry
    "AgentEntry",
    "AgentRegistry",
    # Router
    "AgentRouter",
    "RouteDecision",
    "RouteOutcome",
    "RouteRule",
    "RouteStrategy",
    # State
    "AgentHealth",
    "AgentMetrics",
    "AgentState",
    "AgentStateManager",
    "AgentStatus",
    # Verifier
    "ResultVerifier",
    "VerificationCheck",
    "VerificationReport",
    "VerificationStatus",
    "VerificationType",
    # Workflow
    "StepStatus",
    "WorkflowDefinition",
    "WorkflowEngine",
    "WorkflowExecution",
    "WorkflowStatus",
    "WorkflowStep",
    # Agents
    "GeneralAgent",
    "CodingAgent",
    "ResearchAgent",
    "MemoryAgent",
    "PlannerAgent",
    "AutomationAgent",
    "SecurityAgent",
    "AndroidAgent",
    "WebAgent",
    "VisionAgent",
    "VoiceAgent",
]
