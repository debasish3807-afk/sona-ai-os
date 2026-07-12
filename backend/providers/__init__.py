"""AI Provider System for Sona AI OS.

Provides a unified interface for interacting with multiple AI
providers (OpenAI, Claude, Gemini, Groq, DeepSeek, Qwen,
Mistral, Ollama) with automatic selection, fallback chains,
health monitoring, and capability-based routing.
"""

from providers.base import BaseProvider
from providers.capabilities import (
    Capability,
    CapabilityDescriptor,
    CapabilityLevel,
    CapabilityRequirement,
    CapabilitySet,
)
from providers.claude_provider import ClaudeProvider
from providers.config import (
    ClaudeConfig,
    DeepSeekConfig,
    GeminiConfig,
    GroqConfig,
    MistralConfig,
    OllamaConfig,
    OpenAIConfig,
    ProviderConfig,
    QwenConfig,
    RateLimitConfig,
    RetryConfig,
)
from providers.deepseek_provider import DeepSeekProvider
from providers.exceptions import (
    AllProvidersFailed,
    ContentFilterError,
    InvalidRequestError,
    ModelNotFoundError,
    ModelOverloadedError,
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    QuotaExceededError,
)
from providers.factory import ProviderFactory
from providers.gemini_provider import GeminiProvider
from providers.groq_provider import GroqProvider
from providers.health import (
    CircuitBreakerConfig,
    CircuitState,
    HealthCheckResult,
    HealthMonitor,
    HealthState,
    ProviderHealthStatus,
)
from providers.manager import (
    ProviderManager,
    ProviderManagerConfig,
)
from providers.mistral_provider import MistralProvider
from providers.ollama_provider import OllamaProvider

# Provider implementations
from providers.openai_provider import OpenAIProvider
from providers.qwen_provider import QwenProvider
from providers.registry import (
    ProviderEntry,
    ProviderRegistry,
)
from providers.types import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    FinishReason,
    MessageRole,
    ModelInfo,
    ModelType,
    ProviderID,
    StreamChunk,
    StreamEvent,
    TokenUsage,
)

__all__ = [
    # Base
    "BaseProvider",
    # Capabilities
    "Capability",
    "CapabilityDescriptor",
    "CapabilityLevel",
    "CapabilityRequirement",
    "CapabilitySet",
    # Config
    "ClaudeConfig",
    "DeepSeekConfig",
    "GeminiConfig",
    "GroqConfig",
    "MistralConfig",
    "OllamaConfig",
    "OpenAIConfig",
    "ProviderConfig",
    "QwenConfig",
    "RateLimitConfig",
    "RetryConfig",
    # Exceptions
    "AllProvidersFailed",
    "ContentFilterError",
    "InvalidRequestError",
    "ModelNotFoundError",
    "ModelOverloadedError",
    "ProviderAuthenticationError",
    "ProviderConnectionError",
    "ProviderError",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
    "QuotaExceededError",
    # Factory
    "ProviderFactory",
    # Health
    "CircuitBreakerConfig",
    "CircuitState",
    "HealthCheckResult",
    "HealthMonitor",
    "HealthState",
    "ProviderHealthStatus",
    # Manager
    "ProviderManager",
    "ProviderManagerConfig",
    # Registry
    "ProviderEntry",
    "ProviderRegistry",
    # Types
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "FinishReason",
    "MessageRole",
    "ModelInfo",
    "ModelType",
    "ProviderID",
    "StreamChunk",
    "StreamEvent",
    "TokenUsage",
    # Providers
    "OpenAIProvider",
    "GeminiProvider",
    "OllamaProvider",
    "ClaudeProvider",
    "GroqProvider",
    "DeepSeekProvider",
    "QwenProvider",
    "MistralProvider",
]
