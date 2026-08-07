"""Tests for personal AI domain models."""

from dataclasses import FrozenInstanceError

import pytest

from sona_research.domain.personal_models import (
    KnowledgeEdge,
    KnowledgeGraph,
    KnowledgeNode,
    Note,
    NoteType,
    Task,
    TaskPriority,
    TaskStatus,
)


class TestNoteType:
    def test_all_types(self) -> None:
        assert NoteType.QUICK == "quick"
        assert NoteType.STRUCTURED == "structured"
        assert NoteType.JOURNAL == "journal"
        assert NoteType.MEETING == "meeting"
        assert NoteType.DECISION == "decision"

    def test_type_count(self) -> None:
        assert len(NoteType) == 5


class TestTaskStatus:
    def test_all_statuses(self) -> None:
        assert TaskStatus.TODO == "todo"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.BLOCKED == "blocked"
        assert TaskStatus.DONE == "done"
        assert TaskStatus.CANCELLED == "cancelled"

    def test_status_count(self) -> None:
        assert len(TaskStatus) == 5


class TestTaskPriority:
    def test_all_priorities(self) -> None:
        assert TaskPriority.CRITICAL == "critical"
        assert TaskPriority.HIGH == "high"
        assert TaskPriority.MEDIUM == "medium"
        assert TaskPriority.LOW == "low"

    def test_priority_count(self) -> None:
        assert len(TaskPriority) == 4


class TestNote:
    def test_creation_minimal(self) -> None:
        note = Note(note_id="n1", title="Test", content="Body")
        assert note.note_id == "n1"
        assert note.title == "Test"
        assert note.content == "Body"

    def test_creation_full(self) -> None:
        note = Note(
            note_id="n2",
            title="Meeting Notes",
            content="Discussion about X",
            note_type=NoteType.MEETING,
            tags=["work", "project-x"],
            created_at="2024-01-01",
            updated_at="2024-01-02",
        )
        assert note.note_type == NoteType.MEETING
        assert note.tags == ["work", "project-x"]
        assert note.created_at == "2024-01-01"

    def test_defaults(self) -> None:
        note = Note(note_id="n", title="T", content="C")
        assert note.note_type == NoteType.QUICK
        assert note.tags == []
        assert note.created_at == ""
        assert note.updated_at == ""

    def test_is_frozen(self) -> None:
        note = Note(note_id="n", title="T", content="C")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            note.title = "X"  # type: ignore[misc]


class TestTask:
    def test_creation_minimal(self) -> None:
        task = Task(task_id="t1", title="Do something")
        assert task.task_id == "t1"
        assert task.title == "Do something"

    def test_creation_full(self) -> None:
        task = Task(
            task_id="t2",
            title="Fix bug",
            description="Critical bug in auth",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.CRITICAL,
            assignee="dev1",
            due_date="2024-02-01",
            tags=["bug", "auth"],
            parent_task="t1",
            subtasks=["t3", "t4"],
        )
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.CRITICAL
        assert task.subtasks == ["t3", "t4"]

    def test_defaults(self) -> None:
        task = Task(task_id="t", title="T")
        assert task.description == ""
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.MEDIUM
        assert task.assignee == ""
        assert task.due_date == ""
        assert task.tags == []
        assert task.parent_task == ""
        assert task.subtasks == []

    def test_is_frozen(self) -> None:
        task = Task(task_id="t", title="T")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            task.title = "X"  # type: ignore[misc]


class TestKnowledgeNode:
    def test_creation_minimal(self) -> None:
        node = KnowledgeNode(node_id="n1", label="Python", node_type="concept")
        assert node.node_id == "n1"
        assert node.label == "Python"
        assert node.node_type == "concept"

    def test_creation_with_properties(self) -> None:
        node = KnowledgeNode(
            node_id="p1",
            label="Alice",
            node_type="person",
            properties={"role": "developer", "team": "backend"},
        )
        assert node.properties["role"] == "developer"

    def test_defaults(self) -> None:
        node = KnowledgeNode(node_id="n", label="L", node_type="t")
        assert node.properties == {}

    def test_is_frozen(self) -> None:
        node = KnowledgeNode(node_id="n", label="L", node_type="t")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            node.label = "X"  # type: ignore[misc]


class TestKnowledgeEdge:
    def test_creation_minimal(self) -> None:
        edge = KnowledgeEdge(source_id="a", target_id="b", relationship="related_to")
        assert edge.source_id == "a"
        assert edge.target_id == "b"
        assert edge.relationship == "related_to"

    def test_creation_full(self) -> None:
        edge = KnowledgeEdge(
            source_id="p1",
            target_id="proj1",
            relationship="works_on",
            weight=0.8,
            metadata={"since": "2024"},
        )
        assert edge.weight == 0.8
        assert edge.metadata == {"since": "2024"}

    def test_defaults(self) -> None:
        edge = KnowledgeEdge(source_id="a", target_id="b", relationship="r")
        assert edge.weight == 1.0
        assert edge.metadata == {}

    def test_is_frozen(self) -> None:
        edge = KnowledgeEdge(source_id="a", target_id="b", relationship="r")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            edge.weight = 0.5  # type: ignore[misc]


class TestKnowledgeGraph:
    def test_empty_graph(self) -> None:
        graph = KnowledgeGraph()
        assert graph.nodes == {}
        assert graph.edges == []

    def test_add_nodes(self) -> None:
        graph = KnowledgeGraph()
        node = KnowledgeNode(node_id="n1", label="A", node_type="concept")
        graph.nodes[node.node_id] = node
        assert "n1" in graph.nodes

    def test_add_edges(self) -> None:
        graph = KnowledgeGraph()
        edge = KnowledgeEdge(source_id="a", target_id="b", relationship="links")
        graph.edges.append(edge)
        assert len(graph.edges) == 1

    def test_graph_is_mutable(self) -> None:
        graph = KnowledgeGraph()
        graph.nodes["x"] = KnowledgeNode(node_id="x", label="X", node_type="t")
        graph.nodes["y"] = KnowledgeNode(node_id="y", label="Y", node_type="t")
        assert len(graph.nodes) == 2
