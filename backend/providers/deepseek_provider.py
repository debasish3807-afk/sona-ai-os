"""DeepSeek provider — DeepSeek-Chat, DeepSeek-Reasoner.

OpenAI-compatible API. Env var: DEEPSEEK_API_KEY
"""

from __future__ import annotations

from providers.capabilities import (
    Capability,
    CapabilityDescriptor,
    CapabilityLevel,
    CapabilitySet,
)
from providers.config import DeepSeekConfig
from providers.openai_compat import OpenAICompatProvider
from providers.types import ProviderID


class DeepSeekProvider(OpenAICompatProvider):
    """DeepSeek provider — deepseek-chat, deepseek-reasoner.

    Capabilities: chat, streaming, code generation.
    Authentication: DEEPSEEK_API_KEY environment variable.
    """

    def __init__(self, config: DeepSeekConfig | None = None) -> None:
        cfg = config or DeepSeekConfig()
        capabilities = CapabilitySet(
            provider_id=ProviderID.DEEPSEEK,
            capabilities=[
                CapabilityDescriptor(Capability.CHAT_COMPLETION, CapabilityLevel.EXPERT),
                CapabilityDescriptor(Capability.STREAMING, CapabilityLevel.ADVANCED),
                CapabilityDescriptor(Capability.CODE_GENERATION, CapabilityLevel.EXPERT),
            ],
        )
        super().__init__(
            config=cfg,
            provider_id=ProviderID.DEEPSEEK,
            display_name="DeepSeek",
            capabilities=capabilities,
            supports_tools_flag=True,
            supports_vision_flag=False,
        )
