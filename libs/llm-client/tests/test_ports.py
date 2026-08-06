"""Unit tests for LLM Client abstract port interfaces.

Tests verify that the abstract port interface is correctly defined
and that concrete implementations must implement all abstract methods.
"""

import pytest

from sona_llm.models import CompletionResult, LLMProviderConfig, Message, ProviderType
from sona_llm.ports import LLMClientPort


class TestLLMClientPort:
    """Tests for the LLMClientPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify LLMClientPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMClientPort()  # type: ignore[abstract]

    def test_concrete_implementation_requires_all_methods(self) -> None:
        """Verify that a partial implementation raises TypeError."""

        class PartialImpl(LLMClientPort):
            async def chat_completion(self, messages, model_config):
                return CompletionResult("", "", 0, 0, 0.0)

            # Missing: stream_completion, generate_embedding, generate_embeddings_batch

        with pytest.raises(TypeError):
            PartialImpl()  # type: ignore[abstract]

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""
        from typing import AsyncIterator

        class ConcreteImpl(LLMClientPort):
            async def chat_completion(
                self, messages: list[Message], model_config: LLMProviderConfig
            ) -> CompletionResult:
                return CompletionResult(
                    content="test",
                    model=model_config.model_id,
                    tokens_input=len(messages),
                    tokens_output=1,
                    latency_ms=10.0,
                )

            async def stream_completion(
                self, messages: list[Message], model_config: LLMProviderConfig
            ) -> AsyncIterator[str]:
                async def _gen():
                    yield "test"

                return _gen()

            async def generate_embedding(self, text: str) -> list[float]:
                return [0.1, 0.2, 0.3]

            async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
                return [[0.1, 0.2, 0.3] for _ in texts]

        impl = ConcreteImpl()
        assert isinstance(impl, LLMClientPort)

    def test_implementation_has_correct_method_names(self) -> None:
        """Verify all required abstract methods are defined on the port."""
        abstract_methods = LLMClientPort.__abstractmethods__
        assert "chat_completion" in abstract_methods
        assert "stream_completion" in abstract_methods
        assert "generate_embedding" in abstract_methods
        assert "generate_embeddings_batch" in abstract_methods

    @pytest.mark.asyncio
    async def test_concrete_chat_completion(self) -> None:
        """Test that a concrete implementation's chat_completion works."""
        from typing import AsyncIterator

        class MockLLMClient(LLMClientPort):
            async def chat_completion(
                self, messages: list[Message], model_config: LLMProviderConfig
            ) -> CompletionResult:
                last_msg = messages[-1].content if messages else ""
                return CompletionResult(
                    content=f"Echo: {last_msg}",
                    model=model_config.model_id,
                    tokens_input=10,
                    tokens_output=5,
                    latency_ms=50.0,
                )

            async def stream_completion(
                self, messages: list[Message], model_config: LLMProviderConfig
            ) -> AsyncIterator[str]:
                async def _gen():
                    yield "test"

                return _gen()

            async def generate_embedding(self, text: str) -> list[float]:
                return [0.5] * 128

            async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
                return [[0.5] * 128 for _ in texts]

        client = MockLLMClient()
        config = LLMProviderConfig(provider=ProviderType.OPENAI, model_id="gpt-4o")
        messages = [Message(role="user", content="hello")]

        result = await client.chat_completion(messages, config)
        assert result.content == "Echo: hello"
        assert result.model == "gpt-4o"
        assert result.tokens_input == 10
        assert result.tokens_output == 5

    @pytest.mark.asyncio
    async def test_concrete_generate_embedding(self) -> None:
        """Test that a concrete implementation's generate_embedding works."""
        from typing import AsyncIterator

        class MockLLMClient(LLMClientPort):
            async def chat_completion(self, messages, model_config):
                return CompletionResult("", "", 0, 0, 0.0)

            async def stream_completion(self, messages, model_config) -> AsyncIterator[str]:
                async def _gen():
                    yield ""

                return _gen()

            async def generate_embedding(self, text: str) -> list[float]:
                # Return a fixed-size embedding
                return [float(i) / 100 for i in range(1536)]

            async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
                return [await self.generate_embedding(t) for t in texts]

        client = MockLLMClient()
        embedding = await client.generate_embedding("Hello world")
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(v, float) for v in embedding)

    @pytest.mark.asyncio
    async def test_concrete_generate_embeddings_batch(self) -> None:
        """Test that batch embedding returns one vector per input."""
        from typing import AsyncIterator

        class MockLLMClient(LLMClientPort):
            async def chat_completion(self, messages, model_config):
                return CompletionResult("", "", 0, 0, 0.0)

            async def stream_completion(self, messages, model_config) -> AsyncIterator[str]:
                async def _gen():
                    yield ""

                return _gen()

            async def generate_embedding(self, text: str) -> list[float]:
                return [0.1] * 10

            async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
                return [await self.generate_embedding(t) for t in texts]

        client = MockLLMClient()
        texts = ["first", "second", "third"]
        embeddings = await client.generate_embeddings_batch(texts)
        assert len(embeddings) == 3
        assert all(len(e) == 10 for e in embeddings)
