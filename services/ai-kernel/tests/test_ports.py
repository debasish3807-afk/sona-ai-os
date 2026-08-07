"""Unit tests for AI Kernel abstract port interfaces.

Tests verify that port interfaces are correctly defined, enforce
abstractness, and that concrete implementations must satisfy all methods.
"""

from collections.abc import AsyncIterator

import pytest
from application.ports import AIKernelPort, ModelRouterPort, ReasoningEnginePort
from domain.models import (
    KernelRequest,
    KernelResponse,
    ModelConfig,
    ReasoningStrategy,
)


class TestAIKernelPort:
    """Tests for the AIKernelPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify AIKernelPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AIKernelPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = AIKernelPort.__abstractmethods__
        assert "process" in abstract_methods
        assert "stream" in abstract_methods
        assert "select_model" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteKernel(AIKernelPort):
            async def process(self, request: KernelRequest) -> KernelResponse:
                return KernelResponse(
                    content="response",
                    model_used="test-model",
                    tokens_input=1,
                    tokens_output=1,
                    latency_ms=10.0,
                )

            async def stream(self, request: KernelRequest) -> AsyncIterator[str]:
                async def _gen():
                    yield "token"

                return _gen()

            async def select_model(self, request: KernelRequest) -> ModelConfig:
                return ModelConfig(provider="openai", model_id="gpt-4o")

        kernel = ConcreteKernel()
        assert isinstance(kernel, AIKernelPort)

    @pytest.mark.asyncio
    async def test_process_returns_kernel_response(self) -> None:
        """Test that a concrete process() returns the right type."""

        class MockKernel(AIKernelPort):
            async def process(self, request: KernelRequest) -> KernelResponse:
                return KernelResponse(
                    content=f"Echo: {request.content}",
                    model_used="test-model",
                    tokens_input=5,
                    tokens_output=3,
                    latency_ms=50.0,
                )

            async def stream(self, request: KernelRequest) -> AsyncIterator[str]:
                async def _gen():
                    yield "chunk"

                return _gen()

            async def select_model(self, request: KernelRequest) -> ModelConfig:
                return ModelConfig(provider="openai", model_id="gpt-4o")

        kernel = MockKernel()
        req = KernelRequest(session_id="s1", user_id="u1", content="hello")
        result = await kernel.process(req)
        assert result.content == "Echo: hello"
        assert isinstance(result, KernelResponse)


class TestReasoningEnginePort:
    """Tests for the ReasoningEnginePort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify ReasoningEnginePort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ReasoningEnginePort()  # type: ignore[abstract]

    def test_has_reason_method(self) -> None:
        """Verify the reason abstract method is defined."""
        assert "reason" in ReasoningEnginePort.__abstractmethods__

    @pytest.mark.asyncio
    async def test_concrete_reason(self) -> None:
        """Test that a concrete reason() returns a trace list."""

        class MockReasoner(ReasoningEnginePort):
            async def reason(
                self,
                prompt: str,
                context: dict,
                strategy: ReasoningStrategy,
            ) -> list[str]:
                return [
                    f"Analyzing: {prompt}",
                    "Considering context",
                    "Drawing conclusion",
                ]

        reasoner = MockReasoner()
        trace = await reasoner.reason(
            prompt="Why is the sky blue?",
            context={},
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
        )
        assert len(trace) == 3
        assert "Analyzing: Why is the sky blue?" in trace


class TestModelRouterPort:
    """Tests for the ModelRouterPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify ModelRouterPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ModelRouterPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = ModelRouterPort.__abstractmethods__
        assert "route" in abstract_methods
        assert "list_available" in abstract_methods

    @pytest.mark.asyncio
    async def test_concrete_route(self) -> None:
        """Test that a concrete route() returns a ModelConfig."""

        class MockRouter(ModelRouterPort):
            async def route(self, request: KernelRequest) -> ModelConfig:
                return ModelConfig(provider="openai", model_id="gpt-4o")

            async def list_available(self) -> list[ModelConfig]:
                return [
                    ModelConfig(provider="openai", model_id="gpt-4o"),
                    ModelConfig(provider="anthropic", model_id="claude-3"),
                ]

        router = MockRouter()
        req = KernelRequest(session_id="s1", user_id="u1", content="test")
        config = await router.route(req)
        assert config.provider == "openai"
        assert config.model_id == "gpt-4o"

    @pytest.mark.asyncio
    async def test_concrete_list_available(self) -> None:
        """Test that list_available returns a list of configs."""

        class MockRouter(ModelRouterPort):
            async def route(self, request: KernelRequest) -> ModelConfig:
                return ModelConfig(provider="openai", model_id="gpt-4o")

            async def list_available(self) -> list[ModelConfig]:
                return [
                    ModelConfig(provider="openai", model_id="gpt-4o"),
                    ModelConfig(provider="ollama", model_id="llama3"),
                ]

        router = MockRouter()
        models = await router.list_available()
        assert len(models) == 2
        assert all(isinstance(m, ModelConfig) for m in models)
