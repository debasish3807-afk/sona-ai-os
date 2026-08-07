"""Tests for the Personal AI Runtime orchestrator."""

import pytest

from sona_research.domain.personal_models import NoteType, TaskPriority
from sona_research.infrastructure.di import create_personal_ai_runtime
from sona_research.infrastructure.personal_ai_runtime import PersonalAIRuntime


@pytest.fixture
def runtime() -> PersonalAIRuntime:
    return create_personal_ai_runtime()


class TestPersonalAIRuntimeNotes:
    @pytest.mark.asyncio
    async def test_create_note(self, runtime: PersonalAIRuntime) -> None:
        note = await runtime.create_note("Test", "Content")
        assert note.title == "Test"
        assert note.content == "Content"

    @pytest.mark.asyncio
    async def test_create_note_with_type(self, runtime: PersonalAIRuntime) -> None:
        note = await runtime.create_note("M", "Meeting", NoteType.MEETING, ["work"])
        assert note.note_type == NoteType.MEETING
        assert note.tags == ["work"]

    @pytest.mark.asyncio
    async def test_search_notes(self, runtime: PersonalAIRuntime) -> None:
        await runtime.create_note("Python Guide", "How to write Python")
        await runtime.create_note("Java Guide", "How to write Java")
        results = await runtime.search_notes("Python")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_create_note_updates_metrics(self, runtime: PersonalAIRuntime) -> None:
        await runtime.create_note("T", "C")
        assert runtime.metrics.get_counter("notes_created_total") == 1.0


class TestPersonalAIRuntimeTasks:
    @pytest.mark.asyncio
    async def test_create_task(self, runtime: PersonalAIRuntime) -> None:
        task = await runtime.create_task("Do something")
        assert task.title == "Do something"

    @pytest.mark.asyncio
    async def test_create_task_with_priority(self, runtime: PersonalAIRuntime) -> None:
        task = await runtime.create_task("Urgent", priority=TaskPriority.CRITICAL)
        assert task.priority == TaskPriority.CRITICAL

    @pytest.mark.asyncio
    async def test_complete_task(self, runtime: PersonalAIRuntime) -> None:
        task = await runtime.create_task("T")
        completed = await runtime.complete_task(task.task_id)
        assert completed.status.value == "done"

    @pytest.mark.asyncio
    async def test_create_task_updates_metrics(self, runtime: PersonalAIRuntime) -> None:
        await runtime.create_task("T", priority=TaskPriority.HIGH)
        assert (
            runtime.metrics.get_counter("tasks_created_total", labels={"priority": "high"}) == 1.0
        )


class TestPersonalAIRuntimeKnowledgeGraph:
    @pytest.mark.asyncio
    async def test_add_knowledge(self, runtime: PersonalAIRuntime) -> None:
        node = await runtime.add_knowledge("Python", "concept")
        assert node.label == "Python"
        assert node.node_type == "concept"

    @pytest.mark.asyncio
    async def test_add_knowledge_with_properties(self, runtime: PersonalAIRuntime) -> None:
        node = await runtime.add_knowledge("ML", "concept", {"level": "advanced"})
        assert node.properties == {"level": "advanced"}

    @pytest.mark.asyncio
    async def test_knowledge_updates_metrics(self, runtime: PersonalAIRuntime) -> None:
        await runtime.add_knowledge("Test", "concept")
        assert (
            runtime.metrics.get_counter("graph_nodes_added_total", labels={"type": "concept"})
            == 1.0
        )


class TestPersonalAIRuntimeWorkspace:
    @pytest.mark.asyncio
    async def test_index_workspace(self, runtime: PersonalAIRuntime) -> None:
        runtime.workspace_scanner.add_file("/docs/readme.md", "# Hello")
        runtime.workspace_scanner.add_file("/src/main.py", "print('hi')")
        indexed = await runtime.index_workspace("/")
        assert len(indexed) == 2

    @pytest.mark.asyncio
    async def test_search_workspace(self, runtime: PersonalAIRuntime) -> None:
        runtime.workspace_scanner.add_file("/docs/api.md", "REST API guide")
        await runtime.index_workspace("/")
        results = await runtime.search_workspace("API")
        assert len(results) == 1


class TestPersonalAIRuntimeGitHub:
    @pytest.mark.asyncio
    async def test_get_repository_info(self, runtime: PersonalAIRuntime) -> None:
        repo = await runtime.get_repository_info("owner", "repo")
        assert repo.owner == "owner"
        assert repo.name == "repo"

    @pytest.mark.asyncio
    async def test_index_github_repo(self, runtime: PersonalAIRuntime) -> None:
        stats = await runtime.index_github_repository("owner", "repo")
        assert "nodes_indexed" in stats
        assert "edges_created" in stats


class TestPersonalAIRuntimeSummary:
    @pytest.mark.asyncio
    async def test_get_summary(self, runtime: PersonalAIRuntime) -> None:
        await runtime.create_note("N", "C")
        await runtime.create_task("T")
        summary = await runtime.get_runtime_summary()
        assert summary["notes"] == 1
        assert summary["tasks"] == 1
