"""Tests for Brain OS runtime — full integration tests.

Tests verify the complete execution flow: accept plan → execute → aggregate → respond.
"""

import pytest

from sona_brain.application.ports import BrainOrchestratorPort
from sona_brain.domain.events import ExecutionCompletedEvent, ExecutionStartedEvent
from sona_brain.domain.models import BrainRequest, BrainResponse
from sona_brain.infrastructure.brain_runtime import BrainRuntime
from sona_brain.infrastructure.di import create_brain_runtime
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep, ExecutionStepType


def _make_request(
    messages: list[dict[str, str]] | None = None,
    stream: bool = False,
) -> BrainRequest:
    """Create a test request."""
    return BrainRequest(
        session_id="test-session",
        user_id="test-user",
        messages=messages or [{"role": "user", "content": "Hello"}],
        stream=stream,
    )


def _make_plan(steps: list[ExecutionStep] | None = None) -> ExecutionPlan:
    """Create a test plan."""
    if steps is None:
        steps = [
            ExecutionStep(
                step_id="llm-main",
                step_type=ExecutionStepType.LLM_CALL,
                target="test-model",
                params={"prompt": "Hello", "max_tokens_in": 50, "max_tokens_out": 25},
                timeout_seconds=30.0,
            ),
        ]
    return ExecutionPlan(
        plan_id="test-plan",
        intent="general",
        steps=steps,
        model_id="test-model",
        provider="test-provider",
        confidence=0.9,
    )


class TestBrainRuntime:
    """Tests for BrainRuntime."""

    def test_implements_port(self) -> None:
        """Verify BrainRuntime implements BrainOrchestratorPort."""
        runtime = create_brain_runtime()
        assert isinstance(runtime, BrainOrchestratorPort)

    @pytest.mark.asyncio
    async def test_execute_basic_request(self) -> None:
        """Execute a basic request and get a response."""
        runtime = create_brain_runtime()
        request = _make_request()

        response = await runtime.execute(request)
        assert isinstance(response, BrainResponse)
        assert response.session_id == "test-session"
        assert response.content != ""
        assert response.latency_ms > 0

    @pytest.mark.asyncio
    async def test_execute_plan_directly(self) -> None:
        """Execute a pre-built plan."""
        runtime = create_brain_runtime()
        request = _make_request()
        plan = _make_plan()

        response = await runtime.execute_plan(plan, request)
        assert isinstance(response, BrainResponse)
        assert response.content != ""
        assert response.model_used != ""

    @pytest.mark.asyncio
    async def test_execute_multi_step_plan(self) -> None:
        """Execute a plan with multiple steps."""
        runtime = create_brain_runtime()
        request = _make_request()
        steps = [
            ExecutionStep(
                step_id="memory",
                step_type=ExecutionStepType.MEMORY_RETRIEVAL,
                target="memory-os",
                params={"query": "user context"},
            ),
            ExecutionStep(
                step_id="llm",
                step_type=ExecutionStepType.LLM_CALL,
                target="gpt-4o",
                params={"prompt": "Answer", "max_tokens_in": 50, "max_tokens_out": 25},
                depends_on=["memory"],
            ),
        ]
        plan = _make_plan(steps)

        response = await runtime.execute_plan(plan, request)
        assert response.content != ""
        assert response.memory_updated is True

    @pytest.mark.asyncio
    async def test_execute_plan_with_agent(self) -> None:
        """Execute a plan with agent delegation."""
        runtime = create_brain_runtime()
        request = _make_request()
        steps = [
            ExecutionStep(
                step_id="agent",
                step_type=ExecutionStepType.AGENT_DELEGATION,
                target="research-agent",
                params={"task": "find info"},
            ),
            ExecutionStep(
                step_id="llm",
                step_type=ExecutionStepType.LLM_CALL,
                target="gpt-4o",
                params={"prompt": "Summarize", "max_tokens_in": 50, "max_tokens_out": 25},
                depends_on=["agent"],
            ),
        ]
        plan = _make_plan(steps)

        response = await runtime.execute_plan(plan, request)
        assert response.agent_used == "research-agent"

    @pytest.mark.asyncio
    async def test_execute_stream(self) -> None:
        """Execute stream returns async iterator."""
        runtime = create_brain_runtime()
        request = _make_request(stream=True)

        iterator = await runtime.execute_stream(request)
        chunks = []
        async for chunk in iterator:
            chunks.append(chunk)

        assert len(chunks) > 0
        full_content = "".join(chunks)
        assert full_content != ""

    @pytest.mark.asyncio
    async def test_get_session_context_new_session(self) -> None:
        """Get context for a new session returns defaults."""
        runtime = create_brain_runtime()
        ctx = await runtime.get_session_context("new-session")
        assert ctx["session_id"] == "new-session"
        assert "history" in ctx

    @pytest.mark.asyncio
    async def test_session_context_updated_after_execute(self) -> None:
        """Session context includes history after execution."""
        runtime = create_brain_runtime()
        request = _make_request()
        await runtime.execute(request)

        ctx = await runtime.get_session_context("test-session")
        assert len(ctx["history"]) == 1

    @pytest.mark.asyncio
    async def test_metrics_recorded(self) -> None:
        """Metrics are recorded after execution."""
        runtime = create_brain_runtime()
        request = _make_request()
        await runtime.execute(request)

        assert runtime.metrics.plan_count == 1
        assert runtime.metrics.get_success_rate() > 0

    @pytest.mark.asyncio
    async def test_events_emitted(self) -> None:
        """Domain events are emitted during execution."""
        runtime = create_brain_runtime()
        request = _make_request()
        await runtime.execute(request)

        event_types = [type(e).__name__ for e in runtime.events]
        assert "ExecutionStartedEvent" in event_types
        assert "ExecutionCompletedEvent" in event_types

    @pytest.mark.asyncio
    async def test_parallel_steps_execution(self) -> None:
        """Execute parallel independent steps."""
        runtime = create_brain_runtime()
        request = _make_request()
        steps = [
            ExecutionStep(
                step_id="tool-1",
                step_type=ExecutionStepType.TOOL_CALL,
                target="search",
                params={},
            ),
            ExecutionStep(
                step_id="tool-2",
                step_type=ExecutionStepType.TOOL_CALL,
                target="calculator",
                params={},
            ),
            ExecutionStep(
                step_id="llm",
                step_type=ExecutionStepType.LLM_CALL,
                target="gpt-4o",
                params={"prompt": "Combine", "max_tokens_in": 30, "max_tokens_out": 15},
                depends_on=["tool-1", "tool-2"],
            ),
        ]
        plan = _make_plan(steps)

        response = await runtime.execute_plan(plan, request)
        assert response.content != ""

    @pytest.mark.asyncio
    async def test_di_factory(self) -> None:
        """Factory creates a working runtime with custom config."""
        runtime = create_brain_runtime(
            default_model="claude-3",
            default_provider="anthropic",
            max_concurrency=5,
            max_retries=2,
        )
        assert isinstance(runtime, BrainRuntime)

        request = _make_request()
        response = await runtime.execute(request)
        assert isinstance(response, BrainResponse)
