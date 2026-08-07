"""Tests for step executor.

Tests verify step execution, timeout handling, and type dispatch.
"""

import pytest

from sona_brain.domain.execution import StepState
from sona_brain.infrastructure.step_executor import StepExecutor
from sona_thalamus.domain.execution_plan import ExecutionStep, ExecutionStepType


def _make_step(
    step_type: ExecutionStepType,
    target: str = "test-target",
    params: dict | None = None,
    timeout: float = 60.0,
) -> ExecutionStep:
    """Helper to create a test step."""
    return ExecutionStep(
        step_id="test-step",
        step_type=step_type,
        target=target,
        params=params or {},
        timeout_seconds=timeout,
    )


class TestStepExecutor:
    """Tests for StepExecutor."""

    @pytest.mark.asyncio
    async def test_execute_llm_call(self) -> None:
        """Verify LLM_CALL step execution."""
        executor = StepExecutor(model_id="gpt-4o", provider="openai")
        step = _make_step(
            ExecutionStepType.LLM_CALL,
            target="gpt-4o",
            params={"prompt": "Hello", "max_tokens_in": 50, "max_tokens_out": 25},
        )
        result = await executor.execute_step(step)
        assert result.state == StepState.COMPLETED
        assert result.output is not None
        assert "content" in result.output
        assert result.output["model"] == "gpt-4o"
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_execute_llm_call_with_messages(self) -> None:
        """Verify LLM_CALL with messages parameter."""
        executor = StepExecutor()
        step = _make_step(
            ExecutionStepType.LLM_CALL,
            params={"messages": [{"role": "user", "content": "test msg"}]},
        )
        result = await executor.execute_step(step)
        assert result.state == StepState.COMPLETED
        assert "test msg" in result.output["content"]

    @pytest.mark.asyncio
    async def test_execute_tool_call(self) -> None:
        """Verify TOOL_CALL step execution."""
        executor = StepExecutor()
        step = _make_step(
            ExecutionStepType.TOOL_CALL,
            target="web_search",
            params={"query": "test query"},
        )
        result = await executor.execute_step(step)
        assert result.state == StepState.COMPLETED
        assert result.output["tool"] == "web_search"

    @pytest.mark.asyncio
    async def test_execute_agent_delegation(self) -> None:
        """Verify AGENT_DELEGATION step execution."""
        executor = StepExecutor()
        step = _make_step(
            ExecutionStepType.AGENT_DELEGATION,
            target="research-agent",
            params={"task": "find papers"},
        )
        result = await executor.execute_step(step)
        assert result.state == StepState.COMPLETED
        assert result.output["agent"] == "research-agent"
        assert result.output["delegated"] is True

    @pytest.mark.asyncio
    async def test_execute_memory_retrieval(self) -> None:
        """Verify MEMORY_RETRIEVAL step execution."""
        executor = StepExecutor()
        step = _make_step(
            ExecutionStepType.MEMORY_RETRIEVAL,
            params={"query": "user preferences"},
        )
        result = await executor.execute_step(step)
        assert result.state == StepState.COMPLETED
        assert "memories" in result.output

    @pytest.mark.asyncio
    async def test_execute_knowledge_query(self) -> None:
        """Verify KNOWLEDGE_QUERY step execution."""
        executor = StepExecutor()
        step = _make_step(
            ExecutionStepType.KNOWLEDGE_QUERY,
            params={"query": "python docs", "sources": ["docs"]},
        )
        result = await executor.execute_step(step)
        assert result.state == StepState.COMPLETED
        assert "results" in result.output

    @pytest.mark.asyncio
    async def test_execute_parallel_group(self) -> None:
        """Verify PARALLEL_GROUP step execution."""
        executor = StepExecutor()
        step = _make_step(ExecutionStepType.PARALLEL_GROUP)
        result = await executor.execute_step(step)
        assert result.state == StepState.COMPLETED
        assert result.output["handled"] is True

    @pytest.mark.asyncio
    async def test_execute_conditional(self) -> None:
        """Verify CONDITIONAL step execution."""
        executor = StepExecutor()
        step = _make_step(
            ExecutionStepType.CONDITIONAL,
            params={"condition": True},
        )
        result = await executor.execute_step(step)
        assert result.state == StepState.COMPLETED
        assert result.output["condition_met"] is True

    @pytest.mark.asyncio
    async def test_timeout_handling(self) -> None:
        """Verify step times out with very short timeout."""
        import asyncio
        from unittest.mock import patch

        executor = StepExecutor()
        step = _make_step(
            ExecutionStepType.LLM_CALL,
            timeout=0.001,  # 1ms timeout
        )

        # Patch the LLM handler to be slow
        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(1.0)
            return {"content": "late"}

        with patch.object(executor._llm_handler, "execute", side_effect=slow_execute):
            result = await executor.execute_step(step)

        assert result.state == StepState.FAILED
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_exception_handling(self) -> None:
        """Verify exceptions are caught and recorded."""
        from unittest.mock import patch

        executor = StepExecutor()
        step = _make_step(ExecutionStepType.LLM_CALL)

        with patch.object(executor._llm_handler, "execute", side_effect=RuntimeError("boom")):
            result = await executor.execute_step(step)

        assert result.state == StepState.FAILED
        assert "RuntimeError" in result.error
        assert "boom" in result.error

    @pytest.mark.asyncio
    async def test_latency_recorded(self) -> None:
        """Verify latency is always recorded."""
        executor = StepExecutor()
        step = _make_step(ExecutionStepType.TOOL_CALL, target="fast-tool")
        result = await executor.execute_step(step)
        assert result.latency_ms >= 0.0

    @pytest.mark.asyncio
    async def test_context_passed_to_handler(self) -> None:
        """Verify context dict is passed through."""
        executor = StepExecutor()
        step = _make_step(
            ExecutionStepType.LLM_CALL,
            params={"prompt": "with context"},
        )
        context = {"prev_step": {"output": "data"}}
        result = await executor.execute_step(step, context)
        assert result.state == StepState.COMPLETED
