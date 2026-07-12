"""OpenAI provider — GPT-4o, GPT-4, o1 series.

Uses the shared OpenAI-compatible base with OpenAI-specific configuration.
Env var: OPENAI_API_KEY
"""

from __future__ import annotations

from providers.capabilities import (
    Capability,
    CapabilityDescriptor,
    CapabilityLevel,
    CapabilitySet,
)
from providers.config import OpenAIConfig
from providers.openai_compat import OpenAICompatProvider
from providers.types import ProviderID


class OpenAIProvider(OpenAICompatProvider):
    """OpenAI provider — GPT-4o, GPT-4-turbo, o1, o1-mini.

    Capabilities: chat, streaming, embeddings, tool calling, vision, JSON mode.
    Authentication: OPENAI_API_KEY environment variable.
    """

    def __init__(self, config: OpenAIConfig | None = None) -> None:
        cfg = config or OpenAIConfig()
        capabilities = CapabilitySet(
            provider_id=ProviderID.OPENAI,
            capabilities=[
                CapabilityDescriptor(Capability.CHAT_COMPLETION, CapabilityLevel.EXPERT),
                CapabilityDescriptor(Capability.STREAMING, CapabilityLevel.EXPERT),
                CapabilityDescriptor(Capability.EMBEDDINGS, CapabilityLevel.EXPERT),
                CapabilityDescriptor(Capability.CODE_GENERATION, CapabilityLevel.EXPERT),
                CapabilityDescriptor(Capability.FUNCTION_CALLING, CapabilityLevel.EXPERT),
            ],
        )
        super().__init__(
            config=cfg,
            provider_id=ProviderID.OPENAI,
            display_name="OpenAI",
            capabilities=capabilities,
            supports_tools_flag=True,
            supports_vision_flag=True,
        )
