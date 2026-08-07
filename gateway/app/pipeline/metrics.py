"""Pipeline execution metrics collection.

Tracks timing and token usage across all pipeline stages for
observability and performance monitoring.
"""

import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class PipelineMetrics:
    """Aggregated metrics for a single pipeline execution."""

    request_latency_ms: float = 0.0
    memory_retrieval_ms: float = 0.0
    thalamus_routing_ms: float = 0.0
    brain_execution_ms: float = 0.0
    llm_inference_ms: float = 0.0
    memory_update_ms: float = 0.0
    total_tokens: int = 0


class MetricsCollector:
    """Collects and reports pipeline metrics for a single request."""

    def __init__(self, request_id: str = "") -> None:
        """Initialize the metrics collector.

        Args:
            request_id: The request ID for correlation.
        """
        self._request_id = request_id
        self._metrics = PipelineMetrics()
        self._start_time: float = time.perf_counter()
        self._stage_times: dict[str, float] = {}

    @property
    def metrics(self) -> PipelineMetrics:
        """Return current collected metrics."""
        return self._metrics

    @asynccontextmanager
    async def track_stage(self, stage_name: str) -> Any:
        """Context manager to track timing for a pipeline stage.

        Args:
            stage_name: Name of the stage being tracked.

        Yields:
            None — timing is recorded on exit.
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._stage_times[stage_name] = elapsed_ms
            self._set_stage_metric(stage_name, elapsed_ms)
            logger.debug(
                "pipeline_stage_completed",
                request_id=self._request_id,
                stage=stage_name,
                elapsed_ms=round(elapsed_ms, 2),
            )

    def record_tokens(self, total_tokens: int) -> None:
        """Record total token usage.

        Args:
            total_tokens: Total tokens consumed.
        """
        self._metrics.total_tokens = total_tokens

    def finalize(self) -> PipelineMetrics:
        """Finalize and return the collected metrics.

        Returns:
            The complete PipelineMetrics for this request.
        """
        self._metrics.request_latency_ms = (time.perf_counter() - self._start_time) * 1000
        logger.info(
            "pipeline_metrics_finalized",
            request_id=self._request_id,
            total_latency_ms=round(self._metrics.request_latency_ms, 2),
            total_tokens=self._metrics.total_tokens,
        )
        return self._metrics

    def _set_stage_metric(self, stage_name: str, elapsed_ms: float) -> None:
        """Map stage name to the appropriate metric field."""
        match stage_name:
            case "memory_retrieval":
                self._metrics.memory_retrieval_ms = elapsed_ms
            case "thalamus_routing":
                self._metrics.thalamus_routing_ms = elapsed_ms
            case "brain_execution":
                self._metrics.brain_execution_ms = elapsed_ms
            case "llm_inference":
                self._metrics.llm_inference_ms = elapsed_ms
            case "memory_update":
                self._metrics.memory_update_ms = elapsed_ms
