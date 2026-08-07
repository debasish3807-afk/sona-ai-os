"""Domain events for the Personal AI Integration Runtime."""

from dataclasses import dataclass

from sona_shared.domain.primitives import DomainEvent


@dataclass(frozen=True)
class RepositoryIndexedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a GitHub repository has been indexed."""

    owner: str = ""
    repo: str = ""
    commits_indexed: int = 0


@dataclass(frozen=True)
class WorkspaceIndexedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a workspace directory has been indexed."""

    path: str = ""
    documents_indexed: int = 0


@dataclass(frozen=True)
class NoteCreatedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a new note is created."""

    note_id: str = ""
    title: str = ""


@dataclass(frozen=True)
class TaskCreatedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a new task is created."""

    task_id: str = ""
    title: str = ""
    priority: str = ""


@dataclass(frozen=True)
class KnowledgeGraphUpdatedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when the knowledge graph is updated."""

    nodes_added: int = 0
    edges_added: int = 0
