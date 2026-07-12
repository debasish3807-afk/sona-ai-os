"""Project memory - project-specific context and history.

This module defines the project memory interface for managing
project-scoped context including files, dependencies, conventions,
and project-specific knowledge. Each project maintains its own
isolated memory space.

Classes:
    ProjectConfig: Configuration for project memory behavior.
    ProjectContext: Complete context definition for a project.
    ProjectMemory: Abstract interface extending MemoryStore for project memory.
"""

from __future__ import annotations

import uuid
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .base import MemoryStore
from .types import MemoryEntry, MemoryQuery


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    """Configuration for project memory behavior.

    Controls capacity, indexing, and per-project limits.

    Attributes:
        max_projects: Maximum number of projects to maintain.
        max_entries_per_project: Maximum memory entries per project.
        auto_index: Whether to automatically index project content.
        auto_detect_conventions: Whether to auto-detect project conventions.
        track_file_changes: Whether to track file modification history.
    """

    max_projects: int = 100
    max_entries_per_project: int = 10000
    auto_index: bool = True
    auto_detect_conventions: bool = True
    track_file_changes: bool = True


@dataclass(slots=True)
class ProjectContext:
    """Complete context definition for a project.

    Captures all relevant project information including structure,
    dependencies, coding conventions, and custom metadata.

    Attributes:
        project_id: Unique identifier for this project (UUID4).
        name: Human-readable project name.
        description: Brief description of the project.
        files: List of key file paths in the project.
        dependencies: List of project dependencies.
        conventions: List of coding conventions or rules.
        language: Primary programming language.
        framework: Primary framework if applicable.
        created_at: UTC timestamp when this project was registered.
        updated_at: UTC timestamp of the most recent update.
        metadata: Additional project metadata (e.g., repo URL, team info).
    """

    name: str
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    files: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    conventions: list[str] = field(default_factory=list)
    language: str | None = None
    framework: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


class ProjectMemory(MemoryStore):
    """Abstract interface for project memory operations.

    Extends the base MemoryStore with project lifecycle management,
    project-scoped memory operations, and project context retrieval.
    """

    @abstractmethod
    async def create_project(self, context: ProjectContext) -> str:
        """Create a new project context.

        Registers a new project and initializes its memory space.

        Args:
            context: The project context definition.

        Returns:
            The project_id of the created project.
        """
        ...

    @abstractmethod
    async def get_project(self, project_id: str) -> ProjectContext | None:
        """Retrieve a project context by its ID.

        Args:
            project_id: The unique identifier of the project.

        Returns:
            The project context if found, None otherwise.
        """
        ...

    @abstractmethod
    async def update_project(
        self, project_id: str, updates: dict[str, Any]
    ) -> ProjectContext | None:
        """Update a project context with new information.

        Args:
            project_id: The ID of the project to update.
            updates: Dictionary of fields to update.

        Returns:
            The updated project context, or None if not found.
        """
        ...

    @abstractmethod
    async def add_project_memory(self, project_id: str, entry: MemoryEntry) -> str:
        """Add a memory entry scoped to a specific project.

        Args:
            project_id: The project to add the memory to.
            entry: The memory entry to store.

        Returns:
            The entry_id of the stored memory.
        """
        ...

    @abstractmethod
    async def get_project_memories(
        self, project_id: str, query: MemoryQuery | None = None
    ) -> list[MemoryEntry]:
        """Get memory entries for a specific project.

        Args:
            project_id: The project to retrieve memories for.
            query: Optional query for filtering results.

        Returns:
            List of memory entries scoped to the project.
        """
        ...

    @abstractmethod
    async def list_projects(self, limit: int = 50) -> list[ProjectContext]:
        """List all registered projects.

        Args:
            limit: Maximum number of projects to return.

        Returns:
            List of project contexts.
        """
        ...

    @abstractmethod
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project and all its associated memories.

        Args:
            project_id: The ID of the project to delete.

        Returns:
            True if the project was found and deleted, False otherwise.
        """
        ...
