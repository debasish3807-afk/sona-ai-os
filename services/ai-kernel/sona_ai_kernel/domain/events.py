"""AI Kernel domain events.

Events emitted during AI Kernel processing to support observability,
auditing, and reactive downstream processing.
"""

from dataclasses import dataclass

from sona_shared.domain.primitives import DomainEvent


@dataclass(frozen=True)
class InferenceStartedEvent(DomainEvent):
    """Emitted when an inference request begins processing."""

    request_id: str = ""
    provider: str = ""
    model_id: str = ""


@dataclass(frozen=True)
class InferenceCompletedEvent(DomainEvent):
    """Emitted when an inference request completes successfully."""

    request_id: str = ""
    provider: str = ""
    model_id: str = ""
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: float = 0.0


@dataclass(frozen=True)
class InferenceFailedEvent(DomainEvent):
    """Emitted when an inference request fails."""

    request_id: str = ""
    provider: str = ""
    model_id: str = ""
    error: str = ""


@dataclass(frozen=True)
class ProviderHealthChangedEvent(DomainEvent):
    """Emitted when a provider's health status changes."""

    provider: str = ""
    healthy: bool = True
