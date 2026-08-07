"""Individual step executor for Brain OS.

Executes a single ExecutionStep based on its type, handling timeouts,
latency measurement, and result recording.
"""

import asyncio
import time
from typing import Any

import structlog

from sona_brain.domain.execution import StepResult, StepState
from sona_thalamus.domain.execution_plan import ExecutionStep, ExecutionStepType

logger = structlog.get_logger()


class LLMCallHandler:
    """Handles LLM_CALL step execution.

    Simulates or delegates to the AI Kernel for inference.
    In production, this would call the AI Kernel's process() method.
    """

    def __init__(self, model_id: str = "llama3.2", provider: str = "ollama") -> None:
        """Initialize with model configuration.

        Args:
            model_id: The model identifier to use for LLM calls.
            provider: The provider to route calls through.
        """
        self._model_id = model_id
        self._provider = provider

    async def execute(self, step: ExecutionStep, context: dict[str, Any]) -> dict[str, Any]:
        """Execute an LLM call step.

        Args:
            step: The execution step definition.
            context: Execution context with prior step outputs.

        Returns:
            Dictionary with response content and token usage.
        """
        prompt = step.params.get("prompt", "")
        messages = step.params.get("messages", [])
        temperature = step.params.get("temperature", 0.7)

        # In production, this calls AI Kernel process()
        # For now, generate a structured response
        content = f"Response to: {prompt}" if prompt else "Generated response"
        if messages:
            last_msg = messages[-1].get("content", "") if messages else ""
            content = f"Response to: {last_msg}"

        return {
            "content": content,
            "model": step.target or self._model_id,
            "provider": self._provider,
            "tokens_in": step.params.get("max_tokens_in", 100),
            "tokens_out": step.params.get("max_tokens_out", 50),
            "temperature": temperature,
        }


class ToolCallHandler:
    """Handles TOOL_CALL step execution."""

    async def execute(self, step: ExecutionStep, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool call step.

        Args:
            step: The execution step definition.
            context: Execution context with prior step outputs.

        Returns:
            Dictionary with tool execution results.
        """
        tool_name = step.target
        tool_params = step.params

        logger.info("tool_call_executing", tool=tool_name, params=tool_params)

        return {
            "tool": tool_name,
            "result": f"Tool '{tool_name}' executed successfully",
            "params_used": tool_params,
        }


class AgentDelegationHandler:
    """Handles AGENT_DELEGATION step execution."""

    async def execute(self, step: ExecutionStep, context: dict[str, Any]) -> dict[str, Any]:
        """Execute an agent delegation step.

        Args:
            step: The execution step definition.
            context: Execution context with prior step outputs.

        Returns:
            Dictionary with agent execution results.
        """
        agent_name = step.target
        task = step.params.get("task", "")

        logger.info("agent_delegation", agent=agent_name, task=task)

        return {
            "agent": agent_name,
            "result": f"Agent '{agent_name}' completed task: {task}",
            "delegated": True,
        }


class MemoryRetrievalHandler:
    """Handles MEMORY_RETRIEVAL step execution."""

    async def execute(self, step: ExecutionStep, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a memory retrieval step.

        Args:
            step: The execution step definition.
            context: Execution context with prior step outputs.

        Returns:
            Dictionary with retrieved memory data.
        """
        query = step.params.get("query", "")
        limit = step.params.get("limit", 5)

        logger.info("memory_retrieval", query=query, limit=limit)

        return {
            "memories": [],
            "query": query,
            "count": 0,
        }


class KnowledgeQueryHandler:
    """Handles KNOWLEDGE_QUERY step execution."""

    async def execute(self, step: ExecutionStep, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a knowledge query step.

        Args:
            step: The execution step definition.
            context: Execution context with prior step outputs.

        Returns:
            Dictionary with knowledge query results.
        """
        query = step.params.get("query", "")
        sources = step.params.get("sources", [])

        logger.info("knowledge_query", query=query, sources=sources)

        return {
            "results": [],
            "query": query,
            "sources_searched": sources,
        }


class StepExecutor:
    """Executes individual steps based on their type.

    Routes step execution to the appropriate handler based on the
    step type, manages timeouts, and records execution metrics.
    """

    def __init__(
        self,
        model_id: str = "llama3.2",
        provider: str = "ollama",
    ) -> None:
        """Initialize step executor with default model configuration.

        Args:
            model_id: Default model identifier for LLM calls.
            provider: Default provider for LLM calls.
        """
        self._llm_handler = LLMCallHandler(model_id=model_id, provider=provider)
        self._tool_handler = ToolCallHandler()
        self._agent_handler = AgentDelegationHandler()
        self._memory_handler = MemoryRetrievalHandler()
        self._knowledge_handler = KnowledgeQueryHandler()

    async def execute_step(
        self,
        step: ExecutionStep,
        context: dict[str, Any] | None = None,
    ) -> StepResult:
        """Execute a single step with timeout handling and latency recording.

        Args:
            step: The execution step to execute.
            context: Optional execution context with prior results.

        Returns:
            A StepResult with the execution outcome.
        """
        context = context or {}
        start_time = time.perf_counter()

        try:
            output = await asyncio.wait_for(
                self._dispatch(step, context),
                timeout=step.timeout_seconds,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            return StepResult(
                step_id=step.step_id,
                state=StepState.COMPLETED,
                output=output,
                latency_ms=elapsed_ms,
            )
        except asyncio.TimeoutError:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = f"Step timed out after {step.timeout_seconds}s"
            logger.warning(
                "step_timeout",
                step_id=step.step_id,
                timeout=step.timeout_seconds,
            )
            return StepResult(
                step_id=step.step_id,
                state=StepState.FAILED,
                error=error_msg,
                latency_ms=elapsed_ms,
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.error(
                "step_execution_error",
                step_id=step.step_id,
                error=error_msg,
            )
            return StepResult(
                step_id=step.step_id,
                state=StepState.FAILED,
                error=error_msg,
                latency_ms=elapsed_ms,
            )

    async def _dispatch(
        self,
        step: ExecutionStep,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Route step execution to the appropriate handler.

        Args:
            step: The execution step to dispatch.
            context: Execution context.

        Returns:
            Handler output dictionary.

        Raises:
            ValueError: If step type is not supported.
        """
        match step.step_type:
            case ExecutionStepType.LLM_CALL:
                return await self._llm_handler.execute(step, context)
            case ExecutionStepType.TOOL_CALL:
                return await self._tool_handler.execute(step, context)
            case ExecutionStepType.AGENT_DELEGATION:
                return await self._agent_handler.execute(step, context)
            case ExecutionStepType.MEMORY_RETRIEVAL:
                return await self._memory_handler.execute(step, context)
            case ExecutionStepType.KNOWLEDGE_QUERY:
                return await self._knowledge_handler.execute(step, context)
            case ExecutionStepType.PARALLEL_GROUP:
                # Parallel groups are handled by the scheduler, not individual execution
                return {"group": step.step_id, "handled": True}
            case ExecutionStepType.CONDITIONAL:
                # Conditional steps evaluate their condition and return skip/proceed
                condition = step.params.get("condition", True)
                return {"condition_met": bool(condition), "evaluated": True}
            case _:
                raise ValueError(f"Unsupported step type: {step.step_type}")
