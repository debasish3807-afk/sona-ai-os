"""Phase 18.0 comprehensive tests for Sona AI OS."""

from __future__ import annotations

import pytest

from agents.agent_intelligence import AgentIntelligence
from agents.shared_memory import SharedAgentMemory
from agents.strategy_learner import StrategyLearner
from ai.claude_provider import ClaudeProvider
from ai.gemini_provider import GeminiProvider
from ai.ollama_provider import OllamaProvider
from ai.openai_provider import OpenAIProvider
from ai.openrouter_provider import OpenRouterProvider
from ai.provider_manager import ProviderManager
from ai.retry import AIRetryPolicy
from ai.schemas import AIMessage, AIRequest, AIResponse, ProviderConfig, ProviderStatus, TokenUsage
from ai.token_tracker import TokenTracker
from ai.unified_ai import UnifiedAI
from knowledge import KnowledgeEngine
from knowledge.chunking import ChunkingEngine
from knowledge.document_processor import DocumentProcessor
from knowledge.knowledge_search import KnowledgeSearch
from knowledge.knowledge_store import KnowledgeStore
from knowledge.schemas import Chunk, Citation, Document, DocumentType, SearchResult
from memory.embeddings import SimpleEmbedding
from memory.semantic_search import SemanticSearch
from memory.vector_store import VectorStore
from observability.dashboards import DashboardConfig
from observability.otel import OTelExporter
from observability.prometheus import Counter, Gauge, Histogram, PrometheusRegistry
from security.compliance import ComplianceAuditor
from security.encryption import EncryptionAtRest, TransitEncryption
from security.oidc import OIDCConfig, OIDCProvider
from security.vault import VaultClient
from web import WebSearch
from web.search_engine import SearchEngine
from web.url_reader import URLReader


class TestAISchemas:
    """Tests for AI data schemas."""

    def test_ai_message_creation(self):
        msg = AIMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.name == ""

    def test_ai_message_with_name(self):
        msg = AIMessage(role="assistant", content="Hi", name="sona")
        assert msg.name == "sona"

    def test_ai_request_defaults(self):
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        assert req.temperature == 0.7
        assert req.max_tokens == 4096
        assert req.stream is False
        assert req.model == ""
        assert req.provider == ""

    def test_ai_request_custom_params(self):
        req = AIRequest(
            messages=[AIMessage(role="user", content="x")],
            model="gpt-4o",
            temperature=0.2,
            max_tokens=1024,
        )
        assert req.model == "gpt-4o"
        assert req.temperature == 0.2
        assert req.max_tokens == 1024

    def test_ai_request_stream_flag(self):
        req = AIRequest(messages=[], stream=True)
        assert req.stream is True

    def test_ai_response_creation(self):
        resp = AIResponse(content="answer", model="gpt-4o", provider="openai")
        assert resp.content == "answer"
        assert resp.model == "gpt-4o"
        assert resp.provider == "openai"

    def test_ai_response_defaults(self):
        resp = AIResponse(content="x", model="m", provider="p")
        assert resp.tokens_used == 0
        assert resp.latency_ms == 0.0
        assert resp.finish_reason == "stop"
        assert resp.tool_calls == []
        assert resp.response_id != ""

    def test_token_usage_defaults(self):
        usage = TokenUsage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0
        assert usage.cost_usd == 0.0

    def test_token_usage_custom(self):
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=0.01)
        assert usage.total_tokens == 150

    def test_provider_config_defaults(self):
        cfg = ProviderConfig(name="test")
        assert cfg.api_key == ""
        assert cfg.models == []
        assert cfg.max_retries == 3
        assert cfg.timeout_seconds == 60.0
        assert cfg.enabled is True

    def test_provider_config_with_models(self):
        cfg = ProviderConfig(name="test", models=["model1", "model2"])
        assert len(cfg.models) == 2

    def test_provider_status_values(self):
        assert ProviderStatus.HEALTHY == "healthy"
        assert ProviderStatus.DEGRADED == "degraded"
        assert ProviderStatus.UNAVAILABLE == "unavailable"
        assert ProviderStatus.UNKNOWN == "unknown"


class TestOpenAIProvider:
    """Tests for OpenAI provider."""

    def test_create_default(self):
        provider = OpenAIProvider()
        assert provider.name == "openai"

    def test_create_with_config(self):
        cfg = ProviderConfig(name="openai", models=["gpt-4o"])
        provider = OpenAIProvider(config=cfg)
        assert provider.name == "openai"
        assert "gpt-4o" in provider.available_models

    def test_default_models(self):
        provider = OpenAIProvider()
        assert "gpt-4o" in provider.available_models
        assert len(provider.available_models) >= 3

    @pytest.mark.asyncio
    async def test_complete_returns_response(self):
        provider = OpenAIProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="Hello world")])
        resp = await provider.complete(req)
        assert isinstance(resp, AIResponse)
        assert resp.provider == "openai"

    @pytest.mark.asyncio
    async def test_complete_uses_default_model(self):
        provider = OpenAIProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        resp = await provider.complete(req)
        assert resp.model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_complete_uses_specified_model(self):
        provider = OpenAIProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")], model="gpt-4-turbo")
        resp = await provider.complete(req)
        assert resp.model == "gpt-4-turbo"

    @pytest.mark.asyncio
    async def test_complete_increments_request_count(self):
        provider = OpenAIProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="hi")])
        await provider.complete(req)
        await provider.complete(req)
        assert provider._request_count == 2

    @pytest.mark.asyncio
    async def test_complete_has_latency(self):
        provider = OpenAIProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="hi")])
        resp = await provider.complete(req)
        assert resp.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self):
        provider = OpenAIProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        chunks = [chunk async for chunk in provider.stream(req)]
        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_stream_contains_provider_name(self):
        provider = OpenAIProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        result = "".join([chunk async for chunk in provider.stream(req)])
        assert "OpenAI" in result

    @pytest.mark.asyncio
    async def test_health_check(self):
        provider = OpenAIProvider()
        healthy = await provider.health_check()
        assert healthy is True

    @pytest.mark.asyncio
    async def test_health_check_sets_status(self):
        provider = OpenAIProvider()
        await provider.health_check()
        assert provider.get_status() == ProviderStatus.HEALTHY

    def test_supports_streaming(self):
        provider = OpenAIProvider()
        assert provider.supports_streaming() is True

    def test_supports_tools(self):
        provider = OpenAIProvider()
        assert provider.supports_tools() is True

    def test_supports_vision(self):
        provider = OpenAIProvider()
        assert provider.supports_vision() is True


class TestGeminiProvider:
    """Tests for Gemini provider."""

    def test_create_default(self):
        provider = GeminiProvider()
        assert provider.name == "gemini"

    def test_create_with_config(self):
        cfg = ProviderConfig(name="gemini", models=["gemini-2.0-flash"])
        provider = GeminiProvider(config=cfg)
        assert "gemini-2.0-flash" in provider.available_models

    def test_default_models(self):
        provider = GeminiProvider()
        assert "gemini-2.0-flash" in provider.available_models

    @pytest.mark.asyncio
    async def test_complete_returns_response(self):
        provider = GeminiProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="Hello")])
        resp = await provider.complete(req)
        assert isinstance(resp, AIResponse)
        assert resp.provider == "gemini"

    @pytest.mark.asyncio
    async def test_complete_default_model(self):
        provider = GeminiProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        resp = await provider.complete(req)
        assert resp.model == "gemini-2.0-flash"

    @pytest.mark.asyncio
    async def test_complete_specified_model(self):
        provider = GeminiProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="x")], model="gemini-1.5-pro")
        resp = await provider.complete(req)
        assert resp.model == "gemini-1.5-pro"

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self):
        provider = GeminiProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        chunks = [chunk async for chunk in provider.stream(req)]
        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_stream_contains_gemini(self):
        provider = GeminiProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        result = "".join([chunk async for chunk in provider.stream(req)])
        assert "Gemini" in result

    @pytest.mark.asyncio
    async def test_health_check(self):
        provider = GeminiProvider()
        assert await provider.health_check() is True

    def test_supports_streaming(self):
        provider = GeminiProvider()
        assert provider.supports_streaming() is True

    def test_supports_tools(self):
        provider = GeminiProvider()
        assert provider.supports_tools() is True

    def test_supports_vision(self):
        provider = GeminiProvider()
        assert provider.supports_vision() is True


class TestClaudeProvider:
    """Tests for Claude provider."""

    def test_create_default(self):
        provider = ClaudeProvider()
        assert provider.name == "claude"

    def test_create_with_config(self):
        cfg = ProviderConfig(name="claude", models=["claude-sonnet-4-20250514"])
        provider = ClaudeProvider(config=cfg)
        assert "claude-sonnet-4-20250514" in provider.available_models

    def test_default_models(self):
        provider = ClaudeProvider()
        assert "claude-sonnet-4-20250514" in provider.available_models

    @pytest.mark.asyncio
    async def test_complete_returns_response(self):
        provider = ClaudeProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="Hello")])
        resp = await provider.complete(req)
        assert isinstance(resp, AIResponse)
        assert resp.provider == "claude"

    @pytest.mark.asyncio
    async def test_complete_default_model(self):
        provider = ClaudeProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        resp = await provider.complete(req)
        assert resp.model == "claude-sonnet-4-20250514"

    @pytest.mark.asyncio
    async def test_complete_specified_model(self):
        provider = ClaudeProvider()
        req = AIRequest(
            messages=[AIMessage(role="user", content="x")], model="claude-3-5-haiku-20241022"
        )
        resp = await provider.complete(req)
        assert resp.model == "claude-3-5-haiku-20241022"

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self):
        provider = ClaudeProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        chunks = [chunk async for chunk in provider.stream(req)]
        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_stream_contains_claude(self):
        provider = ClaudeProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        result = "".join([chunk async for chunk in provider.stream(req)])
        assert "Claude" in result

    @pytest.mark.asyncio
    async def test_health_check(self):
        provider = ClaudeProvider()
        assert await provider.health_check() is True

    def test_supports_streaming(self):
        provider = ClaudeProvider()
        assert provider.supports_streaming() is True

    def test_supports_tools(self):
        provider = ClaudeProvider()
        assert provider.supports_tools() is True

    def test_supports_vision(self):
        provider = ClaudeProvider()
        assert provider.supports_vision() is True


