"""AI Kernel entry point.

The central intelligence engine of Sona AI OS. Coordinates all
kernel subsystems including routing, sessions, context, prompts,
responses, model selection, and provider management.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from kernel.context import ContextManager
from kernel.events import EventBus
from kernel.model_selector import ModelSelector
from kernel.prompt_manager import PromptManager
from kernel.registry import ProviderRegistry
from kernel.response_manager import (
    ResponseChunk,
    ResponseManager,
)
from kernel.router import TaskRouter
from kernel.session import SessionManager
from kernel.state import KernelState, StateManager
from kernel.task_manager import TaskManager, TaskType


@dataclass
class KernelConfig:
    """Configuration for the AI Kernel.

    Attributes:
        max_concurrent_tasks: Maximum tasks executing simultaneously.
        default_timeout_seconds: Default task timeout.
        enable_streaming: Whether streaming responses are enabled.
        enable_event_bus: Whether the event bus is active.
        max_sessions: Maximum active sessions.
        metadata: Additional kernel configuration.
    """

    max_concurrent_tasks: int = 10
    default_timeout_seconds: int = 120
    enable_streaming: bool = True
    enable_event_bus: bool = True
    max_sessions: int = 1000
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class KernelRequest:
    """A request submitted to the AI kernel.

    Attributes:
        session_id: Target session for this request.
        content: The user's input content.
        task_type: Type of task to execute.
        streaming: Whether to stream the response.
        model_preference: Optional preferred model.
        context_override: Optional context configuration.
        metadata: Additional request metadata.
    """

    session_id: str
    content: str
    task_type: TaskType = TaskType.CHAT
    streaming: bool = False
    model_preference: str | None = None
    context_override: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class KernelResponse:
    """Response returned from the AI kernel.

    Attributes:
        session_id: Session that produced this response.
        task_id: Task that generated this response.
        content: The response content.
        model_used: Model that generated the response.
        token_usage: Token consumption details.
        latency_ms: Total processing latency.
        metadata: Additional response metadata.
    """

    session_id: str
    task_id: str
    content: str
    model_used: str = ""
    token_usage: dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class AIKernel(ABC):
    """Abstract interface for the AI Kernel.

    The kernel is the central orchestration point that coordinates
    all AI subsystems. It receives requests, manages their lifecycle,
    and returns processed responses.
    """

    @property
    @abstractmethod
    def config(self) -> KernelConfig:
        """Get kernel configuration."""
        ...

    @property
    @abstractmethod
    def state_manager(self) -> StateManager:
        """Access the kernel state manager."""
        ...

    @property
    @abstractmethod
    def session_manager(self) -> SessionManager:
        """Access the session manager."""
        ...

    @property
    @abstractmethod
    def task_manager(self) -> TaskManager:
        """Access the task manager."""
        ...

    @property
    @abstractmethod
    def context_manager(self) -> ContextManager:
        """Access the context manager."""
        ...

    @property
    @abstractmethod
    def prompt_manager(self) -> PromptManager:
        """Access the prompt manager."""
        ...

    @property
    @abstractmethod
    def response_manager(self) -> ResponseManager:
        """Access the response manager."""
        ...

    @property
    @abstractmethod
    def model_selector(self) -> ModelSelector:
        """Access the model selector."""
        ...

    @property
    @abstractmethod
    def router(self) -> TaskRouter:
        """Access the task router."""
        ...

    @property
    @abstractmethod
    def registry(self) -> ProviderRegistry:
        """Access the provider registry."""
        ...

    @property
    @abstractmethod
    def event_bus(self) -> EventBus:
        """Access the event bus."""
        ...

    @abstractmethod
    async def process(self, request: KernelRequest) -> KernelResponse:
        """Process a request through the kernel pipeline.

        This is the primary entry point for all AI interactions.
        The full pipeline includes:
        1. Session validation
        2. Context assembly
        3. Model selection
        4. Prompt construction
        5. Task routing and execution
        6. Response processing

        Args:
            request: The kernel request to process.

        Returns:
            Processed KernelResponse.

        Raises:
            ValueError: If the request is invalid.
            RuntimeError: If the kernel is not operational.
        """
        ...

    @abstractmethod
    async def process_stream(
        self,
        request: KernelRequest,
    ) -> AsyncIterator[ResponseChunk]:
        """Process a request with streaming response.

        Same pipeline as process() but yields response chunks
        as they are generated.

        Args:
            request: The kernel request to process.

        Yields:
            ResponseChunk instances as they become available.

        Raises:
            ValueError: If the request is invalid.
            RuntimeError: If the kernel is not operational.
        """
        ...

    @abstractmethod
    async def get_state(self) -> KernelState:
        """Get the current kernel state.

        Returns:
            Current KernelState snapshot.
        """
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the kernel and all subsystems.

        Brings the kernel from STOPPED to READY state.

        Raises:
            RuntimeError: If initialization fails.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the kernel gracefully.

        Completes in-progress tasks, closes sessions, and
        releases all resources.
        """
        ...
