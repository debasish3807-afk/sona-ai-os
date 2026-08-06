"""Domain models for the Thalamus Router service.

Defines the data structures used for intent classification,
request routing, and load balancing decisions.
"""

from dataclasses import dataclass, field
from enum import StrEnum


class RequestPriority(StrEnum):
    """Priority levels for incoming requests.

    Determines processing order and resource allocation within
    the routing layer.
    """

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


class IntentCategory(StrEnum):
    """Categories for classifying user intent.

    Used by the Thalamus Router to determine which downstream
    service should handle the request.
    """

    CHAT = "chat"
    RESEARCH = "research"
    CODE = "code"
    AUTOMATION = "automation"
    MEMORY = "memory"
    SYSTEM = "system"


@dataclass(frozen=True)
class RoutingDecision:
    """Result of the Thalamus Router's routing analysis.

    Encapsulates the complete routing decision for an incoming request,
    including target service, intent classification, priority, and fallback.

    Attributes:
        target_service: Name of the downstream service to route to.
        intent: Classified intent category of the request.
        priority: Priority level assigned to this request.
        requires_agents: List of agent types needed to fulfill the request.
        estimated_latency_ms: Predicted response latency in milliseconds.
        fallback_service: Optional alternative service if primary is unavailable.
    """

    target_service: str
    intent: IntentCategory
    priority: RequestPriority
    requires_agents: list[str]
    estimated_latency_ms: int
    fallback_service: str | None = None
