"""Tests for the background worker."""

from typing import Any

import pytest

from sona_knowledge.infrastructure.background_worker import (
    BackgroundWorker,
    TaskStatus,
)


@pytest.fixture
def worker() -> BackgroundWorker:
    return BackgroundWorker(max_concurrency=2)


class TestBackgroundWorker:
    """Tests for BackgroundWorker."""

    @pytest.mark.asyncio
    async def test_submit_task(self, worker: BackgroundWorker) -> None:
        task = await worker.submit("task-1", {"key": "value"})
        assert task.task_id == "task-1"
        assert task.status == TaskStatus.QUEUED

    @pytest.mark.asyncio
    async def test_get_status_queued(self, worker: BackgroundWorker) -> None:
        await worker.submit("task-1", {})
        assert worker.get_status("task-1") == TaskStatus.QUEUED

    @pytest.mark.asyncio
    async def test_get_status_unknown(self, worker: BackgroundWorker) -> None:
        assert worker.get_status("nonexistent") is None

    @pytest.mark.asyncio
    async def test_process_one_completes_task(self, worker: BackgroundWorker) -> None:
        async def processor(payload: dict[str, Any]) -> str:
            return f"processed-{payload.get('id')}"

        worker.set_processor(processor)
        await worker.submit("task-1", {"id": "123"})
        result = await worker.process_one()
        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert result.result == "processed-123"

    @pytest.mark.asyncio
    async def test_process_one_empty_queue(self, worker: BackgroundWorker) -> None:
        result = await worker.process_one()
        assert result is None

    @pytest.mark.asyncio
    async def test_process_one_failed(self, worker: BackgroundWorker) -> None:
        async def failing_processor(payload: dict[str, Any]) -> str:
            raise ValueError("Processing error")

        worker.set_processor(failing_processor)
        await worker.submit("task-1", {})
        result = await worker.process_one()
        assert result is not None
        assert result.status == TaskStatus.FAILED
        assert "Processing error" in str(result.error)

    @pytest.mark.asyncio
    async def test_process_all(self, worker: BackgroundWorker) -> None:
        async def processor(payload: dict[str, Any]) -> str:
            return "done"

        worker.set_processor(processor)
        await worker.submit("task-1", {})
        await worker.submit("task-2", {})
        await worker.submit("task-3", {})
        results = await worker.process_all()
        assert len(results) == 3
        assert all(r.status == TaskStatus.COMPLETED for r in results)

    @pytest.mark.asyncio
    async def test_queue_size(self, worker: BackgroundWorker) -> None:
        await worker.submit("task-1", {})
        await worker.submit("task-2", {})
        assert worker.queue_size == 2

    @pytest.mark.asyncio
    async def test_task_count(self, worker: BackgroundWorker) -> None:
        await worker.submit("task-1", {})
        await worker.submit("task-2", {})
        assert worker.task_count == 2

    @pytest.mark.asyncio
    async def test_get_task(self, worker: BackgroundWorker) -> None:
        await worker.submit("task-1", {"data": "test"})
        task = worker.get_task("task-1")
        assert task is not None
        assert task.payload == {"data": "test"}

    @pytest.mark.asyncio
    async def test_get_all_tasks(self, worker: BackgroundWorker) -> None:
        await worker.submit("task-1", {})
        await worker.submit("task-2", {})
        tasks = worker.get_all_tasks()
        assert len(tasks) == 2

    @pytest.mark.asyncio
    async def test_no_processor_fails(self, worker: BackgroundWorker) -> None:
        await worker.submit("task-1", {})
        result = await worker.process_one()
        assert result is not None
        assert result.status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_concurrency_limit(self) -> None:
        worker = BackgroundWorker(max_concurrency=1)

        async def slow_processor(payload: dict[str, Any]) -> str:
            return "done"

        worker.set_processor(slow_processor)
        await worker.submit("task-1", {})
        await worker.submit("task-2", {})
        results = await worker.process_all()
        assert len(results) == 2