class TestOllamaProvider:
    """Tests for Ollama provider."""

    def test_create_default(self):
        provider = OllamaProvider()
        assert provider.name == "ollama"

    def test_create_with_config(self):
        cfg = ProviderConfig(name="ollama", base_url="http://localhost:11434", models=["llama3"])
        provider = OllamaProvider(config=cfg)
        assert "llama3" in provider.available_models

    def test_default_models(self):
        provider = OllamaProvider()
        assert "llama3" in provider.available_models
        assert "mistral" in provider.available_models

    @pytest.mark.asyncio
    async def test_complete_returns_response(self):
        provider = OllamaProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="Hello")])
        resp = await provider.complete(req)
        assert isinstance(resp, AIResponse)
        assert resp.provider == "ollama"

    @pytest.mark.asyncio
    async def test_complete_default_model(self):
        provider = OllamaProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        resp = await provider.complete(req)
        assert resp.model == "llama3"

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self):
        provider = OllamaProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        chunks = [chunk async for chunk in provider.stream(req)]
        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_stream_contains_ollama(self):
        provider = OllamaProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        result = "".join([chunk async for chunk in provider.stream(req)])
        assert "Ollama" in result

    @pytest.mark.asyncio
    async def test_health_check(self):
        provider = OllamaProvider()
        assert await provider.health_check() is True

    def test_supports_streaming(self):
        provider = OllamaProvider()
        assert provider.supports_streaming() is True

    def test_does_not_support_tools(self):
        provider = OllamaProvider()
        assert provider.supports_tools() is False

    def test_does_not_support_vision(self):
        provider = OllamaProvider()
        assert provider.supports_vision() is False

    @pytest.mark.asyncio
    async def test_complete_increments_count(self):
        provider = OllamaProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="hi")])
        await provider.complete(req)
        assert provider._request_count == 1


class TestOpenRouterProvider:
    """Tests for OpenRouter provider."""

    def test_create_default(self):
        provider = OpenRouterProvider()
        assert provider.name == "openrouter"

    def test_create_with_config(self):
        cfg = ProviderConfig(name="openrouter", models=["meta-llama/llama-3-70b"])
        provider = OpenRouterProvider(config=cfg)
        assert "meta-llama/llama-3-70b" in provider.available_models

    def test_default_models(self):
        provider = OpenRouterProvider()
        assert len(provider.available_models) >= 2

    @pytest.mark.asyncio
    async def test_complete_returns_response(self):
        provider = OpenRouterProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="Hello")])
        resp = await provider.complete(req)
        assert isinstance(resp, AIResponse)
        assert resp.provider == "openrouter"

    @pytest.mark.asyncio
    async def test_complete_default_model(self):
        provider = OpenRouterProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        resp = await provider.complete(req)
        assert resp.model == "meta-llama/llama-3-70b"

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self):
        provider = OpenRouterProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        chunks = [chunk async for chunk in provider.stream(req)]
        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_health_check(self):
        provider = OpenRouterProvider()
        assert await provider.health_check() is True

    def test_supports_streaming(self):
        provider = OpenRouterProvider()
        assert provider.supports_streaming() is True

    def test_supports_tools(self):
        provider = OpenRouterProvider()
        assert provider.supports_tools() is True

    def test_supports_vision(self):
        provider = OpenRouterProvider()
        assert provider.supports_vision() is True


class TestProviderManager:
    """Tests for provider manager."""

    def test_register_provider(self):
        mgr = ProviderManager()
        provider = OpenAIProvider()
        mgr.register(provider)
        assert mgr.get("openai") is provider

    def test_get_nonexistent_returns_none(self):
        mgr = ProviderManager()
        assert mgr.get("nonexistent") is None

    def test_first_registered_is_default(self):
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        assert mgr.get_default() is not None
        assert mgr.get_default().name == "openai"

    def test_get_default_empty(self):
        mgr = ProviderManager()
        assert mgr.get_default() is None

    def test_set_default(self):
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        mgr.register(GeminiProvider())
        assert mgr.set_default("gemini") is True
        assert mgr.get_default().name == "gemini"

    def test_set_default_nonexistent(self):
        mgr = ProviderManager()
        assert mgr.set_default("fake") is False

    def test_list_all(self):
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        mgr.register(GeminiProvider())
        names = mgr.list_all()
        assert "openai" in names
        assert "gemini" in names

    def test_list_all_empty(self):
        mgr = ProviderManager()
        assert mgr.list_all() == []

    @pytest.mark.asyncio
    async def test_list_healthy_after_health_check(self):
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        await mgr.health_check_all()
        healthy = mgr.list_healthy()
        assert "openai" in healthy

    @pytest.mark.asyncio
    async def test_health_check_all(self):
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        mgr.register(GeminiProvider())
        results = await mgr.health_check_all()
        assert results["openai"] == ProviderStatus.HEALTHY
        assert results["gemini"] == ProviderStatus.HEALTHY

    def test_get_stats(self):
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        stats = mgr.get_stats()
        assert stats["total_providers"] == 1
        assert stats["default_provider"] == "openai"
        assert "openai" in stats["providers"]

    def test_get_stats_empty(self):
        mgr = ProviderManager()
        stats = mgr.get_stats()
        assert stats["total_providers"] == 0

    def test_register_multiple(self):
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        mgr.register(GeminiProvider())
        mgr.register(ClaudeProvider())
        assert len(mgr.list_all()) == 3

    def test_register_overwrites(self):
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        mgr.register(OpenAIProvider())
        assert len(mgr.list_all()) == 1

    @pytest.mark.asyncio
    async def test_health_check_updates_status(self):
        mgr = ProviderManager()
        p = OpenAIProvider()
        mgr.register(p)
        await mgr.health_check_all()
        assert p.get_status() == ProviderStatus.HEALTHY


class TestUnifiedAI:
    """Tests for Unified AI interface."""

    def _make_unified(self):
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        mgr.register(GeminiProvider())
        return UnifiedAI(mgr)

    @pytest.mark.asyncio
    async def test_complete_default_provider(self):
        ai = self._make_unified()
        req = AIRequest(messages=[AIMessage(role="user", content="hello")])
        resp = await ai.complete(req)
        assert isinstance(resp, AIResponse)

    @pytest.mark.asyncio
    async def test_complete_specified_provider(self):
        ai = self._make_unified()
        req = AIRequest(messages=[AIMessage(role="user", content="hi")], provider="gemini")
        resp = await ai.complete(req)
        assert resp.provider == "gemini"

    @pytest.mark.asyncio
    async def test_complete_no_provider_raises(self):
        mgr = ProviderManager()
        ai = UnifiedAI(mgr)
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        with pytest.raises(RuntimeError):
            await ai.complete(req)

    @pytest.mark.asyncio
    async def test_stream_default_provider(self):
        ai = self._make_unified()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        chunks = [chunk async for chunk in ai.stream(req)]
        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_stream_no_provider_raises(self):
        mgr = ProviderManager()
        ai = UnifiedAI(mgr)
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        with pytest.raises(RuntimeError):
            async for _ in ai.stream(req):
                pass

    @pytest.mark.asyncio
    async def test_complete_with_failover(self):
        ai = self._make_unified()
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        resp = await ai.complete_with_failover(req)
        assert isinstance(resp, AIResponse)

    @pytest.mark.asyncio
    async def test_get_token_usage_initial(self):
        ai = self._make_unified()
        usage = ai.get_token_usage()
        assert usage.total_tokens == 0

    @pytest.mark.asyncio
    async def test_get_token_usage_after_complete(self):
        ai = self._make_unified()
        req = AIRequest(messages=[AIMessage(role="user", content="test token usage")])
        await ai.complete(req)
        usage = ai.get_token_usage()
        assert usage.prompt_tokens > 0

    @pytest.mark.asyncio
    async def test_get_stats(self):
        ai = self._make_unified()
        stats = ai.get_stats()
        assert "total_requests" in stats
        assert "total_failures" in stats
        assert "token_usage" in stats

    @pytest.mark.asyncio
    async def test_get_stats_after_request(self):
        ai = self._make_unified()
        req = AIRequest(messages=[AIMessage(role="user", content="x")])
        await ai.complete(req)
        stats = ai.get_stats()
        assert stats["total_requests"] == 1

    @pytest.mark.asyncio
    async def test_complete_tracks_tokens(self):
        ai = self._make_unified()
        req = AIRequest(messages=[AIMessage(role="user", content="track me")])
        await ai.complete(req)
        usage = ai.get_token_usage()
        assert usage.prompt_tokens >= 0

    @pytest.mark.asyncio
    async def test_stream_specified_provider(self):
        ai = self._make_unified()
        req = AIRequest(messages=[AIMessage(role="user", content="hi")], provider="gemini")
        chunks = [chunk async for chunk in ai.stream(req)]
        result = "".join(chunks)
        assert "Gemini" in result

    @pytest.mark.asyncio
    async def test_multiple_requests_increment_count(self):
        ai = self._make_unified()
        req = AIRequest(messages=[AIMessage(role="user", content="x")])
        await ai.complete(req)
        await ai.complete(req)
        assert ai._total_requests == 2

    @pytest.mark.asyncio
    async def test_failover_all_providers(self):
        ai = self._make_unified()
        req = AIRequest(messages=[AIMessage(role="user", content="failover test")])
        resp = await ai.complete_with_failover(req)
        assert resp.content != ""

    @pytest.mark.asyncio
    async def test_complete_response_has_id(self):
        ai = self._make_unified()
        req = AIRequest(messages=[AIMessage(role="user", content="id test")])
        resp = await ai.complete(req)
        assert resp.response_id != ""


class TestTokenTracker:
    """Tests for token tracking."""

    def test_initial_total_zero(self):
        tracker = TokenTracker()
        usage = tracker.get_total()
        assert usage.total_tokens == 0

    def test_record_single(self):
        tracker = TokenTracker()
        tracker.record(provider="openai", model="gpt-4o", prompt_tokens=10, completion_tokens=5)
        usage = tracker.get_total()
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 5
        assert usage.total_tokens == 15

    def test_record_multiple(self):
        tracker = TokenTracker()
        tracker.record(provider="openai", model="gpt-4o", prompt_tokens=10, completion_tokens=5)
        tracker.record(provider="openai", model="gpt-4o", prompt_tokens=20, completion_tokens=10)
        usage = tracker.get_total()
        assert usage.total_tokens == 45

    def test_get_by_provider(self):
        tracker = TokenTracker()
        tracker.record(provider="openai", model="gpt-4o", prompt_tokens=10, completion_tokens=5)
        tracker.record(provider="gemini", model="flash", prompt_tokens=20, completion_tokens=10)
        usage = tracker.get_by_provider("openai")
        assert usage.total_tokens == 15

    def test_get_by_provider_missing(self):
        tracker = TokenTracker()
        usage = tracker.get_by_provider("nonexistent")
        assert usage.total_tokens == 0

    def test_get_by_model(self):
        tracker = TokenTracker()
        tracker.record(provider="openai", model="gpt-4o", prompt_tokens=10, completion_tokens=5)
        tracker.record(
            provider="openai", model="gpt-4-turbo", prompt_tokens=20, completion_tokens=10
        )
        usage = tracker.get_by_model("gpt-4o")
        assert usage.total_tokens == 15

    def test_get_by_model_missing(self):
        tracker = TokenTracker()
        usage = tracker.get_by_model("nonexistent")
        assert usage.total_tokens == 0

    def test_reset(self):
        tracker = TokenTracker()
        tracker.record(provider="openai", model="gpt-4o", prompt_tokens=100, completion_tokens=50)
        tracker.reset()
        usage = tracker.get_total()
        assert usage.total_tokens == 0

    def test_record_with_cost(self):
        tracker = TokenTracker()
        tracker.record(
            provider="openai", model="gpt-4o", prompt_tokens=10, completion_tokens=5, cost=0.01
        )
        usage = tracker.get_total()
        assert usage.cost_usd == 0.01

    def test_reset_clears_providers(self):
        tracker = TokenTracker()
        tracker.record(provider="openai", model="gpt-4o", prompt_tokens=10, completion_tokens=5)
        tracker.reset()
        usage = tracker.get_by_provider("openai")
        assert usage.total_tokens == 0


