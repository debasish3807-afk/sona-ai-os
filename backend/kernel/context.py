"""Context management for AI kernel operations.

Manages the assembly, enrichment, and lifecycle of context objects
that are passed to AI models. Context includes conversation history,
system instructions, user preferences, and retrieved knowledge.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class ContextType(str, Enum):
    """Types of context entries."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    METADATA = "metadata"


class ContextPriority(int, Enum):
    """Priority levels for context entries during truncation.

    Higher priority entries are preserved when context window is exceeded.
    """

    CRITICAL = 0  # Never truncated (system instructions)
    HIGH = 10  # Rarely truncated (recent messages)
    NORMAL = 50  # Standard priority
    LOW = 90  # Truncated first (old context)
    EXPENDABLE = 100  # Always truncated first


@dataclass
class ContextEntry:
    """A single entry in the context window.

    Attributes:
        entry_id: Unique identifier for this entry.
        context_type: Type classification of this entry.
        content: The actual content string.
        role: Message role (system, user, assistant, tool).
        priority: Truncation priority.
        token_count: Estimated token count for this entry.
        timestamp: When this entry was created.
        source: Origin of this context entry.
        metadata: Additional entry metadata.
    """

    content: str
    context_type: ContextType
    role: str = "user"
    entry_id: str = field(default_factory=lambda: str(uuid4()))
    priority: ContextPriority = ContextPriority.NORMAL
    token_count: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextWindow:
    """Assembled context window ready for model consumption.

    Attributes:
        window_id: Unique identifier for this context assembly.
        session_id: Associated session identifier.
        entries: Ordered list of context entries.
        total_tokens: Total estimated token count.
        max_tokens: Maximum allowed tokens for this window.
        truncated: Whether entries were removed due to token limits.
        created_at: Assembly timestamp.
        metadata: Additional window metadata.
    """

    session_id: str
    entries: list[ContextEntry] = field(default_factory=list)
    window_id: str = field(default_factory=lambda: str(uuid4()))
    total_tokens: int = 0
    max_tokens: int = 8192
    truncated: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def remaining_tokens(self) -> int:
        """Calculate remaining token budget."""
        return max(0, self.max_tokens - self.total_tokens)

    @property
    def utilization(self) -> float:
        """Calculate context window utilization as a ratio."""
        if self.max_tokens == 0:
            return 0.0
        return self.total_tokens / self.max_tokens


@dataclass
class ContextConfig:
    """Configuration for context assembly.

    Attributes:
        max_tokens: Maximum token budget for the context window.
        max_history_entries: Maximum conversation history entries.
        include_system_prompt: Whether to include system instructions.
        include_memory: Whether to query and include memory context.
        include_knowledge: Whether to include RAG-retrieved knowledge.
        truncation_strategy: Strategy for handling token overflow.
        metadata: Additional configuration metadata.
    """

    max_tokens: int = 8192
    max_history_entries: int = 50
    include_system_prompt: bool = True
    include_memory: bool = True
    include_knowledge: bool = True
    truncation_strategy: str = "priority"  # priority | fifo | sliding
    metadata: dict[str, Any] = field(default_factory=dict)


class ContextManager(ABC):
    """Abstract interface for context management.

    Handles the assembly, enrichment, and optimization of context
    windows for AI model consumption.
    """

    @abstractmethod
    async def build_context(
        self,
        session_id: str,
        config: ContextConfig | None = None,
    ) -> ContextWindow:
        """Build a complete context window for a session.

        Assembles all relevant context including system prompts,
        conversation history, memory, and retrieved knowledge.

        Args:
            session_id: The session to build context for.
            config: Optional context configuration overrides.

        Returns:
            Assembled ContextWindow ready for model consumption.
        """
        ...

    @abstractmethod
    async def add_entry(
        self,
        session_id: str,
        entry: ContextEntry,
    ) -> None:
        """Add a new entry to a session's context.

        Args:
            session_id: The target session.
            entry: The context entry to add.
        """
        ...

    @abstractmethod
    async def get_entries(
        self,
        session_id: str,
        context_type: ContextType | None = None,
        limit: int | None = None,
    ) -> list[ContextEntry]:
        """Retrieve context entries for a session.

        Args:
            session_id: The session to query.
            context_type: Optional filter by entry type.
            limit: Maximum number of entries to return.

        Returns:
            List of matching context entries.
        """
        ...

    @abstractmethod
    async def clear_context(self, session_id: str) -> None:
        """Clear all context entries for a session.

        Args:
            session_id: The session to clear.
        """
        ...

    @abstractmethod
    async def truncate(
        self,
        window: ContextWindow,
        target_tokens: int,
    ) -> ContextWindow:
        """Truncate a context window to fit within a token budget.

        Applies the configured truncation strategy to reduce
        the context window to the target token count.

        Args:
            window: The context window to truncate.
            target_tokens: Target maximum token count.

        Returns:
            Truncated ContextWindow within the token budget.
        """
        ...

    @abstractmethod
    async def estimate_tokens(self, content: str) -> int:
        """Estimate the token count for a given content string.

        Args:
            content: Text content to estimate tokens for.

        Returns:
            Estimated token count.
        """
        ...
