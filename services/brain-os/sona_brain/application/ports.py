"""Abstract port interfaces for the Brain OS service.

Defines the contracts that infrastructure adapters must implement
to provide orchestration and pipeline stage capabilities.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from sona_brain.domain.models import BrainRequest, BrainResponse


class BrainOrchestratorPort(ABC):
    """Primary port for the Brain OS orchestrator.

    Defines the contract for executing the full brain pipeline,
    streaming responses, and managing session context. All concrete
    implementations must satisfy this interface.
    """

    @abstractmethod
    async def execute(self, request: BrainRequest) -> BrainResponse:
        """Execute the full brain pipeline for a request.

        Orchestrates memory retrieval, model selection, agent delegation,
        and response generation through the complete pipeline.

        Args:
            request: The brain request containing messages, session, and config.

        Returns:
            A BrainResponse with generated content and usage metrics.
        """
        ...

    @abstractmethod
    async def execute_stream(self, request: BrainRequest) -> AsyncIterator[str]:
        """Stream the brain pipeline execution.

        Executes the same pipeline as execute() but yields response tokens
        as they are generated for real-time delivery.

        Args:
            request: The brain request containing messages, session, and config.

        Yields:
            String tokens/chunks as they are generated.
        """
        ...

    @abstractmethod
    async def get_session_context(self, session_id: str) -> dict[str, Any]:
        """Retrieve full context for a session.

        Returns the accumulated context for a given session including
        conversation history, memory state, and active configuration.

        Args:
            session_id: The session identifier to look up.

        Returns:
            A dictionary containing the full session context.
        """
        ...


class PipelineStagePort(ABC):
    """Port for individual pipeline stages (composable).

    Each stage in the Brain OS pipeline implements this interface,
    allowing stages to be composed, reordered, and conditionally skipped.
    """

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute this pipeline stage, enriching the context.

        Takes the current pipeline context, performs its processing,
        and returns an updated context dict[str, Any] for the next stage.

        Args:
            context: The current pipeline context dictionary.

        Returns:
            An enriched context dictionary with this stage's contributions.
        """
        ...

    @abstractmethod
    def should_skip(self, context: dict[str, Any]) -> bool:
        """Determine if this stage should be skipped.

        Evaluates the current context to decide whether this stage
        is relevant for the current request.

        Args:
            context: The current pipeline context dictionary.

        Returns:
            True if this stage should be skipped, False otherwise.
        """
        ...
