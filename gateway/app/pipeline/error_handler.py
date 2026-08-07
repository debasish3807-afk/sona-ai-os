"""Pipeline error handling and recovery.

Provides graceful degradation for failures in the pipeline,
including provider errors, memory failures, and timeouts.
"""

import structlog

from app.pipeline.metrics import PipelineMetrics

logger = structlog.get_logger()


class PipelineErrorHandler:
    """Handles failures in the pipeline with graceful degradation.

    Provides recovery strategies for different failure modes,
    ensuring the user always gets a reasonable response.
    """

    # Default error content returned when all recovery fails
    FALLBACK_CONTENT = (
        "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."
    )

    async def handle_provider_failure(
        self,
        error: Exception,
        request_id: str,
        messages: list[dict[str, str]],
    ) -> str | None:
        """Handle LLM provider failure with fallback.

        Attempts to provide a graceful response when the primary
        provider is unavailable.

        Args:
            error: The exception from the provider.
            request_id: Request ID for logging correlation.
            messages: The original messages for potential retry.

        Returns:
            Fallback content string, or None if unrecoverable.
        """
        logger.error(
            "pipeline_provider_failure",
            request_id=request_id,
            error=str(error),
            error_type=type(error).__name__,
        )
        return self.FALLBACK_CONTENT

    async def handle_memory_failure(
        self,
        error: Exception,
        request_id: str,
    ) -> None:
        """Handle memory system failure (non-critical).

        Memory failures are logged but do not block the pipeline.
        The request proceeds without memory context.

        Args:
            error: The exception from the memory system.
            request_id: Request ID for logging correlation.
        """
        logger.warning(
            "pipeline_memory_failure",
            request_id=request_id,
            error=str(error),
            error_type=type(error).__name__,
        )

    async def handle_timeout(
        self,
        error: Exception,
        request_id: str,
        elapsed_ms: float,
    ) -> str | None:
        """Handle pipeline timeout.

        Returns a timeout-specific message to the user.

        Args:
            error: The timeout exception.
            request_id: Request ID for logging correlation.
            elapsed_ms: Time elapsed before timeout.

        Returns:
            Timeout message content.
        """
        logger.error(
            "pipeline_timeout",
            request_id=request_id,
            elapsed_ms=round(elapsed_ms, 2),
            error=str(error),
        )
        return "The request took too long to process. Please try a shorter or simpler message."

    async def handle_routing_failure(
        self,
        error: Exception,
        request_id: str,
    ) -> None:
        """Handle THALAMUS routing failure (non-critical).

        Routing failures cause the pipeline to fall back to direct
        Brain OS execution without a THALAMUS plan.

        Args:
            error: The exception from the routing engine.
            request_id: Request ID for logging correlation.
        """
        logger.warning(
            "pipeline_routing_failure",
            request_id=request_id,
            error=str(error),
            error_type=type(error).__name__,
        )

    def create_error_metrics(self, stage: str, elapsed_ms: float) -> PipelineMetrics:
        """Create metrics for a failed pipeline execution.

        Args:
            stage: The stage where the failure occurred.
            elapsed_ms: Time elapsed until failure.

        Returns:
            PipelineMetrics with the failure timing.
        """
        metrics = PipelineMetrics(request_latency_ms=elapsed_ms)
        match stage:
            case "memory_retrieval":
                metrics.memory_retrieval_ms = elapsed_ms
            case "thalamus_routing":
                metrics.thalamus_routing_ms = elapsed_ms
            case "brain_execution":
                metrics.brain_execution_ms = elapsed_ms
        return metrics
