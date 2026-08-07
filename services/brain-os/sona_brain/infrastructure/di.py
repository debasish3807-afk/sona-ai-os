"""Dependency injection factory for Brain OS.

Provides factory functions to create fully-configured Brain OS runtime
instances with all dependencies wired up.
"""

import structlog

from sona_brain.infrastructure.brain_runtime import BrainRuntime
from sona_brain.infrastructure.dynamic_replanner import DynamicReplanner
from sona_brain.infrastructure.execution_scheduler import ExecutionScheduler
from sona_brain.infrastructure.failure_recovery import FailureRecovery
from sona_brain.infrastructure.metrics import ExecutionMetrics
from sona_brain.infrastructure.parallel_executor import ParallelExecutor
from sona_brain.infrastructure.reflection_engine import ReflectionConfig, ReflectionEngine
from sona_brain.infrastructure.result_aggregator import ResultAggregator
from sona_brain.infrastructure.retry_manager import RetryConfig, RetryManager
from sona_brain.infrastructure.sequential_executor import SequentialExecutor
from sona_brain.infrastructure.step_executor import StepExecutor
from sona_brain.infrastructure.timeout_recovery import TimeoutRecovery

logger = structlog.get_logger()


def create_brain_runtime(
    default_model: str = "llama3.2",
    default_provider: str = "ollama",
    max_concurrency: int = 10,
    max_retries: int = 3,
    max_reflection_rounds: int = 2,
) -> BrainRuntime:
    """Create a fully-configured BrainRuntime instance.

    Wires up all infrastructure dependencies and returns a ready-to-use
    brain runtime implementation.

    Args:
        default_model: Default model identifier for LLM calls.
        default_provider: Default provider for LLM calls.
        max_concurrency: Maximum parallel step concurrency.
        max_retries: Maximum retry attempts per step.
        max_reflection_rounds: Maximum reflection iterations.

    Returns:
        A configured BrainRuntime instance.
    """
    # Core executors
    step_executor = StepExecutor(model_id=default_model, provider=default_provider)
    retry_manager = RetryManager(
        config=RetryConfig(max_retries=max_retries, base_delay_seconds=0.1)
    )

    sequential_executor = SequentialExecutor(
        step_executor=step_executor,
        retry_manager=retry_manager,
    )
    parallel_executor = ParallelExecutor(
        step_executor=step_executor,
        retry_manager=retry_manager,
        max_concurrency=max_concurrency,
    )

    # Scheduler
    scheduler = ExecutionScheduler(
        sequential_executor=sequential_executor,
        parallel_executor=parallel_executor,
    )

    # Support systems
    reflection_engine = ReflectionEngine(
        config=ReflectionConfig(max_reflection_rounds=max_reflection_rounds)
    )
    replanner = DynamicReplanner()
    result_aggregator = ResultAggregator()
    failure_recovery = FailureRecovery()
    timeout_recovery = TimeoutRecovery()
    metrics = ExecutionMetrics()

    runtime = BrainRuntime(
        scheduler=scheduler,
        reflection_engine=reflection_engine,
        replanner=replanner,
        result_aggregator=result_aggregator,
        failure_recovery=failure_recovery,
        timeout_recovery=timeout_recovery,
        metrics=metrics,
        default_model=default_model,
        default_provider=default_provider,
    )

    logger.info(
        "brain_runtime_created",
        model=default_model,
        provider=default_provider,
        max_concurrency=max_concurrency,
        max_retries=max_retries,
    )

    return runtime
