"""Domain models for the Evaluation OS service.

Defines the data structures used by the Evaluation OS for quality evaluation,
metric collection, and regression testing operations.
"""

from dataclasses import dataclass, field
from enum import StrEnum


class EvaluationType(StrEnum):
    """Types of evaluations that can be performed.

    Determines the category of quality assessment to run against
    AI model outputs or system components.
    """

    QUALITY = "quality"
    ACCURACY = "accuracy"
    LATENCY = "latency"
    SAFETY = "safety"
    REGRESSION = "regression"


class MetricStatus(StrEnum):
    """Status of an individual metric evaluation.

    Indicates whether a metric measurement meets, fails, or partially
    meets its defined threshold.
    """

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class EvaluationRequest:
    """Request for an evaluation operation.

    Attributes:
        eval_type: The type of evaluation to perform.
        input_data: The input data to evaluate (e.g., prompt or response text).
        expected_output: Optional expected output for comparison-based evaluation.
        model_id: Optional identifier of the model being evaluated.
        metadata: Optional additional metadata for the evaluation context.
    """

    eval_type: EvaluationType
    input_data: str
    expected_output: str | None = None
    model_id: str | None = None
    metadata: dict | None = None


@dataclass(frozen=True)
class MetricResult:
    """Result of a single metric measurement.

    Attributes:
        name: The name/identifier of the metric.
        value: The numeric value of the metric measurement.
        status: Whether the metric passed, failed, or triggered a warning.
        threshold: Optional threshold value used for pass/fail determination.
        details: Optional human-readable details about the measurement.
    """

    name: str
    value: float
    status: MetricStatus
    threshold: float | None = None
    details: str | None = None


@dataclass(frozen=True)
class QualityReport:
    """Comprehensive report from a quality evaluation run.

    Attributes:
        evaluation_id: Unique identifier for this evaluation run.
        metrics: List of individual metric results from the evaluation.
        overall_score: Aggregated score across all metrics (0.0 to 1.0).
        passed: Whether the evaluation passed all required thresholds.
        summary: Human-readable summary of the evaluation results.
    """

    evaluation_id: str
    metrics: list[MetricResult]
    overall_score: float
    passed: bool
    summary: str
