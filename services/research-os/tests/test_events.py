"""Tests for domain events."""

from sona_research.domain.events import (
    KnowledgeGraphUpdatedEvent,
    NoteCreatedEvent,
    RepositoryIndexedEvent,
    TaskCreatedEvent,
    WorkspaceIndexedEvent,
)


class TestRepositoryIndexedEvent:
    def test_creation_defaults(self) -> None:
        event = RepositoryIndexedEvent()
        assert event.owner == ""
        assert event.repo == ""
        assert event.commits_indexed == 0

    def test_creation_with_values(self) -> None:
        event = RepositoryIndexedEvent(owner="octocat", repo="hello", commits_indexed=50)
        assert event.owner == "octocat"
        assert event.repo == "hello"
        assert event.commits_indexed == 50

    def test_has_event_id(self) -> None:
        event = RepositoryIndexedEvent()
        assert event.event_id is not None

    def test_has_occurred_at(self) -> None:
        event = RepositoryIndexedEvent()
        assert event.occurred_at is not None

    def test_is_frozen(self) -> None:
        event = RepositoryIndexedEvent(owner="x")
        # DomainEvent is frozen
        assert event.owner == "x"


class TestWorkspaceIndexedEvent:
    def test_creation_defaults(self) -> None:
        event = WorkspaceIndexedEvent()
        assert event.path == ""
        assert event.documents_indexed == 0

    def test_creation_with_values(self) -> None:
        event = WorkspaceIndexedEvent(path="/docs", documents_indexed=10)
        assert event.path == "/docs"
        assert event.documents_indexed == 10

    def test_has_event_id(self) -> None:
        event = WorkspaceIndexedEvent()
        assert event.event_id is not None

    def test_unique_event_ids(self) -> None:
        e1 = WorkspaceIndexedEvent()
        e2 = WorkspaceIndexedEvent()
        assert e1.event_id != e2.event_id


class TestNoteCreatedEvent:
    def test_creation_defaults(self) -> None:
        event = NoteCreatedEvent()
        assert event.note_id == ""
        assert event.title == ""

    def test_creation_with_values(self) -> None:
        event = NoteCreatedEvent(note_id="note-001", title="My Note")
        assert event.note_id == "note-001"
        assert event.title == "My Note"

    def test_has_event_id(self) -> None:
        event = NoteCreatedEvent()
        assert event.event_id is not None


class TestTaskCreatedEvent:
    def test_creation_defaults(self) -> None:
        event = TaskCreatedEvent()
        assert event.task_id == ""
        assert event.title == ""
        assert event.priority == ""

    def test_creation_with_values(self) -> None:
        event = TaskCreatedEvent(task_id="task-001", title="Fix bug", priority="critical")
        assert event.task_id == "task-001"
        assert event.title == "Fix bug"
        assert event.priority == "critical"

    def test_has_event_id(self) -> None:
        event = TaskCreatedEvent()
        assert event.event_id is not None


class TestKnowledgeGraphUpdatedEvent:
    def test_creation_defaults(self) -> None:
        event = KnowledgeGraphUpdatedEvent()
        assert event.nodes_added == 0
        assert event.edges_added == 0

    def test_creation_with_values(self) -> None:
        event = KnowledgeGraphUpdatedEvent(nodes_added=5, edges_added=3)
        assert event.nodes_added == 5
        assert event.edges_added == 3

    def test_has_event_id(self) -> None:
        event = KnowledgeGraphUpdatedEvent()
        assert event.event_id is not None

    def test_unique_event_ids(self) -> None:
        e1 = KnowledgeGraphUpdatedEvent()
        e2 = KnowledgeGraphUpdatedEvent()
        assert e1.event_id != e2.event_id
