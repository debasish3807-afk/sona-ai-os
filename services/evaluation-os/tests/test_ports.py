"""Unit tests for Evaluation OS abstract port interfaces.

Tests verify that port interfaces are correctly defined, enforce
abstractness, and that concrete implementations must satisfy all methods.
"""

import pytest
from application.ports import MetricCollectorPort, QualityEvaluationPort, RegressionTestPort
from domain.models import (
    EvaluationRequest,
    EvaluationType,
    MetricResult,
    MetricStatus,
    QualityReport,
)


class TestQualityEvaluationPort:
    """Tests for the QualityEvaluationPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify QualityEvaluationPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            QualityEvaluationPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = QualityEvaluationPort.__abstractmethods__
        assert "evaluate" in abstract_methods
        assert "evaluate_batch" in abstract_methods

    def test_complete_implementation_is_instantiable(self) -> None:
        """Verify a full implementation can be instantiated."""

        class ConcreteEvaluator(QualityEvaluationPort):
            async def evaluate(self, request: EvaluationRequest) -> QualityReport:
                return QualityReport(
                    evaluation_id="eval-001",
                    metrics=[],
                    overall_score=1.0,
                    passed=True,
                    summary="All good",
                )

            async def evaluate_batch(
                self, requests: list[EvaluationRequest]
            ) -> list[QualityReport]:
                return [
                    QualityReport(
                        evaluation_id=f"eval-{i}",
                        metrics=[],
                        overall_score=1.0,
                        passed=True,
                        summary="Batch item passed",
                    )
                    for i in range(len(requests))
                ]

        evaluator = ConcreteEvaluator()
        assert isinstance(evaluator, QualityEvaluationPort)

    @pytest.mark.asyncio
    async def test_evaluate_returns_quality_report(self) -> None:
        """Test that a concrete evaluate() returns the right type."""

        class MockEvaluator(QualityEvaluationPort):
            async def evaluate(self, request: EvaluationRequest) -> QualityReport:
                metric = MetricResult(
                    name="quality_score",
                    value=0.9,
                    status=MetricStatus.PASS,
                    threshold=0.8,
                )
                return QualityReport(
                    evaluation_id="eval-test",
                    metrics=[metric],
                    overall_score=0.9,
                    passed=True,
                    summary=f"Evaluated: {request.input_data[:20]}",
                )

            async def evaluate_batch(
                self, requests: list[EvaluationRequest]
            ) -> list[QualityReport]:
                return []

        evaluator = MockEvaluator()
        req = EvaluationRequest(
            eval_type=EvaluationType.QUALITY,
            input_data="Test output to evaluate",
        )
        result = await evaluator.evaluate(req)
        assert isinstance(result, QualityReport)
        assert result.passed is True
        assert len(result.metrics) == 1

    @pytest.mark.asyncio
    async def test_evaluate_batch_returns_list(self) -> None:
        """Test that evaluate_batch returns a list of reports."""

        class MockEvaluator(QualityEvaluationPort):
            async def evaluate(self, request: EvaluationRequest) -> QualityReport:
                return QualityReport(
                    evaluation_id="single",
                    metrics=[],
                    overall_score=1.0,
                    passed=True,
                    summary="OK",
                )

            async def evaluate_batch(
                self, requests: list[EvaluationRequest]
            ) -> list[QualityReport]:
                return [
                    QualityReport(
                        evaluation_id=f"batch-{i}",
                        metrics=[],
                        overall_score=0.95,
                        passed=True,
                        summary=f"Batch item {i}",
                    )
                    for i in range(len(requests))
                ]

        evaluator = MockEvaluator()
        requests = [
            EvaluationRequest(eval_type=EvaluationType.ACCURACY, input_data="input1"),
            EvaluationRequest(eval_type=EvaluationType.SAFETY, input_data="input2"),
        ]
        results = await evaluator.evaluate_batch(requests)
        assert len(results) == 2
        assert all(isinstance(r, QualityReport) for r in results)


class TestMetricCollectorPort:
    """Tests for the MetricCollectorPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify MetricCollectorPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MetricCollectorPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = MetricCollectorPort.__abstractmethods__
        assert "collect" in abstract_methods
        assert "get_metrics" in abstract_methods

    @pytest.mark.asyncio
    async def test_concrete_collect(self) -> None:
        """Test that a concrete collect() works without error."""

        class MockCollector(MetricCollectorPort):
            def __init__(self) -> None:
                self.stored: list[tuple[str, float, dict | None]] = []

            async def collect(
                self, metric_name: str, value: float, tags: dict | None = None
            ) -> None:
                self.stored.append((metric_name, value, tags))

            async def get_metrics(
                self, metric_name: str, time_range: tuple | None = None
            ) -> list[MetricResult]:
                return [
                    MetricResult(name=metric_name, value=v, status=MetricStatus.PASS)
                    for n, v, _ in self.stored
                    if n == metric_name
                ]

        collector = MockCollector()
        await collector.collect("accuracy", 0.95, tags={"model": "gpt-4o"})
        await collector.collect("accuracy", 0.92)
        results = await collector.get_metrics("accuracy")
        assert len(results) == 2
        assert all(isinstance(r, MetricResult) for r in results)

    @pytest.mark.asyncio
    async def test_get_metrics_with_time_range(self) -> None:
        """Test that get_metrics accepts an optional time_range parameter."""

        class MockCollector(MetricCollectorPort):
            async def collect(
                self, metric_name: str, value: float, tags: dict | None = None
            ) -> None:
                pass

            async def get_metrics(
                self, metric_name: str, time_range: tuple | None = None
            ) -> list[MetricResult]:
                return []

        collector = MockCollector()
        results = await collector.get_metrics("latency", time_range=(0, 100))
        assert results == []


