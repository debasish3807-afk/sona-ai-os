"""Provider configuration classes.

Environment-based configuration for each AI provider.
API keys and sensitive values are loaded from environment
variables — never hardcoded.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from providers.types import ProviderID


@dataclass
class RetryConfig:
    """Configuration for request retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts.
        initial_delay_seconds: Initial backoff delay.
        max_delay_seconds: Maximum backoff delay.
        exponential_base: Base for exponential backoff.
        retryable_status_codes: HTTP codes that trigger retry.
    """

    max_retries: int = 3
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    retryable_status_codes: List[int] = field(
        default_factory=lambda: [429, 500, 502, 503, 504]
    )



@dataclass
class RateLimitConfig:
    """Configuration for rate limiting.

    Attributes:
        requests_per_minute: Maximum requests per minute.
        tokens_per_minute: Maximum tokens per minute.
        concurrent_requests: Maximum concurrent requests.
    """

    requests_per_minute: int = 60
    tokens_per_minute: int = 100000
    concurrent_requests: int = 10


@dataclass
class ProviderConfig:
    """Base configuration for an AI provider.

    All provider-specific configs should extend this class.
    API keys are loaded from environment variables at runtime.

    Attributes:
        provider_id: Unique provider identifier.
        api_key_env_var: Environment variable name for the API key.
        base_url: Base URL for the provider API.
        api_version: API version string.
        timeout_seconds: Request timeout.
        retry: Retry configuration.
        rate_limit: Rate limiting configuration.
        default_model: Default model to use.
        enabled: Whether this provider is active.
        priority: Selection priority (lower = preferred).
        tags: Tags for categorization.
        metadata: Additional configuration.
    """

    provider_id: ProviderID
    api_key_env_var: str
    base_url: str = ""
    api_version: str = ""
    timeout_seconds: float = 120.0
    retry: RetryConfig = field(default_factory=RetryConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    default_model: str = ""
    enabled: bool = True
    priority: int = 50
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)



@dataclass
class OpenAIConfig(ProviderConfig):
    """OpenAI-specific configuration."""

    provider_id: ProviderID = ProviderID.OPENAI
    api_key_env_var: str = "OPENAI_API_KEY"
    base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-4o"
    organization_env_var: str = "OPENAI_ORGANIZATION"
    project_env_var: str = "OPENAI_PROJECT"


@dataclass
class GeminiConfig(ProviderConfig):
    """Google Gemini-specific configuration."""

    provider_id: ProviderID = ProviderID.GEMINI
    api_key_env_var: str = "GEMINI_API_KEY"
    base_url: str = "https://generativelanguage.googleapis.com/v1"
    default_model: str = "gemini-2.0-flash"


@dataclass
class OllamaConfig(ProviderConfig):
    """Ollama local model configuration."""

    provider_id: ProviderID = ProviderID.OLLAMA
    api_key_env_var: str = "OLLAMA_API_KEY"
    base_url: str = "http://localhost:11434"
    default_model: str = "llama3"
    priority: int = 90  # Lower priority (local fallback)


@dataclass
class ClaudeConfig(ProviderConfig):
    """Anthropic Claude-specific configuration."""

    provider_id: ProviderID = ProviderID.CLAUDE
    api_key_env_var: str = "ANTHROPIC_API_KEY"
    base_url: str = "https://api.anthropic.com/v1"
    api_version: str = "2024-01-01"
    default_model: str = "claude-sonnet-4-20250514"



@dataclass
class GroqConfig(ProviderConfig):
    """Groq-specific configuration."""

    provider_id: ProviderID = ProviderID.GROQ
    api_key_env_var: str = "GROQ_API_KEY"
    base_url: str = "https://api.groq.com/openai/v1"
    default_model: str = "llama-3.3-70b-versatile"


@dataclass
class DeepSeekConfig(ProviderConfig):
    """DeepSeek-specific configuration."""

    provider_id: ProviderID = ProviderID.DEEPSEEK
    api_key_env_var: str = "DEEPSEEK_API_KEY"
    base_url: str = "https://api.deepseek.com/v1"
    default_model: str = "deepseek-chat"


@dataclass
class QwenConfig(ProviderConfig):
    """Alibaba Qwen-specific configuration."""

    provider_id: ProviderID = ProviderID.QWEN
    api_key_env_var: str = "QWEN_API_KEY"
    base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    default_model: str = "qwen-plus"


@dataclass
class MistralConfig(ProviderConfig):
    """Mistral AI-specific configuration."""

    provider_id: ProviderID = ProviderID.MISTRAL
    api_key_env_var: str = "MISTRAL_API_KEY"
    base_url: str = "https://api.mistral.ai/v1"
    default_model: str = "mistral-large-latest"


# Default configurations for all providers
DEFAULT_PROVIDER_CONFIGS: Dict[ProviderID, type] = {
    ProviderID.OPENAI: OpenAIConfig,
    ProviderID.GEMINI: GeminiConfig,
    ProviderID.OLLAMA: OllamaConfig,
    ProviderID.CLAUDE: ClaudeConfig,
    ProviderID.GROQ: GroqConfig,
    ProviderID.DEEPSEEK: DeepSeekConfig,
    ProviderID.QWEN: QwenConfig,
    ProviderID.MISTRAL: MistralConfig,
}