class TestAIRetry:
    """Tests for AI retry policy."""

    @pytest.mark.asyncio
    async def test_execute_success_no_retry(self):
        policy = AIRetryPolicy(max_retries=3)

        async def success():
            return "ok"

        result = await policy.execute(success)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_execute_with_retries(self):
        policy = AIRetryPolicy(max_retries=3, base_delay=0.01)
        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("fail")
            return "success"

        result = await policy.execute(flaky)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        policy = AIRetryPolicy(max_retries=2, base_delay=0.01)

        async def always_fail():
            raise RuntimeError("always fails")

        with pytest.raises(RuntimeError, match="always fails"):
            await policy.execute(always_fail)

    def test_get_delay_increases(self):
        policy = AIRetryPolicy(base_delay=1.0, max_delay=30.0)
        d0 = policy.get_delay(0)
        d1 = policy.get_delay(1)
        d2 = policy.get_delay(2)
        assert d0 < d1 < d2

    def test_get_delay_respects_max(self):
        policy = AIRetryPolicy(base_delay=1.0, max_delay=5.0)
        delay = policy.get_delay(10)
        assert delay <= 5.5  # max_delay + jitter

    @pytest.mark.asyncio
    async def test_execute_passes_args(self):
        policy = AIRetryPolicy()

        async def add(a, b):
            return a + b

        result = await policy.execute(add, 3, 4)
        assert result == 7

    @pytest.mark.asyncio
    async def test_execute_passes_kwargs(self):
        policy = AIRetryPolicy()

        async def greet(name="world"):
            return f"hello {name}"

        result = await policy.execute(greet, name="sona")
        assert result == "hello sona"

    def test_get_delay_first_attempt(self):
        policy = AIRetryPolicy(base_delay=2.0)
        delay = policy.get_delay(0)
        assert 2.0 <= delay <= 2.2