class TestRegressionTestPort:
    """Tests for the RegressionTestPort abstract base class."""

    def test_port_is_abstract(self) -> None:
        """Verify RegressionTestPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            RegressionTestPort()  # type: ignore[abstract]

    def test_has_required_abstract_methods(self) -> None:
        """Verify all required abstract methods are defined."""
        abstract_methods = RegressionTestPort.__abstractmethods__
        assert "run_suite" in abstract_methods
        assert "compare" in abstract_methods

    @pytest.mark.asyncio
    async def test_concrete_run_suite(self) -> None:
        """Test that a concrete run_suite() returns a QualityReport."""

        class MockRegressionRunner(RegressionTestPort):
            async def run_suite(self, suite_id: str) -> QualityReport:
                return QualityReport(
                    evaluation_id=f"regression-{suite_id}",
                    metrics=[
                        MetricResult(
                            name="test_pass_rate",
                            value=1.0,
                            status=MetricStatus.PASS,
                            threshold=0.95,
                        ),
                    ],
                    overall_score=1.0,
                    passed=True,
                    summary=f"Suite {suite_id} passed all tests.",
                )

            async def compare(self, baseline_id: str, current_id: str) -> QualityReport:
                return QualityReport(
                    evaluation_id="compare-result",
                    metrics=[],
                    overall_score=1.0,
                    passed=True,
                    summary="No regressions detected.",
                )

        runner = MockRegressionRunner()
        report = await runner.run_suite("core-tests")
        assert isinstance(report, QualityReport)
        assert report.passed is True
        assert "core-tests" in report.evaluation_id

    @pytest.mark.asyncio
    async def test_concrete_compare(self) -> None:
        """Test that a concrete compare() returns a QualityReport with comparison details."""

        class MockRegressionRunner(RegressionTestPort):
            async def run_suite(self, suite_id: str) -> QualityReport:
                return QualityReport(
                    evaluation_id="suite-run",
                    metrics=[],
                    overall_score=1.0,
                    passed=True,
                    summary="OK",
                )

            async def compare(self, baseline_id: str, current_id: str) -> QualityReport:
                regression_metric = MetricResult(
                    name="accuracy_delta",
                    value=-0.02,
                    status=MetricStatus.WARNING,
                    details=f"Comparing {baseline_id} vs {current_id}",
                )
                return QualityReport(
                    evaluation_id="compare-result",
                    metrics=[regression_metric],
                    overall_score=0.85,
                    passed=True,
                    summary="Minor regression detected but within tolerance.",
                )

        runner = MockRegressionRunner()
        report = await runner.compare("baseline-v1", "current-v2")
        assert isinstance(report, QualityReport)
        assert len(report.metrics) == 1
        assert report.metrics[0].name == "accuracy_delta"
