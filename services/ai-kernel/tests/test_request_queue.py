"""Unit tests for the request queue module.

Tests verify enqueue, priority ordering, concurrency limits, and backpressure.
"""

import asyncio

import pytest

from sona_ai_kernel.infrastructure.request_queue import QueuedRequest, RequestQueue


class TestQueuedRequest:
    """Tests for the QueuedRequest dataclass."""

    def test_default_priority(self) -> None:
        """Default priority is 5."""
        req = QueuedRequest()
        assert req.priority == 5

    def test_ordering_by_priority(self) -> None:
        """Lower priority number means higher priority in ordering."""
        high = QueuedRequest(priority=1)
        low = QueuedRequest(priority=10)
        assert high < low

    def test_id_generated(self) -> None:
        """Each request gets a unique UUID id."""
        req1 = QueuedRequest()
        req2 = QueuedRequest()
        assert req1.id != req2.id


class TestRequestQueue:
    """Tests for the RequestQueue."""

    @pytest.mark.asyncio
    async def test_enqueue_returns_future(self) -> None:
        """Enqueue returns a future that can be awaited."""
        queue = RequestQueue(max_size=10, max_concurrent=5)
        future = await queue.enqueue("test_request", priority=5)
        assert isinstance(future, asyncio.Future)

    @pytest.mark.asyncio
    async def test_size_increases_on_enqueue(self) -> None:
        """Queue size increases when requests are added."""
        queue = RequestQueue(max_size=10, max_concurrent=5)
        assert queue.size == 0

        await queue.enqueue("request1")
        assert queue.size == 1

        await queue.enqueue("request2")
        assert queue.size == 2

    @pytest.mark.asyncio
    async def test_dequeue_respects_priority(self) -> None:
        """Dequeue returns highest priority (lowest number) first."""
        queue = RequestQueue(max_size=10, max_concurrent=5)

        await queue.enqueue("low", priority=10)
        await queue.enqueue("high", priority=1)
        await queue.enqueue("medium", priority=5)

        first = await queue.dequeue()
        assert first.request == "high"
        assert first.priority == 1

    @pytest.mark.asyncio
    async def test_mark_done_resolves_future(self) -> None:
        """mark_done resolves the request's future with the result."""
        queue = RequestQueue(max_size=10, max_concurrent=5)
        future = await queue.enqueue("my_request")

        queued = await queue.dequeue()
        queue.mark_done(queued, result="completed")

        assert future.done()
        assert future.result() == "completed"

    @pytest.mark.asyncio
    async def test_mark_failed_sets_exception(self) -> None:
        """mark_failed sets an exception on the request's future."""
        queue = RequestQueue(max_size=10, max_concurrent=5)
        future = await queue.enqueue("my_request")

        queued = await queue.dequeue()
        queue.mark_failed(queued, RuntimeError("oops"))

        assert future.done()
        with pytest.raises(RuntimeError, match="oops"):
            future.result()

    @pytest.mark.asyncio
    async def test_active_count_tracks_processing(self) -> None:
        """Active count reflects currently processing requests."""
        queue = RequestQueue(max_size=10, max_concurrent=5)
        assert queue.active == 0

        await queue.enqueue("request")
        queued = await queue.dequeue()
        assert queue.active == 1

        queue.mark_done(queued)
        assert queue.active == 0

    @pytest.mark.asyncio
    async def test_total_processed_increments(self) -> None:
        """total_processed increments on each completion."""
        queue = RequestQueue(max_size=10, max_concurrent=5)
        assert queue.total_processed == 0

        await queue.enqueue("request")
        queued = await queue.dequeue()
        queue.mark_done(queued)
        assert queue.total_processed == 1

    @pytest.mark.asyncio
    async def test_backpressure_on_full_queue(self) -> None:
        """Queue raises QueueFull when at max capacity."""
        queue = RequestQueue(max_size=2, max_concurrent=5)

        await queue.enqueue("r1")
        await queue.enqueue("r2")

        with pytest.raises(asyncio.QueueFull):
            await queue.enqueue("r3")

    @pytest.mark.asyncio
    async def test_concurrency_limit(self) -> None:
        """Semaphore limits concurrent processing."""
        queue = RequestQueue(max_size=10, max_concurrent=2)

        # Enqueue 3 requests with distinct priorities so ordering is deterministic
        await queue.enqueue("r1", priority=1)
        await queue.enqueue("r2", priority=2)
        await queue.enqueue("r3", priority=3)

        # Dequeue 2 (max concurrent)
        q1 = await queue.dequeue()
        q2 = await queue.dequeue()
        assert queue.active == 2
        assert q1.request == "r1"
        assert q2.request == "r2"

        # Third dequeue should block (use wait_for with timeout)
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(queue.dequeue(), timeout=0.05)

        # Complete one to unblock
        queue.mark_done(q1)
        q3 = await asyncio.wait_for(queue.dequeue(), timeout=0.1)
        assert q3.request == "r3"
