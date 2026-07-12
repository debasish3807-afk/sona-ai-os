"""Base tool interface and shared types.

All tools implement BaseTool. The ToolResult is the standardized
return type for every tool execution.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class ToolCategory(str, Enum):
    """Tool classification categories."""

    FILESYSTEM = "filesystem"
    TERMINAL = "terminal"
    GIT = "git"
    GITHUB = "github"
    BROWSER = "browser"
    PYTHON = "python"
    DATABASE = "database"


@dataclass(frozen=True)
class ToolParam:
    """A single parameter definition for a tool."""

    name: str
    param_type: str  # "string", "integer", "boolean", "array", "object"
    description: str
    required: bool = True
    default: Any = None


@dataclass(frozen=True)
class ToolMetadata:
    """Metadata describing a tool's capabilities and interface."""

    name: str
    description: str
    category: ToolCategory
    parameters: list[ToolParam] = field(default_factory=list)
    dangerous: bool = False  # Requires confirmation
    read_only: bool = False  # Does not modify state


@dataclass
class ToolResult:
    """Standardized result from any tool execution."""

    success: bool
    output: str = ""
    error: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    tool_name: str = ""
    executed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class BaseTool(ABC):
    """Abstract base class for all tools.

    Every tool must declare its metadata and implement execute().
    """

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Return the tool's metadata description."""
        ...

    @abstractmethod
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the tool with the given parameters.

        Args:
            **params: Tool-specific parameters.

        Returns:
            ToolResult with output or error.
        """
        ...

    @property
    def name(self) -> str:
        """Shortcut to metadata.name."""
        return self.metadata.name

    @property
    def category(self) -> ToolCategory:
        """Shortcut to metadata.category."""
        return self.metadata.category

    @property
    def is_dangerous(self) -> bool:
        """Whether this tool requires confirmation."""
        return self.metadata.dangerous
