"""Mistral AI provider — Mistral Large, Small, Codestral.

OpenAI-compatible API. Env var: MISTRAL_API_KEY
"""

from __future__ import annotations

from providers.capabilities import (
    Capability,
    CapabilityDescriptor,
    CapabilityLevel,
    CapabilitySet,
)
from providers.config import MistralConfig
from providers.openai_compat import OpenAICompatProvider
from providers.types import ProviderID


class MistralProvider(OpenAICompatProvider):
    """Mistral AI provider — mistral-large, mistral-small, codestral.

    Capabilities: chat, streaming, code generation, function calling.
    Authentication: MISTRAL_API_KEY environment variable.
    """

    def __init__(self, config: MistralConfig | None = None) -> None:
        cfg = config or MistralConfig()
        capabilities = CapabilitySet(
            provider_id=ProviderID.MISTRAL,
            capabilities=[
                CapabilityDescriptor(Capability.CHAT_COMPLETION, CapabilityLevel.ADVANCED),
                CapabilityDescriptor(Capability.STREAMING, CapabilityLevel.ADVANCED),
                CapabilityDescriptor(Capability.CODE_GENERATION, CapabilityLevel.ADVANCED),
                CapabilityDescriptor(Capability.FUNCTION_CALLING, CapabilityLevel.INTERMEDIATE),
            ],
        )
        super().__init__(
            config=cfg,
            provider_id=ProviderID.MISTRAL,
            display_name="Mistral AI",
            capabilities=capabilities,
            supports_tools_flag=True,
            supports_vision_flag=False,
        )
