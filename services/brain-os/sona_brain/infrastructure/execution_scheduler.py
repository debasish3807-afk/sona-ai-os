"""Execution scheduler for Brain OS.

Main orchestrator that analyzes a plan's dependency graph, groups steps
into waves (each wave = set of independent steps), and executes waves
sequentially with steps within a wave running in parallel.
"""

from typing import Any

import structlog

from sona_brain.domain.execution import StepResult, StepState
from sona_brain.infrastructure.parallel_executor import ParallelExecutor
from sona_brain.infrastructure.sequential_executor import SequentialExecutor
from sona_brain.infrastructure.state_manager import ExecutionStateManager
from sona_thalamus.domain.execution_plan import ExecutionPlan, ExecutionStep

logger = structlog.get_logger()


class ExecutionScheduler:
    """Schedules plan execution using wave-based parallelism.

    Analyzes the dependency graph to group steps into waves. Steps
    within a wave have no mutual dependencies and execute in parallel.
    Waves execute sequentially.
    """

    def __init__(
        self,
        sequential_executor: SequentialExecutor,
        parallel_executor: ParallelExecutor,
    ) -> None:
        """Initialize scheduler with executors.

        Args:
            sequential_executor: For executing single-step waves.
            parallel_executor: For executing multi-step waves.
        """
        self._sequential_executor = sequential_executor
        self._parallel_executor = parallel_executor

    async def execute_plan(
        self,
        plan: ExecutionPlan,
        state_manager: ExecutionStateManager,
    ) -> list[StepResult]:
        """Execute an entire plan using wave-based scheduling.

        Groups steps into dependency waves and executes them in order.
        Steps within a wave run in parallel. Stops if a wave fails
        with non-retryable errors.

        Args:
            plan: The execution plan to schedule.
            state_manager: State manager tracking execution.

        Returns:
            All StepResults from the execution.
        """
        waves = self._compute_waves(plan.steps)
        all_results: list[StepResult] = []
        completed_outputs: dict[str, Any] = {}

        logger.info(
            "scheduling_plan",
            plan_id=plan.plan_id,
            total_steps=len(plan.steps),
            wave_count=len(waves),
        )

        for wave_index, wave in enumerate(waves):
            logger.debug(
                "executing_wave",
                wave_index=wave_index,
                step_count=len(wave),
                steps=[s.step_id for s in wave],
            )

            if len(wave) == 1:
                # Single step: use sequential executor
                results = await self._sequential_executor.execute(wave, state_manager)
            else:
                # Multiple steps: use parallel executor
                results = await self._parallel_executor.execute(
                    wave, state_manager, shared_context=completed_outputs
                )

            all_results.extend(results)

            # Collect outputs from completed steps
            for result in results:
                if result.state == StepState.COMPLETED:
                    completed_outputs[result.step_id] = result.output

            # Check for failures that should stop execution
            failed = [r for r in results if r.state == StepState.FAILED]
            if failed:
                logger.warning(
                    "wave_has_failures",
                    wave_index=wave_index,
                    failed_steps=[f.step_id for f in failed],
                )
                # Cancel remaining waves
                remaining_steps = [
                    s for w in waves[wave_index + 1:] for s in w
                ]
                for step in remaining_steps:
                    await state_manager.mark_step_cancelled(step.step_id)
                break

        return all_results

    def _compute_waves(self, steps: list[ExecutionStep]) -> list[list[ExecutionStep]]:
        """Group steps into dependency waves via topological level sorting.

        Steps with no unresolved dependencies form the first wave.
        Steps depending only on first-wave steps form the second wave, etc.

        Args:
            steps: All steps from the execution plan.

        Returns:
            List of waves, where each wave is a list of independent steps.
        """
        if not steps:
            return []

        step_map = {s.step_id: s for s in steps}
        in_degree: dict[str, int] = {}
        dependents: dict[str, list[str]] = {}

        # Initialize
        for step in steps:
            in_degree[step.step_id] = 0
            dependents[step.step_id] = []

        # Compute in-degrees (only count deps within this plan)
        for step in steps:
            for dep_id in step.depends_on:
                if dep_id in step_map:
                    in_degree[step.step_id] += 1
                    dependents[dep_id].append(step.step_id)

        # BFS by levels
        waves: list[list[ExecutionStep]] = []
        current_wave = [
            step_map[sid] for sid, deg in in_degree.items() if deg == 0
        ]

        while current_wave:
            # Sort by priority for deterministic ordering
            current_wave.sort(key=lambda s: (s.priority, s.step_id))
            waves.append(current_wave)

            next_wave_ids: list[str] = []
            for step in current_wave:
                for dep_id in dependents[step.step_id]:
                    in_degree[dep_id] -= 1
                    if in_degree[dep_id] == 0:
                        next_wave_ids.append(dep_id)

            current_wave = [step_map[sid] for sid in next_wave_ids]

        return waves

    def get_wave_count(self, steps: list[ExecutionStep]) -> int:
        """Return the number of waves for a set of steps.

        Args:
            steps: Steps to analyze.

        Returns:
            Number of dependency waves.
        """
        return len(self._compute_waves(steps))
