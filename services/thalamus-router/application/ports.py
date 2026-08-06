"""Abstract port interfaces for the Thalamus Router service.

Defines the contracts for intent classification, request routing,
and load-aware instance selection.
"""

from abc import ABC, abstractmethod
from typing import Any

from domain.models import IntentCategory, RoutingDecision


class ThalamusRouterPort(ABC):
    """Primary port for the Thalamus Router.

    Defines the contract for classifying intent, routing requests,
    and performing downstream service health checks.
    """

    @abstractmethod
    async def classify_intent(self, content: str, context: dict[str, Any]) -> IntentCategory:
        """Classify the intent of incoming content.

        Analyzes the request content and context to determine which
        IntentCategory best describes the user's intention.

        Args:
            content: The user's input text to classify.
            context: Additional contextual information (e.g., session history).

        Returns:
            The classified IntentCategory.
        """
        ...

    @abstractmethod
    async def route(self, request: dict[str, Any]) -> RoutingDecision:
        """Determine routing for a request.

        Produces a complete routing decision including target service,
        intent, priority, required agents, and fallback options.

        Args:
            request: The request payload to route (content, context, user info).

        Returns:
            A RoutingDecision with all routing information.
        """
        ...

    @abstractmethod
    async def health_check(self) -> dict[str, bool]:
        """Check health of all downstream services.

        Performs health checks on all services that the router
        can route to, returning a map of service name to health status.

        Returns:
            Dictionary mapping service names to their health status (True=healthy).
        """
        ...


class LoadBalancerPort(ABC):
    """Port for load-aware routing decisions.

    Infrastructure adapters implement this port to provide
    real-time load information for service instance selection.
    """

    @abstractmethod
    async def get_service_load(self, service_name: str) -> float:
        """Get current load factor for a service.

        Args:
            service_name: Name of the service to check.

        Returns:
            Load factor between 0.0 (idle) and 1.0 (fully loaded).
        """
        ...

    @abstractmethod
    async def select_instance(self, service_name: str) -> str:
        """Select the least-loaded instance of a service.

        Args:
            service_name: Name of the service to select an instance from.

        Returns:
            The endpoint URL or identifier of the selected instance.
        """
        ...
