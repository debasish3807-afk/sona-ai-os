"""Prompt Guard middleware for pre-processing AI inputs.

Provides configurable sensitivity levels and integration with the
AI safety service for blocking/flagging unsafe content.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import structlog

from sona_security.infrastructure.ai_safety import AISafetyService

logger = structlog.get_logger()


class SensitivityLevel(StrEnum):
    """Sensitivity levels for the prompt guard."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    STRICT = "strict"


@dataclass
class GuardResult:
    """Result of a prompt guard check."""

    allowed: bool
    content: str
    reason: str | None = None
    threat_type: str | None = None
    sensitivity_level: str = "medium"
    flagged: bool = False


@dataclass
class PromptGuardConfig:
    """Configuration for the prompt guard."""

    sensitivity: SensitivityLevel = SensitivityLevel.MEDIUM
    block_on_detection: bool = True
    log_all_inputs: bool = False
    max_input_length: int = 50000
    allowed_patterns: list[str] = field(default_factory=list)


class PromptGuard:
    """Prompt guard middleware for AI input pre-processing."""

    def __init__(
        self,
        ai_safety: AISafetyService,
        config: PromptGuardConfig | None = None,
    ) -> None:
        self._ai_safety = ai_safety
        self._config = config or PromptGuardConfig()
        self._blocked_count: int = 0
        self._flagged_count: int = 0
        self._processed_count: int = 0

    @property
    def stats(self) -> dict[str, int]:
        """Get guard processing statistics."""
        return {
            "blocked": self._blocked_count,
            "flagged": self._flagged_count,
            "processed": self._processed_count,
        }

    async def process_input(
        self, content: str, user_id: str = "", metadata: dict[str, Any] | None = None
    ) -> GuardResult:
        """Process input content through safety checks.

        Returns:
            GuardResult indicating whether the content is allowed.
        """
        self._processed_count += 1

        # Length check
        if len(content) > self._config.max_input_length:
            self._blocked_count += 1
            return GuardResult(
                allowed=False,
                content=content,
                reason="Input exceeds maximum length",
                sensitivity_level=self._config.sensitivity.value,
            )

        # Run AI safety checks
        is_safe, reason = await self._ai_safety.check_input(content)

        if not is_safe:
            if self._config.block_on_detection:
                self._blocked_count += 1
                await self._ai_safety.audit_log(
                    {
                        "event_type": "prompt_blocked",
                        "user_id": user_id,
                        "reason": reason,
                        "sensitivity": self._config.sensitivity.value,
                    }
                )
                return GuardResult(
                    allowed=False,
                    content=content,
                    reason=reason,
                    threat_type=reason,
                    sensitivity_level=self._config.sensitivity.value,
                )
            # Flag but don't block
            self._flagged_count += 1
            await self._ai_safety.audit_log(
                {
                    "event_type": "prompt_flagged",
                    "user_id": user_id,
                    "reason": reason,
                    "sensitivity": self._config.sensitivity.value,
                }
            )
            return GuardResult(
                allowed=True,
                content=content,
                reason=reason,
                threat_type=reason,
                sensitivity_level=self._config.sensitivity.value,
                flagged=True,
            )

        # Log if configured
        if self._config.log_all_inputs:
            await self._ai_safety.audit_log(
                {
                    "event_type": "prompt_processed",
                    "user_id": user_id,
                    "outcome": "safe",
                }
            )

        return GuardResult(
            allowed=True,
            content=content,
            sensitivity_level=self._config.sensitivity.value,
        )

    async def process_output(self, content: str, user_id: str = "") -> GuardResult:
        """Process AI output content through safety checks."""
        is_safe, reason = await self._ai_safety.check_output(content)

        if not is_safe:
            self._blocked_count += 1
            await self._ai_safety.audit_log(
                {
                    "event_type": "output_blocked",
                    "user_id": user_id,
                    "reason": reason,
                }
            )
            return GuardResult(
                allowed=False,
                content=content,
                reason=reason,
                threat_type=reason,
                sensitivity_level=self._config.sensitivity.value,
            )

        return GuardResult(
            allowed=True,
            content=content,
            sensitivity_level=self._config.sensitivity.value,
        )
