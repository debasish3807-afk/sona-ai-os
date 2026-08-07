"""Unit tests for Evaluation OS domain models.

Tests verify that all domain models, enums, and dataclasses are correctly
defined, instantiate properly, and enforce immutability.
"""

from dataclasses import FrozenInstanceError

import pytest

from sona_evaluation.domain.models import (
    EvaluationRequest,
    EvaluationType,
    MetricResult,
    MetricStatus,
    QualityReport,
)


class TestEvaluationType:
    """Tests for the EvaluationType enum."""

    def test_all_types_defined(self) -> None:
        """Verify all expected evaluation types are available."""
        assert EvaluationType.QUALITY == "quality"
        assert EvaluationType.ACCURACY == "accuracy"
        assert EvaluationType.LATENCY == "latency"
        assert EvaluationType.SAFETY == "safety"
        assert EvaluationType.REGRESSION == "regression"

    def test_type_count(self) -> None:
        """Verify exactly 5 evaluation types exist."""
        assert len(EvaluationType) == 5

    def test_type_is_str_enum(self) -> None:
        """Verify evaluation types are usable as strings."""
        assert str(EvaluationType.QUALITY) == "quality"
        assert str(EvaluationType.REGRESSION) == "regression"


class TestMetricStatus:
    """Tests for the MetricStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """Verify all expected metric statuses are available."""
        assert MetricStatus.PASS == "pass"
        assert MetricStatus.FAIL == "fail"
        assert MetricStatus.WARNING == "warning"
        assert MetricStatus.SKIPPED == "skipped"

    def test_status_count(self) -> None:
        """Verify exactly 4 metric statuses exist."""
        assert len(MetricStatus) == 4

    def test_status_is_str_enum(self) -> None:
        """Verify statuses are usable as strings."""
        assert str(MetricStatus.PASS) == "pass"
        assert str(MetricStatus.FAIL) == "fail"


class TestEvaluationRequest:
    """Tests for the EvaluationRequest frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        req = EvaluationRequest(
            eval_type=EvaluationType.QUALITY,
            input_data="Sample model output to evaluate",
        )
        assert req.eval_type == EvaluationType.QUALITY
        assert req.input_data == "Sample model output to evaluate"

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        req = EvaluationRequest(
            eval_type=EvaluationType.ACCURACY,
            input_data="test input",
        )
        assert req.expected_output is None
        assert req.model_id is None
        assert req.metadata is None

    def test_with_all_fields(self) -> None:
        """Create with all optional fields."""
        req = EvaluationRequest(
            eval_type=EvaluationType.ACCURACY,
            input_data="What is 2+2?",
            expected_output="4",
            model_id="gpt-4o",
            metadata={"category": "math", "difficulty": "easy"},
        )
        assert req.expected_output == "4"
        assert req.model_id == "gpt-4o"
        assert req.metadata == {"category": "math", "difficulty": "easy"}

    def test_is_frozen(self) -> None:
        """Verify EvaluationRequest is immutable."""
        req = EvaluationRequest(
            eval_type=EvaluationType.QUALITY,
            input_data="test",
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            req.input_data = "changed"  # type: ignore[misc]


class TestMetricResult:
    """Tests for the MetricResult frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        result = MetricResult(
            name="accuracy",
            value=0.95,
            status=MetricStatus.PASS,
        )
        assert result.name == "accuracy"
        assert result.value == 0.95
        assert result.status == MetricStatus.PASS

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        result = MetricResult(
            name="latency_p99",
            value=150.0,
            status=MetricStatus.WARNING,
        )
        assert result.threshold is None
        assert result.details is None

    def test_with_all_fields(self) -> None:
        """Create with all optional fields."""
        result = MetricResult(
            name="coherence",
            value=0.82,
            status=MetricStatus.PASS,
            threshold=0.75,
            details="Score exceeds minimum coherence threshold",
        )
        assert result.threshold == 0.75
        assert result.details == "Score exceeds minimum coherence threshold"

    def test_is_frozen(self) -> None:
        """Verify MetricResult is immutable."""
        result = MetricResult(
            name="test",
            value=1.0,
            status=MetricStatus.PASS,
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            result.value = 0.5  # type: ignore[misc]


class TestQualityReport:
    """Tests for the QualityReport frozen dataclass."""

    def test_creation_with_passing_metrics(self) -> None:
        """Create a passing quality report."""
        metrics = [
            MetricResult(name="accuracy", value=0.95, status=MetricStatus.PASS, threshold=0.9),
            MetricResult(name="coherence", value=0.88, status=MetricStatus.PASS, threshold=0.8),
        ]
        report = QualityReport(
            evaluation_id="eval-001",
            metrics=metrics,
            overall_score=0.92,
            passed=True,
            summary="All quality metrics passed.",
        )
        assert report.evaluation_id == "eval-001"
        assert len(report.metrics) == 2
        assert report.overall_score == 0.92
        assert report.passed is True
        assert report.summary == "All quality metrics passed."

    def test_creation_with_failing_metrics(self) -> None:
        """Create a failing quality report."""
        metrics = [
            MetricResult(name="accuracy", value=0.6, status=MetricStatus.FAIL, threshold=0.9),
            MetricResult(name="safety", value=0.99, status=MetricStatus.PASS, threshold=0.95),
        ]
        report = QualityReport(
            evaluation_id="eval-002",
            metrics=metrics,
            overall_score=0.45,
            passed=False,
            summary="Accuracy below threshold.",
        )
        assert report.passed is False
        assert report.overall_score == 0.45

    def test_is_frozen(self) -> None:
        """Verify QualityReport is immutable."""
        report = QualityReport(
            evaluation_id="eval-003",
            metrics=[],
            overall_score=1.0,
            passed=True,
            summary="Empty evaluation.",
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            report.passed = False  # type: ignore[misc]

    def test_empty_metrics_list(self) -> None:
        """Verify a report can be created with an empty metrics list."""
        report = QualityReport(
            evaluation_id="eval-empty",
            metrics=[],
            overall_score=0.0,
            passed=False,
            summary="No metrics collected.",
        )
        assert report.metrics == []
        assert report.overall_score == 0.0
