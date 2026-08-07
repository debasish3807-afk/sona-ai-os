"""Abstract port interfaces for the Evaluation OS service.

Defines the contracts that infrastructure adapters must implement
to provide quality evaluation, metric collection, and regression testing capabilities.
"""

from abc import ABC, abstractmethod
from typing import Any

from sona_evaluation.domain.models import EvaluationRequest, MetricResult, QualityReport


class QualityEvaluationPort(ABC):
    """Primary port for quality evaluation operations.

    Defines the contract for running quality evaluations against
    AI model outputs, system responses, or generated content.
    All concrete implementations (e.g., custom scorers, LLM judges)
    must satisfy this interface.
    """

    @abstractmethod
    async def evaluate(self, request: EvaluationRequest) -> QualityReport:
        """Evaluate a single input against quality criteria.

        Args:
            request: The evaluation request containing input data and evaluation type.

        Returns:
            A QualityReport with metric results and overall assessment.
        """
        ...

    @abstractmethod
    async def evaluate_batch(self, requests: list[EvaluationRequest]) -> list[QualityReport]:
        """Evaluate multiple inputs in batch.

        Args:
            requests: A list of evaluation requests to process.

        Returns:
            A list of QualityReport instances, one per input request.
        """
        ...


class MetricCollectorPort(ABC):
    """Port for collecting and retrieving evaluation metrics.

    Infrastructure adapters implement this port to store metric measurements
    and retrieve historical metric data for trend analysis and dashboards.
    """

    @abstractmethod
    async def collect(
        self, metric_name: str, value: float, tags: dict[str, Any] | None = None
    ) -> None:
        """Record a metric measurement.

        Args:
            metric_name: The name/identifier of the metric to record.
            value: The numeric value to record.
            tags: Optional key-value tags for metric categorization.
        """
        ...

    @abstractmethod
    async def get_metrics(
        self, metric_name: str, time_range: tuple[Any, ...] | None = None
    ) -> list[MetricResult]:
        """Retrieve historical metric measurements.

        Args:
            metric_name: The name of the metric to retrieve.
            time_range: Optional time range tuple[Any, ...] (start, end) to filter results.

        Returns:
            A list of MetricResult instances within the specified range.
        """
        ...


class RegressionTestPort(ABC):
    """Port for running regression test suites and comparing results.

    Infrastructure adapters implement this port to execute predefined
    test suites and compare current results against baseline measurements.
    """

    @abstractmethod
    async def run_suite(self, suite_id: str) -> QualityReport:
        """Run a predefined regression test suite.

        Args:
            suite_id: Identifier of the test suite to execute.

        Returns:
            A QualityReport summarizing the suite execution results.
        """
        ...

    @abstractmethod
    async def compare(self, baseline_id: str, current_id: str) -> QualityReport:
        """Compare current evaluation results against a baseline.

        Args:
            baseline_id: Identifier of the baseline evaluation report.
            current_id: Identifier of the current evaluation report.

        Returns:
            A QualityReport detailing the comparison, highlighting regressions.
        """
        ...
