"""Tests for task workflow transitions and lifecycle."""

import pytest

from sona_research.domain.personal_models import TaskStatus
from sona_research.infrastructure.tasks.runtime import InvalidTransitionError, TasksRuntime


@pytest.fixture
def runtime() -> TasksRuntime:
    return TasksRuntime()


class TestTaskWorkflowHappyPath:
    @pytest.mark.asyncio
    async def test_full_lifecycle(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("Feature X")
        assert task.status == TaskStatus.TODO

        task = await runtime.transition_status(task.task_id, TaskStatus.IN_PROGRESS)
        assert task.status == TaskStatus.IN_PROGRESS

        task = await runtime.transition_status(task.task_id, TaskStatus.DONE)
        assert task.status == TaskStatus.DONE

    @pytest.mark.asyncio
    async def test_blocked_then_resumed(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("Blocked task")
        await runtime.transition_status(task.task_id, TaskStatus.IN_PROGRESS)
        await runtime.transition_status(task.task_id, TaskStatus.BLOCKED)
        task = await runtime.transition_status(task.task_id, TaskStatus.IN_PROGRESS)
        assert task.status == TaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_cancelled_from_todo(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("Cancel me")
        task = await runtime.transition_status(task.task_id, TaskStatus.CANCELLED)
        assert task.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancelled_from_in_progress(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("Cancel mid-work")
        await runtime.transition_status(task.task_id, TaskStatus.IN_PROGRESS)
        task = await runtime.transition_status(task.task_id, TaskStatus.CANCELLED)
        assert task.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancelled_from_blocked(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("Cancel blocked")
        await runtime.transition_status(task.task_id, TaskStatus.IN_PROGRESS)
        await runtime.transition_status(task.task_id, TaskStatus.BLOCKED)
        task = await runtime.transition_status(task.task_id, TaskStatus.CANCELLED)
        assert task.status == TaskStatus.CANCELLED


class TestTaskWorkflowInvalidTransitions:
    @pytest.mark.asyncio
    async def test_cannot_go_from_done(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("Done task")
        await runtime.complete_task(task.task_id)
        with pytest.raises(InvalidTransitionError):
            await runtime.transition_status(task.task_id, TaskStatus.IN_PROGRESS)

    @pytest.mark.asyncio
    async def test_cannot_go_from_cancelled(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("Cancel task")
        await runtime.transition_status(task.task_id, TaskStatus.CANCELLED)
        with pytest.raises(InvalidTransitionError):
            await runtime.transition_status(task.task_id, TaskStatus.TODO)

    @pytest.mark.asyncio
    async def test_cannot_skip_to_done_from_todo(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("Skip attempt")
        with pytest.raises(InvalidTransitionError):
            await runtime.transition_status(task.task_id, TaskStatus.DONE)

    @pytest.mark.asyncio
    async def test_cannot_block_from_todo(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("Block attempt")
        with pytest.raises(InvalidTransitionError):
            await runtime.transition_status(task.task_id, TaskStatus.BLOCKED)


class TestTaskWorkflowSubtasks:
    @pytest.mark.asyncio
    async def test_subtask_workflow(self, runtime: TasksRuntime) -> None:
        parent = await runtime.create_task("Epic")
        sub1 = await runtime.create_task("Sub 1", parent_task=parent.task_id)
        sub2 = await runtime.create_task("Sub 2", parent_task=parent.task_id)

        await runtime.complete_task(sub1.task_id)
        await runtime.complete_task(sub2.task_id)

        subtasks = await runtime.get_subtasks(parent.task_id)
        assert all(st.status == TaskStatus.DONE for st in subtasks)

    @pytest.mark.asyncio
    async def test_parent_tracks_subtasks(self, runtime: TasksRuntime) -> None:
        parent = await runtime.create_task("Parent")
        await runtime.create_task("S1", parent_task=parent.task_id)
        await runtime.create_task("S2", parent_task=parent.task_id)
        await runtime.create_task("S3", parent_task=parent.task_id)

        parent_updated = await runtime.get_task(parent.task_id)
        assert parent_updated is not None
        assert len(parent_updated.subtasks) == 3


class TestTaskWorkflowUpdate:
    @pytest.mark.asyncio
    async def test_update_title(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("Old Title")
        updated = await runtime.update_task(task.task_id, title="New Title")
        assert updated is not None
        assert updated.title == "New Title"

    @pytest.mark.asyncio
    async def test_update_description(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("T", description="old")
        updated = await runtime.update_task(task.task_id, description="new")
        assert updated is not None
        assert updated.description == "new"

    @pytest.mark.asyncio
    async def test_update_preserves_status(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("T")
        await runtime.transition_status(task.task_id, TaskStatus.IN_PROGRESS)
        updated = await runtime.update_task(task.task_id, title="Updated")
        assert updated is not None
        assert updated.status == TaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_update_nonexistent(self, runtime: TasksRuntime) -> None:
        result = await runtime.update_task("nonexistent", title="X")
        assert result is None


class TestTaskWorkflowCounting:
    @pytest.mark.asyncio
    async def test_count_all(self, runtime: TasksRuntime) -> None:
        await runtime.create_task("A")
        await runtime.create_task("B")
        assert await runtime.count() == 2

    @pytest.mark.asyncio
    async def test_count_by_status(self, runtime: TasksRuntime) -> None:
        t1 = await runtime.create_task("A")
        await runtime.create_task("B")
        await runtime.transition_status(t1.task_id, TaskStatus.IN_PROGRESS)
        assert await runtime.count(TaskStatus.TODO) == 1
        assert await runtime.count(TaskStatus.IN_PROGRESS) == 1

    @pytest.mark.asyncio
    async def test_delete_task(self, runtime: TasksRuntime) -> None:
        task = await runtime.create_task("Delete me")
        deleted = await runtime.delete_task(task.task_id)
        assert deleted is True
        assert await runtime.count() == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, runtime: TasksRuntime) -> None:
        deleted = await runtime.delete_task("nope")
        assert deleted is False
