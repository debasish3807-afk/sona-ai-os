"""Unit tests for Brain OS abstract port interfaces.

Tests verify that port interfaces are correctly defined, enforce
abstractness, and that concrete implementations must satisfy all methods.
"""

from collections.abc import AsyncIterator

import pytest
from application.ports import BrainOrchestratorPort, PipelineStagePort
from domain.models import BrainRequest, BrainResponse


class TestBrainOrchestratorPort:
    """Tests for the BrainOrchestratorPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify BrainOrchestratorPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BrainOrchestratorPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = BrainOrchestratorPort.__abstractmethods__
        assert "execute" in abstract_methods
        assert "execute_stream" in abstract_methods
        assert "get_session_context" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteOrchestrator(BrainOrchestratorPort):
            async def execute(self, request: BrainRequest) -> BrainResponse:
                return BrainResponse(
                    content="response",
                    session_id=request.session_id,
                    model_used="test-model",
                    tokens={"input": 1, "output": 1},
                    latency_ms=10.0,
                )

            async def execute_stream(self, request: BrainRequest) -> AsyncIterator[str]:
                async def _gen():
                    yield "token"

                return _gen()

            async def get_session_context(self, session_id: str) -> dict:
                return {"session_id": session_id, "history": []}

        orchestrator = ConcreteOrchestrator()
        assert isinstance(orchestrator, BrainOrchestratorPort)

    def test_partial_implementation_raises(self) -> None:
        """Verify partial implementations cannot be instantiated."""

        class PartialOrchestrator(BrainOrchestratorPort):
            async def execute(self, request: BrainRequest) -> BrainResponse:
                return BrainResponse(
                    content="response",
                    session_id=request.session_id,
                    model_used="test-model",
                    tokens={"input": 1, "output": 1},
                    latency_ms=10.0,
                )

        with pytest.raises(TypeError):
            PartialOrchestrator()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_execute_returns_brain_response(self) -> None:
        """Test that a concrete execute() returns the right type."""

        class MockOrchestrator(BrainOrchestratorPort):
            async def execute(self, request: BrainRequest) -> BrainResponse:
                return BrainResponse(
                    content=f"Echo: {request.messages[-1]['content']}",
                    session_id=request.session_id,
                    model_used="gpt-4o",
                    tokens={"input": 5, "output": 3},
                    latency_ms=50.0,
                    memory_updated=True,
                )

            async def execute_stream(self, request: BrainRequest) -> AsyncIterator[str]:
                async def _gen():
                    yield "chunk"

                return _gen()

            async def get_session_context(self, session_id: str) -> dict:
                return {"session_id": session_id}

        orchestrator = MockOrchestrator()
        req = BrainRequest(
            session_id="s1",
            user_id="u1",
            messages=[{"role": "user", "content": "hello"}],
        )
        result = await orchestrator.execute(req)
        assert result.content == "Echo: hello"
        assert isinstance(result, BrainResponse)
        assert result.memory_updated is True

    @pytest.mark.asyncio
    async def test_get_session_context_returns_dict(self) -> None:
        """Test that get_session_context returns session data."""

        class MockOrchestrator(BrainOrchestratorPort):
            async def execute(self, request: BrainRequest) -> BrainResponse:
                return BrainResponse(
                    content="r",
                    session_id="s1",
                    model_used="m",
                    tokens={"input": 0, "output": 0},
                    latency_ms=0.0,
                )

            async def execute_stream(self, request: BrainRequest) -> AsyncIterator[str]:
                async def _gen():
                    yield "x"

                return _gen()

            async def get_session_context(self, session_id: str) -> dict:
                return {
                    "session_id": session_id,
                    "history": ["msg1", "msg2"],
                    "preferences": {"model": "gpt-4o"},
                }

        orchestrator = MockOrchestrator()
        ctx = await orchestrator.get_session_context("sess-abc")
        assert ctx["session_id"] == "sess-abc"
        assert len(ctx["history"]) == 2


class TestPipelineStagePort:
    """Tests for the PipelineStagePort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify PipelineStagePort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            PipelineStagePort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = PipelineStagePort.__abstractmethods__
        assert "execute" in abstract_methods
        assert "should_skip" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class MemoryRetrievalStage(PipelineStagePort):
            async def execute(self, context: dict) -> dict:
                context["memory"] = ["recalled data"]
                return context

            def should_skip(self, context: dict) -> bool:
                return context.get("skip_memory", False)

        stage = MemoryRetrievalStage()
        assert isinstance(stage, PipelineStagePort)

    @pytest.mark.asyncio
    async def test_execute_enriches_context(self) -> None:
        """Test that a concrete execute() enriches the pipeline context."""

        class ModelSelectionStage(PipelineStagePort):
            async def execute(self, context: dict) -> dict:
                context["selected_model"] = "gpt-4o"
                context["model_config"] = {"temperature": 0.7}
                return context

            def should_skip(self, context: dict) -> bool:
                return "model_override" in context

        stage = ModelSelectionStage()
        result = await stage.execute({"user_id": "u1", "content": "hello"})
        assert result["selected_model"] == "gpt-4o"
        assert result["model_config"]["temperature"] == 0.7
        # Original context preserved
        assert result["user_id"] == "u1"

    def test_should_skip_returns_true(self) -> None:
        """Test that should_skip can signal stage should be bypassed."""

        class OptionalStage(PipelineStagePort):
            async def execute(self, context: dict) -> dict:
                return context

            def should_skip(self, context: dict) -> bool:
                return not context.get("feature_enabled", False)

        stage = OptionalStage()
        assert stage.should_skip({"feature_enabled": False}) is True
        assert stage.should_skip({}) is True

    def test_should_skip_returns_false(self) -> None:
        """Test that should_skip can signal stage should execute."""

        class RequiredStage(PipelineStagePort):
            async def execute(self, context: dict) -> dict:
                return context

            def should_skip(self, context: dict) -> bool:
                return False

        stage = RequiredStage()
        assert stage.should_skip({"any": "context"}) is False
