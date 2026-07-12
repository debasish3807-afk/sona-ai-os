"""Engine Protocol — the contract every cognitive engine must implement.

Engines are the processing units of the Cognitive Kernel. Each engine
handles one stage of the cognitive pipeline (intent, goal, reasoning, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EngineState(str, Enum):
    """Lifecycle states for a cognitive engine."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class EngineInfo:
    """Metadata about a registered engine."""

    engine_id: str
    name: str
    version: str = "1.0.0"
    priority: int = 50  # Lower = higher priority
    dependencies: list[str] = field(default_factory=list)
    state: EngineState = EngineState.CREATED
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineResult:
    """Result returned by an engine after processing."""

    engine_id: str
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    duration_ms: float = 0.0
    tokens_used: int = 0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class CognitiveEngine(ABC):
    """Abstract base for all cognitive engines.

    Every engine in the pipeline implements this protocol.
    The kernel coordinates engines through this interface.
    """

    @property
    @abstractmethod
    def info(self) -> EngineInfo:
        """Return engine metadata."""
        ...

    @property
    @abstractmethod
    def state(self) -> EngineState:
        """Current lifecycle state."""
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize engine (load models, connect services)."""
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start the engine (begin accepting work)."""
        ...

    @abstractmethod
    async def process(self, context: dict[str, Any]) -> EngineResult:
        """Process a request through this engine.

        Args:
            context: The current pipeline context dict.

        Returns:
            EngineResult with output data.
        """
        ...

    @abstractmethod
    async def pause(self) -> None:
        """Temporarily pause processing."""
        ...

    @abstractmethod
    async def resume(self) -> None:
        """Resume from paused state."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the engine gracefully."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Full shutdown — release all resources."""
        ...

    @abstractmethod
    async def health(self) -> bool:
        """Return True if engine is healthy."""
        ...

    @abstractmethod
    def metrics(self) -> dict[str, Any]:
        """Return engine-specific metrics."""
        ...