class TestEmbeddings:
    """Tests for embedding provider."""

    @pytest.mark.asyncio
    async def test_embed_returns_list(self):
        emb = SimpleEmbedding()
        vec = await emb.embed("hello world")
        assert isinstance(vec, list)

    @pytest.mark.asyncio
    async def test_embed_correct_dimension(self):
        emb = SimpleEmbedding(dimension=128)
        vec = await emb.embed("test text")
        assert len(vec) == 128

    @pytest.mark.asyncio
    async def test_embed_custom_dimension(self):
        emb = SimpleEmbedding(dimension=64)
        vec = await emb.embed("test")
        assert len(vec) == 64

    @pytest.mark.asyncio
    async def test_embed_batch_returns_list(self):
        emb = SimpleEmbedding()
        vecs = await emb.embed_batch(["hello", "world"])
        assert len(vecs) == 2

    @pytest.mark.asyncio
    async def test_embed_batch_correct_dimensions(self):
        emb = SimpleEmbedding(dimension=128)
        vecs = await emb.embed_batch(["a", "b", "c"])
        for vec in vecs:
            assert len(vec) == 128

    @pytest.mark.asyncio
    async def test_embed_deterministic(self):
        emb = SimpleEmbedding()
        v1 = await emb.embed("same text")
        v2 = await emb.embed("same text")
        assert v1 == v2

    @pytest.mark.asyncio
    async def test_embed_different_texts_differ(self):
        emb = SimpleEmbedding()
        v1 = await emb.embed("hello")
        v2 = await emb.embed("goodbye")
        assert v1 != v2

    @pytest.mark.asyncio
    async def test_embed_normalized(self):
        import math

        emb = SimpleEmbedding()
        vec = await emb.embed("normalize me")
        magnitude = math.sqrt(sum(v * v for v in vec))
        assert abs(magnitude - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_embed_empty_string(self):
        emb = SimpleEmbedding()
        vec = await emb.embed("")
        assert len(vec) == 128

    @pytest.mark.asyncio
    async def test_embed_batch_empty(self):
        emb = SimpleEmbedding()
        vecs = await emb.embed_batch([])
        assert vecs == []


class TestVectorStore:
    """Tests for vector store."""

    def test_add_vector(self):
        store = VectorStore(dimension=3)
        store.add("doc1", [1.0, 0.0, 0.0])
        assert store.size == 1

    def test_add_multiple(self):
        store = VectorStore(dimension=3)
        store.add("doc1", [1.0, 0.0, 0.0])
        store.add("doc2", [0.0, 1.0, 0.0])
        assert store.size == 2

    def test_search_returns_results(self):
        store = VectorStore(dimension=3)
        store.add("doc1", [1.0, 0.0, 0.0])
        results = store.search([1.0, 0.0, 0.0])
        assert len(results) == 1
        assert results[0][0] == "doc1"

    def test_search_top_k(self):
        store = VectorStore(dimension=3)
        store.add("d1", [1.0, 0.0, 0.0])
        store.add("d2", [0.9, 0.1, 0.0])
        store.add("d3", [0.0, 1.0, 0.0])
        results = store.search([1.0, 0.0, 0.0], top_k=2)
        assert len(results) == 2

    def test_search_sorted_by_similarity(self):
        store = VectorStore(dimension=3)
        store.add("exact", [1.0, 0.0, 0.0])
        store.add("close", [0.9, 0.1, 0.0])
        store.add("far", [0.0, 0.0, 1.0])
        results = store.search([1.0, 0.0, 0.0])
        assert results[0][0] == "exact"
        assert results[0][1] > results[1][1]

    def test_remove_existing(self):
        store = VectorStore(dimension=3)
        store.add("doc1", [1.0, 0.0, 0.0])
        assert store.remove("doc1") is True
        assert store.size == 0

    def test_remove_nonexistent(self):
        store = VectorStore(dimension=3)
        assert store.remove("nonexistent") is False

    def test_clear(self):
        store = VectorStore(dimension=3)
        store.add("d1", [1.0, 0.0, 0.0])
        store.add("d2", [0.0, 1.0, 0.0])
        store.clear()
        assert store.size == 0

    def test_dimension_mismatch_add_raises(self):
        store = VectorStore(dimension=3)
        with pytest.raises(ValueError):
            store.add("doc1", [1.0, 0.0])

    def test_dimension_mismatch_search_raises(self):
        store = VectorStore(dimension=3)
        store.add("doc1", [1.0, 0.0, 0.0])
        with pytest.raises(ValueError):
            store.search([1.0, 0.0])

    def test_cosine_similarity_identical(self):
        store = VectorStore(dimension=3)
        store.add("doc1", [1.0, 0.0, 0.0])
        results = store.search([1.0, 0.0, 0.0])
        assert abs(results[0][1] - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self):
        store = VectorStore(dimension=3)
        store.add("doc1", [1.0, 0.0, 0.0])
        results = store.search([0.0, 1.0, 0.0])
        assert abs(results[0][1]) < 0.001

    def test_size_property(self):
        store = VectorStore(dimension=3)
        assert store.size == 0
        store.add("d1", [1.0, 0.0, 0.0])
        assert store.size == 1

    def test_add_with_metadata(self):
        store = VectorStore(dimension=3)
        store.add("doc1", [1.0, 0.0, 0.0], metadata={"title": "Test"})
        assert store.size == 1

    def test_search_empty_store(self):
        store = VectorStore(dimension=3)
        results = store.search([1.0, 0.0, 0.0])
        assert results == []


class TestSemanticSearch:
    """Tests for semantic search."""

    def _make_search(self):
        emb = SimpleEmbedding(dimension=128)
        store = VectorStore(dimension=128)
        return SemanticSearch(emb, store)

    @pytest.mark.asyncio
    async def test_index_document(self):
        ss = self._make_search()
        await ss.index("doc1", "hello world")
        results = await ss.search("hello")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_returns_dicts(self):
        ss = self._make_search()
        await ss.index("doc1", "machine learning AI")
        results = await ss.search("AI learning")
        assert isinstance(results[0], dict)
        assert "doc_id" in results[0]
        assert "score" in results[0]

    @pytest.mark.asyncio
    async def test_search_top_k(self):
        ss = self._make_search()
        await ss.index("d1", "alpha")
        await ss.index("d2", "beta")
        await ss.index("d3", "gamma")
        results = await ss.search("alpha", top_k=2)
        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_index_with_metadata(self):
        ss = self._make_search()
        await ss.index("doc1", "test content", metadata={"source": "test"})
        results = await ss.search("test")
        assert results[0]["metadata"]["source"] == "test"

    @pytest.mark.asyncio
    async def test_index_batch(self):
        ss = self._make_search()
        items = [
            ("d1", "first document", None),
            ("d2", "second document", None),
            ("d3", "third document", None),
        ]
        await ss.index_batch(items)
        results = await ss.search("first")
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_remove_document(self):
        ss = self._make_search()
        await ss.index("doc1", "removable content")
        assert ss.remove("doc1") is True

    @pytest.mark.asyncio
    async def test_remove_nonexistent(self):
        ss = self._make_search()
        assert ss.remove("nonexistent") is False

    @pytest.mark.asyncio
    async def test_search_empty_index(self):
        ss = self._make_search()
        results = await ss.search("anything")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_scores_sorted(self):
        ss = self._make_search()
        await ss.index("d1", "python programming language")
        await ss.index("d2", "java programming")
        await ss.index("d3", "cooking recipe for pie")
        results = await ss.search("python programming")
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_index_overwrite(self):
        ss = self._make_search()
        await ss.index("doc1", "original")
        await ss.index("doc1", "updated")
        results = await ss.search("updated")
        assert any(r["doc_id"] == "doc1" for r in results)

    @pytest.mark.asyncio
    async def test_batch_with_metadata(self):
        ss = self._make_search()
        items = [("d1", "hello", {"tag": "a"}), ("d2", "world", {"tag": "b"})]
        await ss.index_batch(items)
        results = await ss.search("hello")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_returns_doc_id(self):
        ss = self._make_search()
        await ss.index("my-doc", "test content for search")
        results = await ss.search("test content")
        assert results[0]["doc_id"] == "my-doc"


class TestKnowledgeEngine:
    """Tests for knowledge engine."""

    @pytest.mark.asyncio
    async def test_ingest_text(self):
        engine = KnowledgeEngine()
        doc_id = await engine.ingest("Test Doc", "Some content here")
        assert doc_id != ""

    @pytest.mark.asyncio
    async def test_ingest_markdown(self):
        engine = KnowledgeEngine()
        doc_id = await engine.ingest("MD Doc", "# Title\n\nContent", doc_type="markdown")
        assert doc_id != ""

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        engine = KnowledgeEngine()
        await engine.ingest("Search Test", "Python is a programming language")
        results = await engine.search("Python")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_get_document(self):
        engine = KnowledgeEngine()
        doc_id = await engine.ingest("Get Test", "Content for retrieval")
        doc = await engine.get_document(doc_id)
        assert doc is not None
        assert doc.title == "Get Test"

    @pytest.mark.asyncio
    async def test_get_document_missing(self):
        engine = KnowledgeEngine()
        doc = await engine.get_document("nonexistent-id")
        assert doc is None

    @pytest.mark.asyncio
    async def test_delete_document(self):
        engine = KnowledgeEngine()
        doc_id = await engine.ingest("Delete Test", "Will be deleted")
        result = await engine.delete_document(doc_id)
        assert result is True
        doc = await engine.get_document(doc_id)
        assert doc is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self):
        engine = KnowledgeEngine()
        result = await engine.delete_document("fake-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_ingest_url(self):
        engine = KnowledgeEngine()
        doc_id = await engine.ingest_url("https://example.com", title="Example")
        assert doc_id != ""

    @pytest.mark.asyncio
    async def test_stats_initial(self):
        engine = KnowledgeEngine()
        stats = engine.get_stats()
        assert stats["documents"] == 0

    @pytest.mark.asyncio
    async def test_stats_after_ingest(self):
        engine = KnowledgeEngine()
        await engine.ingest("Stats Doc", "Some content")
        stats = engine.get_stats()
        assert stats["documents"] == 1

    @pytest.mark.asyncio
    async def test_ingest_html(self):
        engine = KnowledgeEngine()
        doc_id = await engine.ingest("HTML Doc", "<p>Hello</p>", doc_type="html")
        assert doc_id != ""

    @pytest.mark.asyncio
    async def test_search_top_k(self):
        engine = KnowledgeEngine()
        for i in range(5):
            await engine.ingest(f"Doc {i}", f"Content {i} about testing")
        results = await engine.search("testing", top_k=3)
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_ingest_with_source(self):
        engine = KnowledgeEngine()
        doc_id = await engine.ingest("Sourced", "Content", source="manual")
        doc = await engine.get_document(doc_id)
        assert doc.source == "manual"

    @pytest.mark.asyncio
    async def test_multiple_ingest(self):
        engine = KnowledgeEngine()
        id1 = await engine.ingest("First", "First content")
        id2 = await engine.ingest("Second", "Second content")
        assert id1 != id2

    @pytest.mark.asyncio
    async def test_search_empty(self):
        engine = KnowledgeEngine()
        results = await engine.search("nonexistent query")
        assert results == []


class TestChunkingEngine:
    """Tests for chunking engine."""

    def test_chunk_text_basic(self):
        engine = ChunkingEngine(max_chunk_size=50, overlap=10)
        chunks = engine.chunk_text("a" * 100)
        assert len(chunks) >= 2

    def test_chunk_text_short(self):
        engine = ChunkingEngine(max_chunk_size=100)
        chunks = engine.chunk_text("short text")
        assert len(chunks) == 1

    def test_chunk_text_empty(self):
        engine = ChunkingEngine()
        chunks = engine.chunk_text("")
        assert chunks == []

    def test_chunk_markdown_by_headings(self):
        engine = ChunkingEngine(max_chunk_size=500)
        md = "# Section 1\n\nContent 1\n\n# Section 2\n\nContent 2"
        chunks = engine.chunk_markdown(md)
        assert len(chunks) >= 1

    def test_chunk_markdown_empty(self):
        engine = ChunkingEngine()
        chunks = engine.chunk_markdown("")
        assert chunks == []

    def test_chunk_document_text(self):
        engine = ChunkingEngine(max_chunk_size=50, overlap=10)
        doc = Document(title="Test", content="a" * 100, doc_type=DocumentType.TXT)
        chunks = engine.chunk_document(doc)
        assert len(chunks) >= 2
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_chunk_document_markdown(self):
        engine = ChunkingEngine(max_chunk_size=500)
        doc = Document(title="MD", content="# Head\n\nBody content", doc_type=DocumentType.MARKDOWN)
        chunks = engine.chunk_document(doc)
        assert len(chunks) >= 1

    def test_overlap_creates_more_chunks(self):
        engine_no_overlap = ChunkingEngine(max_chunk_size=50, overlap=0)
        engine_overlap = ChunkingEngine(max_chunk_size=50, overlap=10)
        text = "a" * 150
        c1 = engine_no_overlap.chunk_text(text)
        c2 = engine_overlap.chunk_text(text)
        assert len(c2) >= len(c1)

    def test_chunk_preserves_content(self):
        engine = ChunkingEngine(max_chunk_size=1000, overlap=0)
        text = "Hello world, this is a test."
        chunks = engine.chunk_text(text)
        assert chunks[0] == text

    def test_chunks_have_doc_id(self):
        engine = ChunkingEngine()
        doc = Document(title="Test", content="Content here", doc_type=DocumentType.TXT)
        chunks = engine.chunk_document(doc)
        for chunk in chunks:
            assert chunk.doc_id == doc.doc_id


class TestDocumentProcessor:
    """Tests for document processor."""

    def test_process_text(self):
        proc = DocumentProcessor()
        doc = proc.process_text("Title", "Content here")
        assert doc.title == "Title"
        assert doc.doc_type == DocumentType.TXT

    def test_process_markdown(self):
        proc = DocumentProcessor()
        doc = proc.process_markdown("MD Title", "# Heading\n\nBody")
        assert doc.doc_type == DocumentType.MARKDOWN

    def test_process_html(self):
        proc = DocumentProcessor()
        doc = proc.process_html("HTML Title", "<p>Hello</p>")
        assert doc.doc_type == DocumentType.HTML
        assert "<p>" not in doc.content

    def test_process_html_strips_scripts(self):
        proc = DocumentProcessor()
        html = "<script>alert('x')</script><p>Clean</p>"
        doc = proc.process_html("Safe", html)
        assert "alert" not in doc.content
        assert "Clean" in doc.content

    def test_process_url(self):
        proc = DocumentProcessor()
        doc = proc.process_url("https://example.com", "Example")
        assert doc.doc_type == DocumentType.URL
        assert doc.source == "https://example.com"

    def test_process_text_with_source(self):
        proc = DocumentProcessor()
        doc = proc.process_text("Title", "Content", source="manual_upload")
        assert doc.source == "manual_upload"

    def test_stats_initial(self):
        proc = DocumentProcessor()
        stats = proc.get_stats()
        assert stats["documents_processed"] == 0

    def test_stats_after_processing(self):
        proc = DocumentProcessor()
        proc.process_text("T1", "C1")
        proc.process_markdown("T2", "# C2")
        stats = proc.get_stats()
        assert stats["documents_processed"] == 2

    def test_process_text_creates_chunks(self):
        proc = DocumentProcessor()
        doc = proc.process_text("Title", "A" * 1000)
        assert len(doc.chunks) >= 1

    def test_process_url_title_fallback(self):
        proc = DocumentProcessor()
        doc = proc.process_url("https://example.com/page")
        assert doc.title == "https://example.com/page"


class TestKnowledgeStore:
    """Tests for knowledge store."""

    def test_add_document(self):
        store = KnowledgeStore()
        doc = Document(title="Test", content="Content", doc_type=DocumentType.TXT)
        doc_id = store.add(doc)
        assert doc_id == doc.doc_id

    def test_get_document(self):
        store = KnowledgeStore()
        doc = Document(title="Test", content="Content", doc_type=DocumentType.TXT)
        store.add(doc)
        retrieved = store.get(doc.doc_id)
        assert retrieved is not None
        assert retrieved.title == "Test"

    def test_get_missing(self):
        store = KnowledgeStore()
        assert store.get("nonexistent") is None

    def test_list_all(self):
        store = KnowledgeStore()
        doc1 = Document(title="First", content="C1", doc_type=DocumentType.TXT)
        doc2 = Document(title="Second", content="C2", doc_type=DocumentType.TXT)
        store.add(doc1)
        store.add(doc2)
        docs = store.list_all()
        assert len(docs) == 2

    def test_delete_document(self):
        store = KnowledgeStore()
        doc = Document(title="Del", content="C", doc_type=DocumentType.TXT)
        store.add(doc)
        assert store.delete(doc.doc_id) is True
        assert store.get(doc.doc_id) is None

    def test_delete_nonexistent(self):
        store = KnowledgeStore()
        assert store.delete("fake") is False

    def test_search_by_content(self):
        store = KnowledgeStore()
        doc = Document(
            title="Python", content="Python programming language", doc_type=DocumentType.TXT
        )
        store.add(doc)
        results = store.search("Python")
        assert len(results) >= 1

    def test_search_by_title(self):
        store = KnowledgeStore()
        doc = Document(title="Unique Title XYZ", content="Some content", doc_type=DocumentType.TXT)
        store.add(doc)
        results = store.search("Unique Title XYZ")
        assert len(results) >= 1

    def test_get_chunks(self):
        store = KnowledgeStore()
        chunks = [Chunk(doc_id="d1", content="chunk1", index=0)]
        store.store_chunks("d1", chunks)
        retrieved = store.get_chunks("d1")
        assert len(retrieved) == 1

    def test_get_chunks_empty(self):
        store = KnowledgeStore()
        assert store.get_chunks("nonexistent") == []

    def test_count_property(self):
        store = KnowledgeStore()
        assert store.count == 0
        doc = Document(title="T", content="C", doc_type=DocumentType.TXT)
        store.add(doc)
        assert store.count == 1

    def test_list_all_limit(self):
        store = KnowledgeStore()
        for i in range(10):
            doc = Document(title=f"Doc{i}", content=f"Content{i}", doc_type=DocumentType.TXT)
            store.add(doc)
        docs = store.list_all(limit=5)
        assert len(docs) == 5


class TestKnowledgeSearch:
    """Tests for knowledge search."""

    def _make_search(self):
        store = KnowledgeStore()
        return KnowledgeSearch(store), store

    @pytest.mark.asyncio
    async def test_search_empty(self):
        ks, _ = self._make_search()
        results = await ks.search("anything")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_finds_document(self):
        ks, store = self._make_search()
        doc = Document(
            title="AI Guide", content="artificial intelligence overview", doc_type=DocumentType.TXT
        )
        store.add(doc)
        results = await ks.search("artificial intelligence")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_with_chunks(self):
        ks, store = self._make_search()
        doc = Document(title="Test", content="chunked content here", doc_type=DocumentType.TXT)
        store.add(doc)
        chunks = [Chunk(doc_id=doc.doc_id, content="chunked content here", index=0)]
        store.store_chunks(doc.doc_id, chunks)
        results = await ks.search("chunked")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_with_citations(self):
        ks, store = self._make_search()
        doc = Document(
            title="Cited Doc",
            content="citation test content",
            doc_type=DocumentType.TXT,
            source="manual",
        )
        store.add(doc)
        results, citations = await ks.search_with_citations("citation test")
        assert len(results) >= 1
        assert len(citations) >= 1

    @pytest.mark.asyncio
    async def test_citations_have_source(self):
        ks, store = self._make_search()
        doc = Document(
            title="Source Doc", content="source test", doc_type=DocumentType.TXT, source="api"
        )
        store.add(doc)
        _, citations = await ks.search_with_citations("source test")
        assert citations[0].source == "api"

    @pytest.mark.asyncio
    async def test_search_top_k(self):
        ks, store = self._make_search()
        for i in range(5):
            doc = Document(title=f"D{i}", content=f"shared content {i}", doc_type=DocumentType.TXT)
            store.add(doc)
        results = await ks.search("shared content", top_k=2)
        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_index_document_no_chunks(self):
        ks, store = self._make_search()
        doc = Document(title="NoChunk", content="body", doc_type=DocumentType.TXT)
        store.add(doc)
        await ks.index_document(doc)  # Should not raise

    @pytest.mark.asyncio
    async def test_search_result_fields(self):
        ks, store = self._make_search()
        doc = Document(title="Fields", content="fields test doc", doc_type=DocumentType.TXT)
        store.add(doc)
        results = await ks.search("fields test")
        r = results[0]
        assert isinstance(r, SearchResult)
        assert r.doc_id == doc.doc_id
        assert r.score > 0

    @pytest.mark.asyncio
    async def test_citation_has_title(self):
        ks, store = self._make_search()
        doc = Document(title="My Title", content="my content", doc_type=DocumentType.TXT)
        store.add(doc)
        _, citations = await ks.search_with_citations("my content")
        assert citations[0].title == "My Title"

    @pytest.mark.asyncio
    async def test_search_no_match(self):
        ks, store = self._make_search()
        doc = Document(title="Specific", content="very specific topic", doc_type=DocumentType.TXT)
        store.add(doc)
        results = await ks.search("completely unrelated xyz")
        assert results == []


class TestWebSearch:
    """Tests for web search interface."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        ws = WebSearch()
        results = await ws.search("python programming")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_result_has_title(self):
        ws = WebSearch()
        results = await ws.search("test query")
        assert results[0].title != ""

    @pytest.mark.asyncio
    async def test_search_result_has_url(self):
        ws = WebSearch()
        results = await ws.search("test")
        assert results[0].url.startswith("http")

    @pytest.mark.asyncio
    async def test_search_news(self):
        ws = WebSearch()
        results = await ws.search_news("AI developments")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_read_url(self):
        ws = WebSearch()
        page = await ws.read_url("https://example.com")
        assert page.url == "https://example.com"
        assert page.status_code == 200

    @pytest.mark.asyncio
    async def test_search_and_read(self):
        ws = WebSearch()
        pages = await ws.search_and_read("test query", top_n=2)
        assert len(pages) >= 1

    def test_generate_citations(self):
        ws = WebSearch()
        from web.schemas import WebResult

        results = [
            WebResult(title="Page 1", url="http://a.com", snippet="snip1", score=0.9),
            WebResult(title="Page 2", url="http://b.com", snippet="snip2", score=0.8),
        ]
        citations = ws.generate_citations(results)
        assert len(citations) == 2
        assert citations[0]["index"] == 1
        assert citations[1]["index"] == 2

    def test_generate_citations_empty(self):
        ws = WebSearch()
        citations = ws.generate_citations([])
        assert citations == []

    def test_get_stats(self):
        ws = WebSearch()
        stats = ws.get_stats()
        assert "engine" in stats

    @pytest.mark.asyncio
    async def test_search_max_results(self):
        ws = WebSearch()
        results = await ws.search("query", max_results=1)
        assert len(results) <= 1

    @pytest.mark.asyncio
    async def test_read_url_has_content(self):
        ws = WebSearch()
        page = await ws.read_url("https://example.com/page")
        assert page.content != ""

    @pytest.mark.asyncio
    async def test_search_news_max_results(self):
        ws = WebSearch()
        results = await ws.search_news("news", max_results=2)
        assert len(results) <= 2


class TestURLReader:
    """Tests for URL reader."""

    @pytest.mark.asyncio
    async def test_read_returns_page(self):
        reader = URLReader()
        page = await reader.read("https://example.com")
        assert page.url == "https://example.com"

    @pytest.mark.asyncio
    async def test_read_status_code(self):
        reader = URLReader()
        page = await reader.read("https://example.com")
        assert page.status_code == 200

    @pytest.mark.asyncio
    async def test_read_has_content(self):
        reader = URLReader()
        page = await reader.read("https://example.com/test")
        assert page.content != ""

    @pytest.mark.asyncio
    async def test_read_batch(self):
        reader = URLReader()
        pages = await reader.read_batch(["https://a.com", "https://b.com"])
        assert len(pages) == 2

    @pytest.mark.asyncio
    async def test_read_batch_empty(self):
        reader = URLReader()
        pages = await reader.read_batch([])
        assert pages == []

    def test_extract_text_strips_html(self):
        reader = URLReader()
        text = reader.extract_text("<p>Hello <b>World</b></p>")
        assert "Hello" in text
        assert "World" in text
        assert "<p>" not in text

    def test_extract_text_strips_scripts(self):
        reader = URLReader()
        html = "<script>var x = 1;</script><p>Content</p>"
        text = reader.extract_text(html)
        assert "var x" not in text
        assert "Content" in text

    @pytest.mark.asyncio
    async def test_read_increments_stats(self):
        reader = URLReader()
        await reader.read("https://example.com")
        assert reader._stats["reads"] == 1


class TestSearchEngine:
    """Tests for search engine."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        engine = SearchEngine()
        results = await engine.search("test query")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_result_has_url(self):
        engine = SearchEngine()
        results = await engine.search("python")
        assert results[0].url.startswith("http")

    @pytest.mark.asyncio
    async def test_news_search(self):
        engine = SearchEngine()
        results = await engine.news_search("news query")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_caching(self):
        engine = SearchEngine()
        await engine.search("cached query")
        cached = engine.get_cached("cached query")
        assert cached is not None

    def test_get_cached_missing(self):
        engine = SearchEngine()
        assert engine.get_cached("never searched") is None

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        engine = SearchEngine()
        await engine.search("to be cleared")
        count = engine.clear_cache()
        assert count >= 1
        assert engine.get_cached("to be cleared") is None

    def test_clear_cache_empty(self):
        engine = SearchEngine()
        count = engine.clear_cache()
        assert count == 0

    def test_get_stats_initial(self):
        engine = SearchEngine()
        stats = engine.get_stats()
        assert stats["searches"] == 0
        assert stats["cache_hits"] == 0

    @pytest.mark.asyncio
    async def test_stats_after_search(self):
        engine = SearchEngine()
        await engine.search("stats test")
        stats = engine.get_stats()
        assert stats["searches"] == 1

    @pytest.mark.asyncio
    async def test_cache_hit_counted(self):
        engine = SearchEngine()
        await engine.search("same")
        await engine.search("same")
        stats = engine.get_stats()
        assert stats["cache_hits"] == 1


class TestAgentIntelligence:
    """Tests for agent intelligence."""

    @pytest.mark.asyncio
    async def test_collaborative_reason(self):
        ai = AgentIntelligence()
        result = await ai.collaborative_reason(["agent1", "agent2"], "solve problem X")
        assert "perspectives" in result
        assert "consensus" in result
        assert result["agent_count"] == 2

    @pytest.mark.asyncio
    async def test_collaborative_reason_single_agent(self):
        ai = AgentIntelligence()
        result = await ai.collaborative_reason(["agent1"], "test")
        assert len(result["perspectives"]) == 1

    @pytest.mark.asyncio
    async def test_share_memory(self):
        ai = AgentIntelligence()
        result = await ai.share_memory("agent1", "agent2", "data", {"key": "value"})
        assert result is True

    @pytest.mark.asyncio
    async def test_delegate_dynamically(self):
        ai = AgentIntelligence()
        best = await ai.delegate_dynamically("write code", ["coder", "tester", "reviewer"])
        assert best in ["coder", "tester", "reviewer"]

    @pytest.mark.asyncio
    async def test_delegate_no_agents_raises(self):
        ai = AgentIntelligence()
        with pytest.raises(ValueError):
            await ai.delegate_dynamically("task", [])

    def test_record_strategy(self):
        ai = AgentIntelligence()
        ai.record_strategy("agent1", "code review", "approved", True)
        strategies = ai.get_learned_strategies(agent_id="agent1")
        assert len(strategies) == 1

    def test_get_learned_strategies_empty(self):
        ai = AgentIntelligence()
        strategies = ai.get_learned_strategies()
        assert strategies == []

    def test_get_learned_strategies_with_limit(self):
        ai = AgentIntelligence()
        for i in range(5):
            ai.record_strategy("a1", f"task{i}", f"outcome{i}", True)
        strategies = ai.get_learned_strategies(limit=3)
        assert len(strategies) <= 3

    @pytest.mark.asyncio
    async def test_recover_failed_task(self):
        ai = AgentIntelligence()
        plan = await ai.recover_failed_task("agent1", "deploy app", "timeout error")
        assert "recommendation" in plan
        assert plan["original_agent"] == "agent1"

    @pytest.mark.asyncio
    async def test_recover_suggests_retry_or_reassign(self):
        ai = AgentIntelligence()
        plan = await ai.recover_failed_task("agent1", "task", "error")
        assert plan["recommendation"] in ["retry", "reassign"]

    def test_stats_initial(self):
        ai = AgentIntelligence()
        stats = ai.get_stats()
        assert stats["reasoning_count"] == 0
        assert stats["delegation_count"] == 0
        assert stats["recovery_count"] == 0

    @pytest.mark.asyncio
    async def test_stats_after_reasoning(self):
        ai = AgentIntelligence()
        await ai.collaborative_reason(["a1", "a2"], "problem")
        stats = ai.get_stats()
        assert stats["reasoning_count"] == 1

    @pytest.mark.asyncio
    async def test_stats_after_delegation(self):
        ai = AgentIntelligence()
        await ai.delegate_dynamically("task", ["a1", "a2"])
        stats = ai.get_stats()
        assert stats["delegation_count"] == 1

    @pytest.mark.asyncio
    async def test_stats_after_recovery(self):
        ai = AgentIntelligence()
        await ai.recover_failed_task("a1", "task", "err")
        stats = ai.get_stats()
        assert stats["recovery_count"] == 1

    @pytest.mark.asyncio
    async def test_collaborative_reason_consensus(self):
        ai = AgentIntelligence()
        result = await ai.collaborative_reason(["a1", "a2", "a3"], "complex problem")
        assert result["consensus"]["participant_count"] == 3


class TestSharedAgentMemory:
    """Tests for shared agent memory."""

    def test_share(self):
        mem = SharedAgentMemory()
        result = mem.share("agent1", "agent2", "data_key", "data_value")
        assert result is True

    def test_get_shared(self):
        mem = SharedAgentMemory()
        mem.share("agent1", "agent2", "key1", "value1")
        value = mem.get_shared("agent2", "key1")
        assert value == "value1"

    def test_get_shared_missing(self):
        mem = SharedAgentMemory()
        assert mem.get_shared("agent1", "nonexistent") is None

    def test_get_all_shared(self):
        mem = SharedAgentMemory()
        mem.share("a1", "a2", "k1", "v1")
        mem.share("a1", "a2", "k2", "v2")
        all_shared = mem.get_all_shared("a2")
        assert "k1" in all_shared
        assert "k2" in all_shared

    def test_get_all_shared_empty(self):
        mem = SharedAgentMemory()
        assert mem.get_all_shared("agent1") == {}

    def test_revoke(self):
        mem = SharedAgentMemory()
        mem.share("a1", "a2", "key", "value")
        result = mem.revoke("a1", "a2", "key")
        assert result is True
        assert mem.get_shared("a2", "key") is None

    def test_revoke_wrong_source(self):
        mem = SharedAgentMemory()
        mem.share("a1", "a2", "key", "value")
        result = mem.revoke("a3", "a2", "key")
        assert result is False

    def test_revoke_nonexistent(self):
        mem = SharedAgentMemory()
        result = mem.revoke("a1", "a2", "nonexistent")
        assert result is False

    def test_stats(self):
        mem = SharedAgentMemory()
        mem.share("a1", "a2", "k1", "v1")
        mem.share("a1", "a2", "k2", "v2")
        stats = mem.get_sharing_stats()
        assert stats["total_shared"] == 2
        assert stats["active_entries"] == 2

    def test_stats_after_revoke(self):
        mem = SharedAgentMemory()
        mem.share("a1", "a2", "k1", "v1")
        mem.revoke("a1", "a2", "k1")
        stats = mem.get_sharing_stats()
        assert stats["total_revoked"] == 1
        assert stats["active_entries"] == 0


class TestStrategyLearner:
    """Tests for strategy learner."""

    def test_record(self):
        sl = StrategyLearner()
        sl.record("agent1", "code review", "approved", True)
        history = sl.get_history()
        assert len(history) == 1

    def test_get_best_strategy(self):
        sl = StrategyLearner()
        sl.record("a1", "deploy app", "used docker", True)
        best = sl.get_best_strategy("deploy")
        assert best is not None
        assert best["outcome"] == "used docker"

    def test_get_best_strategy_none(self):
        sl = StrategyLearner()
        assert sl.get_best_strategy("nonexistent") is None

    def test_get_success_rate(self):
        sl = StrategyLearner()
        sl.record("a1", "task1", "ok", True)
        sl.record("a1", "task2", "fail", False)
        rate = sl.get_success_rate("a1")
        assert rate == 0.5

    def test_get_success_rate_all(self):
        sl = StrategyLearner()
        sl.record("a1", "t1", "ok", True)
        sl.record("a2", "t2", "ok", True)
        sl.record("a1", "t3", "fail", False)
        rate = sl.get_success_rate()
        assert abs(rate - 2.0 / 3.0) < 0.01

    def test_get_success_rate_empty(self):
        sl = StrategyLearner()
        assert sl.get_success_rate() == 0.0

    def test_get_history_limit(self):
        sl = StrategyLearner()
        for i in range(10):
            sl.record("a1", f"task{i}", f"out{i}", True)
        history = sl.get_history(limit=5)
        assert len(history) == 5

    def test_get_history_by_agent(self):
        sl = StrategyLearner()
        sl.record("a1", "t1", "o1", True)
        sl.record("a2", "t2", "o2", True)
        history = sl.get_history(agent_id="a1")
        assert len(history) == 1
        assert history[0]["agent_id"] == "a1"

    def test_clear(self):
        sl = StrategyLearner()
        sl.record("a1", "t1", "o1", True)
        sl.clear()
        assert sl.get_history() == []

    def test_record_multiple(self):
        sl = StrategyLearner()
        sl.record("a1", "task1", "outcome1", True)
        sl.record("a1", "task2", "outcome2", False)
        sl.record("a2", "task3", "outcome3", True)
        history = sl.get_history()
        assert len(history) == 3


class TestPrometheusRegistry:
    """Tests for Prometheus metrics."""

    def test_counter_create(self):
        c = Counter("test_counter", "A test counter")
        assert c.name == "test_counter"
        assert c.value == 0.0

    def test_counter_inc(self):
        c = Counter("test_counter")
        c.inc()
        assert c.value == 1.0

    def test_counter_inc_value(self):
        c = Counter("test_counter")
        c.inc(5)
        assert c.value == 5.0

    def test_counter_negative_raises(self):
        c = Counter("test_counter")
        with pytest.raises(ValueError):
            c.inc(-1)

    def test_counter_with_labels(self):
        c = Counter("http_requests")
        c.inc(1, labels={"method": "GET"})
        c.inc(2, labels={"method": "POST"})
        export = c.export()
        assert "GET" in export
        assert "POST" in export

    def test_gauge_create(self):
        g = Gauge("test_gauge", "A test gauge")
        assert g.value == 0.0

    def test_gauge_set(self):
        g = Gauge("test_gauge")
        g.set(42.0)
        assert g.value == 42.0

    def test_gauge_inc_dec(self):
        g = Gauge("test_gauge")
        g.inc(5)
        g.dec(2)
        assert g.value == 3.0

    def test_gauge_with_labels(self):
        g = Gauge("active_conns")
        g.set(10, labels={"host": "server1"})
        export = g.export()
        assert "server1" in export

    def test_histogram_create(self):
        h = Histogram("request_duration", "Duration in seconds")
        assert h.count == 0
        assert h.sum == 0.0

    def test_histogram_observe(self):
        h = Histogram("request_duration")
        h.observe(0.5)
        h.observe(1.5)
        assert h.count == 2
        assert h.sum == 2.0

    def test_histogram_export_format(self):
        h = Histogram("latency", buckets=[0.1, 0.5, 1.0])
        h.observe(0.3)
        export = h.export()
        assert "latency_bucket" in export
        assert "latency_count" in export
        assert "latency_sum" in export

    def test_registry_counter(self):
        reg = PrometheusRegistry()
        c = reg.counter("req_total", "Total requests")
        c.inc()
        assert reg.counter("req_total") is c

    def test_registry_gauge(self):
        reg = PrometheusRegistry()
        g = reg.gauge("active", "Active connections")
        g.set(5)
        assert reg.gauge("active") is g

    def test_registry_export(self):
        reg = PrometheusRegistry()
        reg.counter("c1").inc(10)
        reg.gauge("g1").set(5)
        reg.histogram("h1").observe(0.1)
        output = reg.export()
        assert "c1" in output
        assert "g1" in output
        assert "h1" in output


class TestOTelExporter:
    """Tests for OpenTelemetry exporter."""

    def test_create(self):
        exp = OTelExporter(service_name="test-svc")
        assert exp._service_name == "test-svc"

    def test_export_traces(self):
        exp = OTelExporter()
        spans = [{"name": "span1", "duration": 100}]
        result = exp.export_traces(spans)
        assert result is True

    def test_export_traces_empty(self):
        exp = OTelExporter()
        result = exp.export_traces([])
        assert result is True

    def test_export_metrics(self):
        exp = OTelExporter()
        metrics = {"cpu_usage": 0.5, "memory": 1024}
        result = exp.export_metrics(metrics)
        assert result is True

    def test_export_metrics_empty(self):
        exp = OTelExporter()
        result = exp.export_metrics({})
        assert result is True

    def test_get_resource_attributes(self):
        exp = OTelExporter(service_name="my-svc")
        attrs = exp.get_resource_attributes()
        assert attrs["service.name"] == "my-svc"
        assert "service.version" in attrs

    def test_get_stats(self):
        exp = OTelExporter()
        exp.export_traces([{"span": 1}])
        stats = exp.get_stats()
        assert stats["exported_traces"] == 1

    def test_stats_accumulate(self):
        exp = OTelExporter()
        exp.export_traces([{"s": 1}])
        exp.export_traces([{"s": 2}, {"s": 3}])
        exp.export_metrics({"m1": 1})
        stats = exp.get_stats()
        assert stats["exported_traces"] == 3
        assert stats["exported_metrics"] == 1


class TestDashboardConfig:
    """Tests for dashboard configuration."""

    def test_generate_overview(self):
        dc = DashboardConfig()
        dashboard = dc.generate_overview_dashboard()
        assert "title" in dashboard
        assert "panels" in dashboard
        assert len(dashboard["panels"]) >= 3

    def test_generate_ai(self):
        dc = DashboardConfig()
        dashboard = dc.generate_ai_dashboard()
        assert "AI Performance" in dashboard["title"]
        assert len(dashboard["panels"]) >= 3

    def test_generate_agent(self):
        dc = DashboardConfig()
        dashboard = dc.generate_agent_dashboard()
        assert "Agent Coordination" in dashboard["title"]
        assert len(dashboard["panels"]) >= 3

    def test_list_dashboards(self):
        dc = DashboardConfig()
        dashboards = dc.list_dashboards()
        assert "overview" in dashboards
        assert "ai-performance" in dashboards
        assert "agent-coordination" in dashboards

    def test_dashboard_has_uid(self):
        dc = DashboardConfig()
        dashboard = dc.generate_overview_dashboard()
        assert "uid" in dashboard
        assert dashboard["uid"] == "sona-overview"

    def test_custom_title(self):
        dc = DashboardConfig(title="Custom App")
        dashboard = dc.generate_overview_dashboard()
        assert "Custom App" in dashboard["title"]


class TestVaultClient:
    """Tests for vault client."""

    def test_write_secret(self):
        vault = VaultClient(namespace="test")
        result = vault.write_secret("db/password", {"password": "secret123"})
        assert result is True

    def test_read_secret(self):
        vault = VaultClient(namespace="test")
        vault.write_secret("db/password", {"password": "secret123"})
        data = vault.read_secret("db/password")
        assert data is not None
        assert data["password"] == "secret123"

    def test_read_missing(self):
        vault = VaultClient(namespace="test")
        assert vault.read_secret("nonexistent") is None

    def test_delete_secret(self):
        vault = VaultClient(namespace="test")
        vault.write_secret("temp/key", {"key": "val"})
        assert vault.delete_secret("temp/key") is True
        assert vault.read_secret("temp/key") is None

    def test_delete_nonexistent(self):
        vault = VaultClient(namespace="test")
        assert vault.delete_secret("fake") is False

    def test_list_secrets(self):
        vault = VaultClient(namespace="test")
        vault.write_secret("app/db", {"host": "localhost"})
        vault.write_secret("app/cache", {"host": "redis"})
        keys = vault.list_secrets("app")
        assert "db" in keys
        assert "cache" in keys

    def test_list_secrets_empty(self):
        vault = VaultClient(namespace="test")
        keys = vault.list_secrets("empty")
        assert keys == []

    def test_rotate_credentials(self):
        vault = VaultClient(namespace="test")
        vault.write_secret("svc/api", {"api_key": "old_key"})
        result = vault.rotate_credentials("svc/api")
        assert "key" in result
        assert result["key"] != ""

    def test_rotate_nonexistent(self):
        vault = VaultClient(namespace="test")
        result = vault.rotate_credentials("nonexistent")
        assert "error" in result

    def test_health(self):
        vault = VaultClient(namespace="test")
        health = vault.get_health()
        assert health["initialized"] is True
        assert health["sealed"] is False
        assert health["namespace"] == "test"

    def test_write_overwrite(self):
        vault = VaultClient(namespace="test")
        vault.write_secret("key/path", {"v": "1"})
        vault.write_secret("key/path", {"v": "2"})
        data = vault.read_secret("key/path")
        assert data["v"] == "2"

    def test_health_secrets_count(self):
        vault = VaultClient(namespace="test")
        vault.write_secret("a/b", {"x": 1})
        health = vault.get_health()
        assert health["secrets_count"] == 1


class TestOIDCProvider:
    """Tests for OIDC provider."""

    def _make_provider(self):
        config = OIDCConfig(
            issuer_url="https://auth.example.com",
            client_id="test-client",
            client_secret="test-secret",
            redirect_uri="https://app.example.com/callback",
        )
        return OIDCProvider(config)

    def test_get_authorization_url(self):
        provider = self._make_provider()
        url = provider.get_authorization_url()
        assert "https://auth.example.com/authorize" in url
        assert "client_id=test-client" in url

    def test_get_authorization_url_with_state(self):
        provider = self._make_provider()
        url = provider.get_authorization_url(state="abc123")
        assert "state=abc123" in url

    def test_authorization_url_has_scopes(self):
        provider = self._make_provider()
        url = provider.get_authorization_url()
        assert "openid" in url

    @pytest.mark.asyncio
    async def test_exchange_code(self):
        provider = self._make_provider()
        tokens = await provider.exchange_code("valid-code")
        assert tokens is not None
        assert tokens.id_token != ""
        assert tokens.access_token != ""

    @pytest.mark.asyncio
    async def test_exchange_empty_code(self):
        provider = self._make_provider()
        tokens = await provider.exchange_code("")
        assert tokens is None

    @pytest.mark.asyncio
    async def test_get_user_info(self):
        provider = self._make_provider()
        tokens = await provider.exchange_code("code123")
        user = await provider.get_user_info(tokens.access_token)
        assert user is not None
        assert user.sub != ""

    @pytest.mark.asyncio
    async def test_get_user_info_empty_token(self):
        provider = self._make_provider()
        user = await provider.get_user_info("")
        assert user is None

    @pytest.mark.asyncio
    async def test_refresh_token(self):
        provider = self._make_provider()
        tokens = await provider.exchange_code("code1")
        new_tokens = await provider.refresh_token(tokens.refresh_token)
        assert new_tokens is not None
        assert new_tokens.access_token != tokens.access_token

    @pytest.mark.asyncio
    async def test_refresh_empty_token(self):
        provider = self._make_provider()
        result = await provider.refresh_token("")
        assert result is None

    def test_validate_id_token(self):
        provider = self._make_provider()
        id_token = provider._generate_id_token("test-subject")
        claims = provider.validate_id_token(id_token)
        assert claims is not None
        assert claims["sub"] == "test-subject"

    def test_validate_id_token_empty(self):
        provider = self._make_provider()
        assert provider.validate_id_token("") is None

    def test_validate_id_token_invalid(self):
        provider = self._make_provider()
        assert provider.validate_id_token("not.a.valid.token") is None


class TestEncryptionAtRest:
    """Tests for encryption at rest."""

    def test_encrypt_field(self):
        enc = EncryptionAtRest(master_key="test-key")
        ciphertext = enc.encrypt_field("hello")
        assert ciphertext != ""
        assert ciphertext != "hello"

    def test_decrypt_field(self):
        enc = EncryptionAtRest(master_key="test-key")
        ciphertext = enc.encrypt_field("secret data")
        plaintext = enc.decrypt_field(ciphertext)
        assert plaintext == "secret data"

    def test_roundtrip(self):
        enc = EncryptionAtRest(master_key="my-key")
        original = "sensitive information 123"
        encrypted = enc.encrypt_field(original)
        decrypted = enc.decrypt_field(encrypted)
        assert decrypted == original

    def test_encrypt_empty(self):
        enc = EncryptionAtRest()
        assert enc.encrypt_field("") == ""

    def test_decrypt_empty(self):
        enc = EncryptionAtRest()
        assert enc.decrypt_field("") == ""

    def test_encrypt_dict(self):
        enc = EncryptionAtRest(master_key="key")
        data = {"name": "Alice", "age": 30}
        encrypted = enc.encrypt_dict(data)
        assert encrypted["name"] != "Alice"
        assert encrypted["age"] == 30  # non-string unchanged

    def test_decrypt_dict(self):
        enc = EncryptionAtRest(master_key="key")
        data = {"name": "Alice", "role": "admin"}
        encrypted = enc.encrypt_dict(data)
        decrypted = enc.decrypt_dict(encrypted)
        assert decrypted["name"] == "Alice"
        assert decrypted["role"] == "admin"

    def test_different_keys_different_output(self):
        enc1 = EncryptionAtRest(master_key="key1")
        enc2 = EncryptionAtRest(master_key="key2")
        c1 = enc1.encrypt_field("same text")
        c2 = enc2.encrypt_field("same text")
        assert c1 != c2

    def test_transit_encrypt_decrypt(self):
        transit = TransitEncryption(key_name="test")
        encrypted = transit.encrypt("hello transit")
        decrypted = transit.decrypt(encrypted)
        assert decrypted == "hello transit"

    def test_transit_rotate_key(self):
        transit = TransitEncryption(key_name="app")
        key_id = transit.rotate_key()
        assert "app-v2" in key_id


class TestComplianceAuditor:
    """Tests for compliance auditor."""

    def test_run_all(self):
        auditor = ComplianceAuditor()
        checks = auditor.run_all()
        assert len(checks) >= 5

    def test_all_checks_pass(self):
        auditor = ComplianceAuditor()
        checks = auditor.run_all()
        assert all(c.passed for c in checks)

    def test_check_encryption(self):
        auditor = ComplianceAuditor()
        check = auditor.check_encryption()
        assert check.name == "encryption_at_rest"
        assert check.passed is True

    def test_check_authentication(self):
        auditor = ComplianceAuditor()
        check = auditor.check_authentication()
        assert check.name == "authentication"
        assert check.severity == "critical"

    def test_check_secrets_management(self):
        auditor = ComplianceAuditor()
        check = auditor.check_secrets_management()
        assert check.passed is True

    def test_check_rate_limiting(self):
        auditor = ComplianceAuditor()
        check = auditor.check_rate_limiting()
        assert check.passed is True

    def test_check_audit_logging(self):
        auditor = ComplianceAuditor()
        check = auditor.check_audit_logging()
        assert check.passed is True

    def test_get_compliance_score(self):
        auditor = ComplianceAuditor()
        score = auditor.get_compliance_score()
        assert score == 1.0


class TestIntegrationPhase18:
    """End-to-end integration tests combining AI + Knowledge + Web + Agents."""

    @pytest.mark.asyncio
    async def test_ai_complete_and_track_tokens(self):
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        ai = UnifiedAI(mgr)
        req = AIRequest(messages=[AIMessage(role="user", content="summarize this")])
        resp = await ai.complete(req)
        usage = ai.get_token_usage()
        assert resp.content != ""
        assert usage.prompt_tokens >= 0

    @pytest.mark.asyncio
    async def test_knowledge_ingest_and_search(self):
        engine = KnowledgeEngine()
        await engine.ingest("AI Tutorial", "Machine learning is a subset of AI")
        results = await engine.search("machine learning")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_web_search_and_citations(self):
        ws = WebSearch()
        results = await ws.search("AI frameworks")
        citations = ws.generate_citations(results)
        assert len(citations) >= 1
        assert "url" in citations[0]

    @pytest.mark.asyncio
    async def test_agent_delegate_and_record(self):
        ai = AgentIntelligence()
        best = await ai.delegate_dynamically("write tests", ["tester", "coder"])
        ai.record_strategy(best, "write tests", "completed", True)
        strategies = ai.get_learned_strategies()
        assert len(strategies) == 1

    @pytest.mark.asyncio
    async def test_provider_failover_integration(self):
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        mgr.register(GeminiProvider())
        ai = UnifiedAI(mgr)
        req = AIRequest(messages=[AIMessage(role="user", content="failover")])
        resp = await ai.complete_with_failover(req)
        assert resp.content != ""

    @pytest.mark.asyncio
    async def test_embedding_and_vector_search(self):
        emb = SimpleEmbedding(dimension=128)
        store = VectorStore(dimension=128)
        ss = SemanticSearch(emb, store)
        await ss.index("d1", "python machine learning")
        await ss.index("d2", "javascript web development")
        results = await ss.search("python AI")
        assert results[0]["doc_id"] == "d1"

    @pytest.mark.asyncio
    async def test_vault_encrypt_store_retrieve(self):
        vault = VaultClient(namespace="integration")
        enc = EncryptionAtRest(master_key="vault-key")
        encrypted = enc.encrypt_field("super_secret_password")
        vault.write_secret("app/db", {"encrypted_pass": encrypted})
        data = vault.read_secret("app/db")
        decrypted = enc.decrypt_field(data["encrypted_pass"])
        assert decrypted == "super_secret_password"

    @pytest.mark.asyncio
    async def test_oidc_full_flow(self):
        config = OIDCConfig(
            issuer_url="https://auth.example.com",
            client_id="app",
            client_secret="secret",
            redirect_uri="https://app.com/cb",
        )
        oidc = OIDCProvider(config)
        tokens = await oidc.exchange_code("auth-code-123")
        user = await oidc.get_user_info(tokens.access_token)
        assert user is not None
        assert user.sub != ""

    @pytest.mark.asyncio
    async def test_knowledge_ingest_delete_flow(self):
        engine = KnowledgeEngine()
        doc_id = await engine.ingest("Temp Doc", "temporary content")
        assert await engine.get_document(doc_id) is not None
        await engine.delete_document(doc_id)
        assert await engine.get_document(doc_id) is None

    def test_prometheus_full_metrics(self):
        reg = PrometheusRegistry()
        req_counter = reg.counter("http_requests_total", "Total HTTP requests")
        latency = reg.histogram("http_duration_seconds", "Duration")
        active = reg.gauge("active_connections")
        req_counter.inc(100)
        latency.observe(0.05)
        latency.observe(0.1)
        active.set(42)
        output = reg.export()
        assert "http_requests_total" in output
        assert "http_duration_seconds" in output
        assert "active_connections" in output

    @pytest.mark.asyncio
    async def test_multi_provider_stats(self):
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        mgr.register(GeminiProvider())
        mgr.register(ClaudeProvider())
        ai = UnifiedAI(mgr)
        req = AIRequest(messages=[AIMessage(role="user", content="test")])
        await ai.complete(req)
        stats = ai.get_stats()
        assert stats["providers"]["total_providers"] == 3

    @pytest.mark.asyncio
    async def test_agent_collaborative_and_share_memory(self):
        ai = AgentIntelligence()
        result = await ai.collaborative_reason(["a1", "a2"], "design API")
        await ai.share_memory("a1", "a2", "api_design", result["consensus"])
        shared = ai._shared_memory.get_shared("a2", "api_design")
        assert shared is not None

    @pytest.mark.asyncio
    async def test_web_search_read_url(self):
        ws = WebSearch()
        results = await ws.search("documentation")
        page = await ws.read_url(results[0].url)
        assert page.content != ""

    def test_compliance_with_vault(self):
        vault = VaultClient()
        vault.write_secret("compliance/key", {"api_key": "safe"})
        auditor = ComplianceAuditor()
        score = auditor.get_compliance_score()
        assert score == 1.0

    @pytest.mark.asyncio
    async def test_otel_with_ai_metrics(self):
        exp = OTelExporter(service_name="sona")
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        ai = UnifiedAI(mgr)
        req = AIRequest(messages=[AIMessage(role="user", content="trace")])
        await ai.complete(req)
        stats = ai.get_stats()
        exp.export_metrics(stats["token_usage"])
        otel_stats = exp.get_stats()
        assert otel_stats["exported_metrics"] >= 1

    @pytest.mark.asyncio
    async def test_knowledge_search_with_semantic(self):
        engine = KnowledgeEngine()
        await engine.ingest("Python Guide", "Python is great for data science and AI")
        await engine.ingest("JS Guide", "JavaScript powers the modern web")
        results = await engine.search("Python")
        assert any("Python" in r.content for r in results)

    @pytest.mark.asyncio
    async def test_retry_with_provider(self):
        policy = AIRetryPolicy(max_retries=2, base_delay=0.01)
        provider = OpenAIProvider()
        req = AIRequest(messages=[AIMessage(role="user", content="retry test")])
        resp = await policy.execute(provider.complete, req)
        assert isinstance(resp, AIResponse)

    @pytest.mark.asyncio
    async def test_token_tracker_multi_provider(self):
        tracker = TokenTracker()
        tracker.record(provider="openai", model="gpt-4o", prompt_tokens=100, completion_tokens=50)
        tracker.record(provider="gemini", model="flash", prompt_tokens=80, completion_tokens=40)
        total = tracker.get_total()
        assert total.total_tokens == 270
        assert tracker.get_by_provider("openai").total_tokens == 150

    @pytest.mark.asyncio
    async def test_dashboard_for_ai_metrics(self):
        dc = DashboardConfig(title="Integration Test")
        ai_dash = dc.generate_ai_dashboard()
        assert len(ai_dash["panels"]) >= 3
        assert ai_dash["refresh"] == "10s"

    @pytest.mark.asyncio
    async def test_agent_recovery_flow(self):
        ai = AgentIntelligence()
        ai.record_strategy("agent1", "deploy", "success", True)
        ai.record_strategy("agent1", "deploy", "failed", False)
        plan = await ai.recover_failed_task("agent1", "deploy app", "timeout")
        assert plan["agent_success_rate"] == 0.5
        assert plan["recommendation"] in ["retry", "reassign"]


class TestAISchemasExtra:
    """Additional schema tests."""

    def test_ai_request_tools_default_none(self):
        req = AIRequest(messages=[])
        assert req.tools is None

    def test_ai_request_with_tools(self):
        req = AIRequest(messages=[], tools=[{"name": "search", "params": {}}])
        assert len(req.tools) == 1

    def test_ai_request_system_prompt(self):
        req = AIRequest(messages=[], system_prompt="You are helpful.")
        assert req.system_prompt == "You are helpful."

    def test_ai_response_unique_ids(self):
        r1 = AIResponse(content="a", model="m", provider="p")
        r2 = AIResponse(content="b", model="m", provider="p")
        assert r1.response_id != r2.response_id

    def test_token_usage_addition(self):
        u1 = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        u2 = TokenUsage(prompt_tokens=20, completion_tokens=10, total_tokens=30)
        combined_total = u1.total_tokens + u2.total_tokens
        assert combined_total == 45

    def test_provider_config_base_url(self):
        cfg = ProviderConfig(name="custom", base_url="http://localhost:8080")
        assert cfg.base_url == "http://localhost:8080"


class TestProviderManagerExtra:
    """Additional provider manager tests."""

    @pytest.mark.asyncio
    async def test_health_check_with_all_providers(self):
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        mgr.register(GeminiProvider())
        mgr.register(ClaudeProvider())
        mgr.register(OllamaProvider())
        results = await mgr.health_check_all()
        assert len(results) == 4

    def test_stats_provider_details(self):
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        stats = mgr.get_stats()
        assert "models" in stats["providers"]["openai"]
        assert "requests" in stats["providers"]["openai"]


class TestVectorStoreExtra:
    """Additional vector store tests."""

    def test_add_overwrite_same_id(self):
        store = VectorStore(dimension=3)
        store.add("doc1", [1.0, 0.0, 0.0])
        store.add("doc1", [0.0, 1.0, 0.0])
        assert store.size == 1
        results = store.search([0.0, 1.0, 0.0])
        assert results[0][0] == "doc1"
        assert results[0][1] > 0.99

    def test_search_with_negative_values(self):
        store = VectorStore(dimension=3)
        store.add("doc1", [-1.0, 0.0, 0.0])
        results = store.search([-1.0, 0.0, 0.0])
        assert abs(results[0][1] - 1.0) < 0.001


class TestEncryptionExtra:
    """Additional encryption tests."""

    def test_transit_encrypt_empty(self):
        transit = TransitEncryption()
        assert transit.encrypt("") == ""

    def test_transit_decrypt_empty(self):
        transit = TransitEncryption()
        assert transit.decrypt("") == ""

    def test_transit_get_key_info(self):
        transit = TransitEncryption(key_name="mykey")
        info = transit.get_key_info()
        assert info["name"] == "mykey"
        assert info["version"] == 1

    def test_encryption_at_rest_default_key(self):
        enc = EncryptionAtRest()
        ct = enc.encrypt_field("test")
        pt = enc.decrypt_field(ct)
        assert pt == "test"


class TestWebExtra:
    """Additional web tests."""

    @pytest.mark.asyncio
    async def test_url_reader_title_extraction(self):
        reader = URLReader()
        page = await reader.read("https://example.com/my-page")
        assert page.title != ""

    @pytest.mark.asyncio
    async def test_search_engine_news_url(self):
        engine = SearchEngine()
        results = await engine.news_search("tech")
        assert "news" in results[0].url

    def test_web_result_creation(self):
        from web.schemas import WebResult

        r = WebResult(title="Test", url="http://test.com", snippet="snip")
        assert r.title == "Test"
        assert r.score == 0.0


class TestKnowledgeExtra:
    """Additional knowledge tests."""

    def test_document_creation(self):
        doc = Document(title="T", content="C", doc_type=DocumentType.TXT)
        assert doc.doc_id != ""
        assert doc.created_at > 0

    def test_chunk_creation(self):
        chunk = Chunk(doc_id="d1", content="text", index=0)
        assert chunk.chunk_id != ""

    def test_search_result_creation(self):
        sr = SearchResult(chunk_id="c1", doc_id="d1", content="text", score=0.9)
        assert sr.score == 0.9

    def test_citation_creation(self):
        cit = Citation(source="web", title="Page", chunk_id="c1", relevance=0.8)
        assert cit.relevance == 0.8

    def test_document_type_values(self):
        assert DocumentType.PDF == "pdf"
        assert DocumentType.MARKDOWN == "markdown"
        assert DocumentType.HTML == "html"
        assert DocumentType.URL == "url"
        assert DocumentType.TXT == "txt"


class TestAgentIntelligenceExtra:
    """Additional agent intelligence tests."""

    @pytest.mark.asyncio
    async def test_delegate_with_learned_strategy(self):
        ai = AgentIntelligence()
        ai.record_strategy("coder", "write code", "completed fast", True)
        ai.record_strategy("tester", "write code", "slow", False)
        best = await ai.delegate_dynamically("write code", ["coder", "tester"])
        assert best == "coder"

    def test_shared_memory_via_intelligence(self):
        ai = AgentIntelligence()
        stats = ai.get_stats()
        assert "memory_stats" in stats
        assert "strategy_success_rate" in stats


class TestIntegrationExtra:
    """Additional integration tests to reach 400+."""

    @pytest.mark.asyncio
    async def test_unified_ai_stream_gemini(self):
        mgr = ProviderManager()
        mgr.register(GeminiProvider())
        ai = UnifiedAI(mgr)
        req = AIRequest(messages=[AIMessage(role="user", content="stream test")])
        chunks = [c async for c in ai.stream(req)]
        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_knowledge_engine_stats_update(self):
        engine = KnowledgeEngine()
        await engine.ingest("Doc A", "content a")
        await engine.ingest("Doc B", "content b")
        stats = engine.get_stats()
        assert stats["documents"] == 2

    @pytest.mark.asyncio
    async def test_semantic_search_with_knowledge(self):
        emb = SimpleEmbedding(dimension=128)
        store = VectorStore(dimension=128)
        ss = SemanticSearch(emb, store)
        await ss.index("k1", "artificial intelligence neural networks")
        await ss.index("k2", "cooking recipes and food")
        results = await ss.search("neural networks AI")
        assert results[0]["doc_id"] == "k1"

    @pytest.mark.asyncio
    async def test_provider_switch_mid_session(self):
        mgr = ProviderManager()
        mgr.register(OpenAIProvider())
        mgr.register(ClaudeProvider())
        ai = UnifiedAI(mgr)
        r1 = await ai.complete(
            AIRequest(messages=[AIMessage(role="user", content="q1")], provider="openai")
        )
        r2 = await ai.complete(
            AIRequest(messages=[AIMessage(role="user", content="q2")], provider="claude")
        )
        assert r1.provider == "openai"
        assert r2.provider == "claude"

    def test_vault_and_compliance_integration(self):
        vault = VaultClient(namespace="sec")
        vault.write_secret("keys/master", {"key": "value"})
        auditor = ComplianceAuditor()
        checks = auditor.run_all()
        assert all(c.passed for c in checks)
        health = vault.get_health()
        assert health["secrets_count"] == 1

    @pytest.mark.asyncio
    async def test_chunking_in_knowledge_pipeline(self):
        engine = KnowledgeEngine()
        doc_id = await engine.ingest("Long Doc", "Section about AI. " * 50)
        assert await engine.get_document(doc_id) is not None
