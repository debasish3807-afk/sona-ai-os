"""AI Kernel module - Central intelligence engine for Sona AI OS.

This module provides the core interfaces for the AI kernel including:
- AIKernel: The central orchestration point
- KernelManager: Lifecycle management and composition root
- TaskRouter: Intelligent task routing
- ProviderRegistry: Provider registration and discovery
- SessionManager: User session management
- ContextManager: Context window assembly
- PromptManager: Prompt lifecycle management
- ResponseManager: Response pipeline processing
- ModelSelector: Intelligent model selection
- EventBus: Decoupled event communication
- StateManager: Kernel state tracking
"""

from kernel.context import (
    ContextConfig,
    ContextEntry,
    ContextManager,
    ContextPriority,
    ContextType,
    ContextWindow,
)
from kernel.events import (
    Event,
    EventBus,
    EventEmitter,
    EventPriority,
    EventResult,
    EventSubscription,
    KernelEvents,
)
from kernel.kernel import (
    AIKernel,
    KernelConfig,
    KernelRequest,
    KernelResponse,
)
from kernel.lifecycle import (
    ComponentHealth,
    ComponentInfo,
    ComponentState,
    HealthStatus,
    Lifecycle,
    LifecycleManager,
)
from kernel.manager import KernelManager, ManagerConfig
from kernel.model_selector import (
    ModelCapability,
    ModelProfile,
    ModelSelector,
    SelectionCriteria,
    SelectionResult,
    SelectionStrategy,
)
from kernel.prompt_manager import (
    PromptFormat,
    PromptManager,
    PromptMessage,
    PromptRole,
    PromptTemplate,
    RenderedPrompt,
)
from kernel.registry import (
    Provider,
    ProviderCapability,
    ProviderHealth,
    ProviderInfo,
    ProviderRegistry,
    ProviderType,
)
from kernel.response_manager import (
    ModelResponse,
    ProcessedResponse,
    ResponseChunk,
    ResponseFilter,
    ResponseFormat,
    ResponseManager,
    ResponseStatus,
    TokenUsage,
)
from kernel.router import (
    RouteDecision,
    RouteRule,
    RouteStatus,
    TaskRouter,
)
from kernel.session import (
    Session,
    SessionConfig,
    SessionManager,
    SessionMessage,
    SessionStatus,
    SessionSummary,
)
from kernel.state import (
    KernelState,
    KernelStatus,
    ProviderStatus,
    ResourceMetrics,
    StateManager,
)
from kernel.task_manager import (
    Task,
    TaskConfig,
    TaskManager,
    TaskPriority,
    TaskStatus,
    TaskSummary,
    TaskType,
)

__all__ = [
    # Kernel
    "AIKernel",
    "KernelConfig",
    "KernelRequest",
    "KernelResponse",
    # Manager
    "KernelManager",
    "ManagerConfig",
    # Router
    "TaskRouter",
    "RouteRule",
    "RouteDecision",
    "RouteStatus",
    # Registry
    "Provider",
    "ProviderCapability",
    "ProviderHealth",
    "ProviderInfo",
    "ProviderRegistry",
    "ProviderType",
    # Context
    "ContextConfig",
    "ContextEntry",
    "ContextManager",
    "ContextPriority",
    "ContextType",
    "ContextWindow",
    # Session
    "Session",
    "SessionConfig",
    "SessionManager",
    "SessionMessage",
    "SessionStatus",
    "SessionSummary",
    # Events
    "Event",
    "EventBus",
    "EventEmitter",
    "EventPriority",
    "EventResult",
    "EventSubscription",
    "KernelEvents",
    # Lifecycle
    "ComponentHealth",
    "ComponentInfo",
    "ComponentState",
    "HealthStatus",
    "Lifecycle",
    "LifecycleManager",
    # Prompt
    "PromptFormat",
    "PromptManager",
    "PromptMessage",
    "PromptRole",
    "PromptTemplate",
    "RenderedPrompt",
    # Response
    "ModelResponse",
    "ProcessedResponse",
    "ResponseChunk",
    "ResponseFilter",
    "ResponseFormat",
    "ResponseManager",
    "ResponseStatus",
    "TokenUsage",
    # Task
    "Task",
    "TaskConfig",
    "TaskManager",
    "TaskPriority",
    "TaskStatus",
    "TaskSummary",
    "TaskType",
    # State
    "KernelState",
    "KernelStatus",
    "ProviderStatus",
    "ResourceMetrics",
    "StateManager",
    # Model Selection
    "ModelCapability",
    "ModelProfile",
    "ModelSelector",
    "SelectionCriteria",
    "SelectionResult",
    "SelectionStrategy",
]
