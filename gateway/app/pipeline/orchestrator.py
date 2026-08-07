"""End-to-end pipeline orchestrator connecting all services.

Orchestrates the full request lifecycle:
1. Create context with IDs
2. Retrieve conversation history from Memory OS
3. Retrieve relevant memories from Memory OS
4. Route through THALAMUS to get ExecutionPlan
5. Execute plan via Brain OS
6. Store conversation in Memory OS
7. Return PipelineResult
"""

import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import structlog

from app.pipeline.context_injector import ContextInjector
from app.pipeline.error_handler import PipelineErrorHandler
from app.pipeline.metrics import MetricsCollector
from app.pipeline.session import SessionManager
from sona_brain.domain.models import BrainRequest, BrainResponse
from sona_brain.infrastructure.brain_runtime import BrainRuntime
from sona_memory.domain.models import MemoryEntry, MemoryType
from sona_memory.infrastructure.memory_manager import MemoryManager
from sona_thalamus.infrastructure.routing_engine import RoutingEngine

logger = structlog.get_logger()


@dataclass
class PipelineContext:
    """Context for a single pipeline execution."""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    user_id: str = ""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    memory_context: list[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""

    content: str
    model_used: str
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: float = 0.0
    intent: str = ""
    memory_updated: bool = False


class PipelineOrchestrator:
    """Orchestrates the full request pipeline across all services.

    Connects THALAMUS (routing), Brain OS (execution), Memory OS (context),
    and provides session management, error handling, and metrics collection.
    """

    def __init__(
        self,
        thalamus: RoutingEngine,
        brain: BrainRuntime,
        memory: MemoryManager,
        kernel: object | None = None,
    ) -> None:
        """Initialize the pipeline orchestrator.

        Args:
            thalamus: The THALAMUS routing engine.
            brain: The Brain OS runtime.
            memory: The Memory OS manager.
            kernel: Optional AI Kernel reference (wired internally by Brain).
        """
        self._thalamus = thalamus
        self._brain = brain
        self._memory = memory
        self._kernel = kernel
        self._session_manager = SessionManager()
        self._context_injector = ContextInjector()
        self._error_handler = PipelineErrorHandler()

    async def execute(
        self,
        messages: list[dict[str, str]],
        user_id: str,
        session_id: str,
        model: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> PipelineResult:
        """Execute the full pipeline for a chat completion request.

        Flows through memory retrieval, context injection, THALAMUS routing,
        Brain OS execution, and memory storage.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            user_id: The requesting user's ID.
            session_id: The session ID for conversation tracking.
            model: Requested model name.
            temperature: Sampling temperature.
            max_tokens: Maximum output tokens.

        Returns:
            PipelineResult with generated content and metadata.
        """
        # Step 1: Create context
        ctx = PipelineContext(
            session_id=session_id,
            user_id=user_id,
        )
        metrics = MetricsCollector(request_id=ctx.request_id)

        log = logger.bind(
            request_id=ctx.request_id,
            session_id=ctx.session_id,
            user_id=ctx.user_id,
            trace_id=ctx.trace_id,
        )
        log.info("pipeline_execute_start", model=model)

        # Step 2: Ensure session exists
        self._session_manager.get_or_create_session(session_id, user_id)

        # Step 3: Retrieve memory context (non-blocking on failure)
        enriched_messages = messages
        try:
            async with metrics.track_stage("memory_retrieval"):
                enriched_messages = await self._context_injector.inject(
                    messages=messages,
                    user_id=user_id,
                    session_id=session_id,
                    memory=self._memory,
                )
        except Exception as e:
            await self._error_handler.handle_memory_failure(e, ctx.request_id)

        # Step 4: Route through THALAMUS
        intent = ""
        try:
            async with metrics.track_stage("thalamus_routing"):
                plan = await self._thalamus.create_execution_plan(
                    {
                        "content": self._extract_last_user_content(messages),
                        "context": {"model": model, "temperature": temperature},
                        "session_id": session_id,
                    }
                )
                intent = plan.intent
        except Exception as e:
            await self._error_handler.handle_routing_failure(e, ctx.request_id)

        # Step 5: Execute via Brain OS
        try:
            async with metrics.track_stage("brain_execution"):
                brain_request = BrainRequest(
                    session_id=session_id,
                    user_id=user_id,
                    messages=enriched_messages,
                    stream=False,
                )
                brain_response: BrainResponse = await self._brain.execute(brain_request)
        except Exception as e:
            log.error("pipeline_brain_failure", error=str(e))
            fallback = await self._error_handler.handle_provider_failure(
                e, ctx.request_id, messages
            )
            elapsed_ms = (time.time() - ctx.start_time) * 1000
            return PipelineResult(
                content=fallback or PipelineErrorHandler.FALLBACK_CONTENT,
                model_used=model,
                latency_ms=elapsed_ms,
                intent=intent,
            )

        # Step 6: Store conversation in Memory OS (non-blocking on failure)
        memory_updated = False
        try:
            async with metrics.track_stage("memory_update"):
                memory_updated = await self._store_conversation(
                    user_id=user_id,
                    session_id=session_id,
                    messages=messages,
                    response_content=brain_response.content,
                )
        except Exception as e:
            await self._error_handler.handle_memory_failure(e, ctx.request_id)

        # Step 7: Build result
        tokens_in = brain_response.tokens.get("input", 0)
        tokens_out = brain_response.tokens.get("output", 0)
        metrics.record_tokens(tokens_in + tokens_out)
        metrics.finalize()

        elapsed_ms = (time.time() - ctx.start_time) * 1000
        result = PipelineResult(
            content=brain_response.content,
            model_used=brain_response.model_used,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            latency_ms=elapsed_ms,
            intent=intent,
            memory_updated=memory_updated,
        )

        log.info(
            "pipeline_execute_complete",
            model_used=result.model_used,
            tokens_total=tokens_in + tokens_out,
            latency_ms=round(elapsed_ms, 2),
            intent=intent,
        )

        return result

    async def execute_stream(
        self,
        messages: list[dict[str, str]],
        user_id: str,
        session_id: str,
        model: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Execute the pipeline with streaming response.

        Similar to execute() but yields tokens as they are generated.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            user_id: The requesting user's ID.
            session_id: The session ID for conversation tracking.
            model: Requested model name.
            temperature: Sampling temperature.
            max_tokens: Maximum output tokens.

        Yields:
            String tokens as they are generated.
        """
        ctx = PipelineContext(
            session_id=session_id,
            user_id=user_id,
        )

        log = logger.bind(
            request_id=ctx.request_id,
            session_id=ctx.session_id,
            user_id=ctx.user_id,
        )
        log.info("pipeline_stream_start", model=model)

        # Ensure session
        self._session_manager.get_or_create_session(session_id, user_id)

        # Retrieve memory context (non-blocking)
        enriched_messages = messages
        try:
            enriched_messages = await self._context_injector.inject(
                messages=messages,
                user_id=user_id,
                session_id=session_id,
                memory=self._memory,
            )
        except Exception as e:
            await self._error_handler.handle_memory_failure(e, ctx.request_id)

        # Route through THALAMUS (non-blocking on failure)
        try:
            await self._thalamus.create_execution_plan(
                {
                    "content": self._extract_last_user_content(messages),
                    "context": {"model": model, "temperature": temperature},
                    "session_id": session_id,
                }
            )
        except Exception as e:
            await self._error_handler.handle_routing_failure(e, ctx.request_id)

        # Execute via Brain OS streaming
        brain_request = BrainRequest(
            session_id=session_id,
            user_id=user_id,
            messages=enriched_messages,
            stream=True,
        )

        try:
            stream_iter = await self._brain.execute_stream(brain_request)
            collected_content: list[str] = []

            async for token in stream_iter:
                collected_content.append(token)
                yield token

            # Store conversation after streaming completes
            full_response = "".join(collected_content)
            try:
                await self._store_conversation(
                    user_id=user_id,
                    session_id=session_id,
                    messages=messages,
                    response_content=full_response,
                )
            except Exception as e:
                await self._error_handler.handle_memory_failure(e, ctx.request_id)

        except Exception as e:
            log.error("pipeline_stream_failure", error=str(e))
            yield PipelineErrorHandler.FALLBACK_CONTENT

    async def _store_conversation(
        self,
        user_id: str,
        session_id: str,
        messages: list[dict[str, str]],
        response_content: str,
    ) -> bool:
        """Store the conversation exchange in Memory OS.

        Args:
            user_id: The user ID.
            session_id: The session ID.
            messages: The user's messages.
            response_content: The assistant's response.

        Returns:
            True if storage succeeded, False otherwise.
        """
        # Store the last user message
        last_user_msg = self._extract_last_user_content(messages)
        if last_user_msg:
            user_entry = MemoryEntry(
                id=str(uuid.uuid4()),
                memory_type=MemoryType.SHORT_TERM,
                content=last_user_msg,
                metadata={"session_id": session_id, "role": "user"},
                importance=0.5,
            )
            await self._memory.store(user_id, user_entry)

        # Store the assistant response
        response_entry = MemoryEntry(
            id=str(uuid.uuid4()),
            memory_type=MemoryType.SHORT_TERM,
            content=response_content,
            metadata={"session_id": session_id, "role": "assistant"},
            importance=0.5,
        )
        await self._memory.store(user_id, response_entry)

        return True

    @staticmethod
    def _extract_last_user_content(messages: list[dict[str, str]]) -> str:
        """Extract the content of the last user message.

        Args:
            messages: List of message dicts.

        Returns:
            The content string of the last user message, or empty string.
        """
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return ""
