"""Alibaba Qwen provider — Qwen-Plus, Qwen-Turbo, Qwen-Max.

OpenAI-compatible API via DashScope. Env var: QWEN_API_KEY
"""

from __future__ import annotations

from providers.capabilities import (
    Capability,
    CapabilityDescriptor,
    CapabilityLevel,
    CapabilitySet,
)
from providers.config import QwenConfig
from providers.openai_compat import OpenAICompatProvider
from providers.types import ProviderID


class QwenProvider(OpenAICompatProvider):
    """Alibaba Qwen provider — qwen-plus, qwen-turbo, qwen-max.

    Capabilities: chat, streaming, code generation.
    Authentication: QWEN_API_KEY environment variable.
    """

    def __init__(self, config: QwenConfig | None = None) -> None:
        cfg = config or QwenConfig()
        capabilities = CapabilitySet(
            provider_id=ProviderID.QWEN,
            capabilities=[
                CapabilityDescriptor(Capability.CHAT_COMPLETION, CapabilityLevel.ADVANCED),
                CapabilityDescriptor(Capability.STREAMING, CapabilityLevel.ADVANCED),
                CapabilityDescriptor(Capability.CODE_GENERATION, CapabilityLevel.INTERMEDIATE),
            ],
        )
        super().__init__(
            config=cfg,
            provider_id=ProviderID.QWEN,
            display_name="Alibaba Qwen",
            capabilities=capabilities,
            supports_tools_flag=False,
            supports_vision_flag=False,
        )
