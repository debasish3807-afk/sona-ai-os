"""Personal AI domain models (notes, tasks, knowledge graph)."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class NoteType(StrEnum):
    """Types of notes that can be created."""

    QUICK = "quick"
    STRUCTURED = "structured"
    JOURNAL = "journal"
    MEETING = "meeting"
    DECISION = "decision"


class TaskStatus(StrEnum):
    """Possible statuses for a task."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(StrEnum):
    """Priority levels for tasks."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class Note:
    """A personal note."""

    note_id: str
    title: str
    content: str
    note_type: NoteType = NoteType.QUICK
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True)
class Task:
    """A personal task."""

    task_id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: str = ""
    due_date: str = ""
    tags: list[str] = field(default_factory=list)
    parent_task: str = ""
    subtasks: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class KnowledgeNode:
    """A node in the personal knowledge graph."""

    node_id: str
    label: str
    node_type: str  # e.g., "concept", "person", "project", "decision"
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeEdge:
    """An edge connecting two nodes in the knowledge graph."""

    source_id: str
    target_id: str
    relationship: str  # e.g., "related_to", "depends_on", "authored_by"
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    """A personal knowledge graph containing nodes and edges."""

    nodes: dict[str, KnowledgeNode] = field(default_factory=dict)
    edges: list[KnowledgeEdge] = field(default_factory=list)
