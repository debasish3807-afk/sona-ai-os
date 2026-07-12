"""Cloud provider tests — validates all provider implementations."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestOpenAIProvider:
    """Test OpenAI provider instantiation and properties."""

    def test_provider_creation(self):
        from providers.openai_provider import OpenAIProvider

        provider = OpenAIProvider()
        assert provider.provider_id.value == "openai"
        assert provider.display_name == "OpenAI"
        assert provider.is_initialized is False

    def test_provider_capabilities(self):
        from providers.openai_provider import OpenAIProvider

        provider = OpenAIProvider()
        assert provider.supports_streaming() is True
        assert provider.supports_tools() is True
        assert provider.supports_vision() is True
        assert provider.supports_function_calling() is True

    def test_provider_default_model(self):
        from providers.openai_provider import OpenAIProvider

        provider = OpenAIProvider()
        assert provider.config.default_model == "gpt-4o"


class TestClaudeProvider:
    """Test Claude provider instantiation and properties."""

    def test_provider_creation(self):
        from providers.claude_provider import ClaudeProvider

        provider = ClaudeProvider()
        assert provider.provider_id.value == "claude"
        assert provider.display_name == "Anthropic Claude"
        assert provider.is_initialized is False

    def test_provider_capabilities(self):
        from providers.claude_provider import ClaudeProvider

        provider = ClaudeProvider()
        assert provider.supports_streaming() is True
        assert provider.supports_tools() is True
        assert provider.supports_vision() is True

    def test_static_model_catalog(self):
        from providers.claude_provider import CLAUDE_MODELS

        assert len(CLAUDE_MODELS) >= 3
        assert any("sonnet" in m.model_id for m in CLAUDE_MODELS)


class TestGeminiProvider:
    """Test Gemini provider instantiation and properties."""

    def test_provider_creation(self):
        from providers.gemini_provider import GeminiProvider

        provider = GeminiProvider()
        assert provider.provider_id.value == "gemini"
        assert provider.display_name == "Google Gemini"
        assert provider.is_initialized is False

    def test_provider_capabilities(self):
        from providers.gemini_provider import GeminiProvider

        provider = GeminiProvider()
        assert provider.supports_streaming() is True
        assert provider.supports_tools() is True
        assert provider.supports_vision() is True

    def test_static_model_catalog(self):
        from providers.gemini_provider import GEMINI_MODELS

        assert len(GEMINI_MODELS) >= 3
        assert any("flash" in m.model_id for m in GEMINI_MODELS)


class TestDeepSeekProvider:
    """Test DeepSeek provider."""

    def test_provider_creation(self):
        from providers.deepseek_provider import DeepSeekProvider

        provider = DeepSeekProvider()
        assert provider.provider_id.value == "deepseek"
        assert provider.display_name == "DeepSeek"
        assert provider.config.default_model == "deepseek-chat"

    def test_provider_capabilities(self):
        from providers.deepseek_provider import DeepSeekProvider

        provider = DeepSeekProvider()
        assert provider.supports_streaming() is True
        assert provider.supports_tools() is True


class TestMistralProvider:
    """Test Mistral provider."""

    def test_provider_creation(self):
        from providers.mistral_provider import MistralProvider

        provider = MistralProvider()
        assert provider.provider_id.value == "mistral"
        assert provider.display_name == "Mistral AI"
        assert provider.config.default_model == "mistral-large-latest"

    def test_provider_capabilities(self):
        from providers.mistral_provider import MistralProvider

        provider = MistralProvider()
        assert provider.supports_streaming() is True
        assert provider.supports_tools() is True


class TestQwenProvider:
    """Test Qwen provider."""

    def test_provider_creation(self):
        from providers.qwen_provider import QwenProvider

        provider = QwenProvider()
        assert provider.provider_id.value == "qwen"
        assert provider.display_name == "Alibaba Qwen"
        assert provider.config.default_model == "qwen-plus"


class TestCostTracker:
    """Test cost estimation."""

    def test_known_model_cost(self):
        from providers.cost_tracker import estimate_cost
        from providers.types import TokenUsage

        usage = TokenUsage(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)
        cost = estimate_cost("gpt-4o", usage)
        assert cost.total_cost_usd > 0
        assert cost.input_cost_usd > 0
        assert cost.output_cost_usd > 0

    def test_unknown_model_zero_cost(self):
        from providers.cost_tracker import estimate_cost
        from providers.types import TokenUsage

        usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        cost = estimate_cost("unknown-model-xyz", usage)
        assert cost.total_cost_usd == 0.0

    def test_deepseek_cost(self):
        from providers.cost_tracker import estimate_cost
        from providers.types import TokenUsage

        usage = TokenUsage(
            prompt_tokens=1_000_000, completion_tokens=1_000_000, total_tokens=2_000_000
        )
        cost = estimate_cost("deepseek-chat", usage)
        assert 0.1 < cost.input_cost_usd < 1.0
        assert 0.1 < cost.output_cost_usd < 1.0


class TestHTTPClient:
    """Test provider HTTP client utilities."""

    def test_load_api_key_missing(self):
        from providers.http_client import load_api_key

        result = load_api_key("NONEXISTENT_KEY_XYZ_12345")
        assert result is None

    def test_provider_client_creation(self):
        from providers.config import OpenAIConfig
        from providers.http_client import ProviderClient

        config = OpenAIConfig()
        client = ProviderClient(config, api_key="test-key")
        assert client.base_url == "https://api.openai.com/v1"
        assert client.api_key == "test-key"


class TestAutoDiscovery:
    """Test provider auto-discovery logic."""

    def test_orchestrator_creation(self):
        from brain.orchestrator import BrainOrchestrator

        brain = BrainOrchestrator()
        assert brain.is_initialized is False
        assert brain.available_providers == {}

    def test_failover_providers_list(self):
        """_get_failover_providers excludes specified provider."""
        from brain.orchestrator import BrainOrchestrator
        from providers.ollama_provider import OllamaProvider

        brain = BrainOrchestrator()
        # Simulate providers
        p1 = OllamaProvider()
        brain._providers = {"ollama": p1}
        fallbacks = brain._get_failover_providers("ollama")
        assert fallbacks == []

    def test_select_provider_explicit(self):
        """Explicit provider selection works."""
        from brain.orchestrator import BrainOrchestrator
        from providers.ollama_provider import OllamaProvider

        brain = BrainOrchestrator()
        p1 = OllamaProvider()
        brain._providers = {"ollama": p1}
        selected = brain._select_provider("ollama")
        assert selected is p1
