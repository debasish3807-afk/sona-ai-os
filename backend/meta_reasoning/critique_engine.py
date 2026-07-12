"""Meta Reasoning & Self Reflection Engine — critique generation."""

from __future__ import annotations

from config.logging import get_logger

logger = get_logger(__name__)


class CritiqueEngine:
    """Generates critiques of execution plans by detecting weaknesses."""

    def critique(self, plan: dict, reflection: dict) -> list[str]:
        """Generate a list of critique points for a plan.

        Args:
            plan: The execution plan to critique.
            reflection: The reflection report to reference.

        Returns:
            List of critique strings identifying weaknesses.
        """
        critiques: list[str] = []
        critiques.extend(self._detect_logic_gaps(plan))
        critiques.extend(self._detect_weak_assumptions(plan))
        critiques.extend(self._detect_missing_evidence(plan))
        critiques.extend(self._detect_contradictions(plan))
        critiques.extend(self._detect_duplicate_work(plan))
        critiques.extend(self._detect_missing_dependencies(plan))
        critiques.extend(self._detect_risky_decisions(plan, reflection))
        logger.info("critique_generated", count=len(critiques))
        return critiques

    def _detect_logic_gaps(self, plan: dict) -> list[str]:
        """Detect logical gaps in the plan."""
        gaps: list[str] = []
        tasks = plan.get("tasks", [])
        if not tasks:
            gaps.append("No tasks defined — plan has no actionable steps")
        execution_mode = plan.get("execution_mode", "")
        if execution_mode == "parallel" and len(tasks) < 2:
            gaps.append("Parallel mode with fewer than 2 tasks is unnecessary")
        return gaps

    def _detect_weak_assumptions(self, plan: dict) -> list[str]:
        """Detect assumptions that lack strong backing."""
        assumptions: list[str] = []
        cost_info = plan.get("cost", {})
        if cost_info.get("total_estimated", 0) == 0:
            assumptions.append("Zero cost estimate may be an unverified assumption")
        duration = plan.get("estimated_duration_ms", 0)
        if duration == 0:
            assumptions.append("Zero duration estimate is likely unrealistic")
        return assumptions

    def _detect_missing_evidence(self, plan: dict) -> list[str]:
        """Detect claims without supporting evidence."""
        missing: list[str] = []
        risk_info = plan.get("risk", {})
        if not risk_info:
            missing.append("No risk assessment provided — risk is unquantified")
        if not plan.get("capabilities"):
            missing.append("No capabilities declared — execution requirements unclear")
        return missing

    def _detect_contradictions(self, plan: dict) -> list[str]:
        """Detect contradictory elements in the plan."""
        contradictions: list[str] = []
        risk_info = plan.get("risk", {})
        overall_risk = risk_info.get("overall_risk", 0.0)
        if overall_risk > 0.8 and plan.get("execution_mode") == "parallel":
            contradictions.append(
                "High-risk plan uses parallel execution, increasing failure blast radius"
            )
        return contradictions

    def _detect_duplicate_work(self, plan: dict) -> list[str]:
        """Detect potential duplicate or redundant tasks."""
        duplicates: list[str] = []
        tasks = plan.get("tasks", [])
        seen = set()
        for task in tasks:
            if task in seen:
                duplicates.append(f"Duplicate task detected: '{task}'")
            seen.add(task)
        return duplicates

    def _detect_missing_dependencies(self, plan: dict) -> list[str]:
        """Detect tasks that likely need dependencies but have none."""
        missing: list[str] = []
        tasks = plan.get("tasks", [])
        dependencies = plan.get("dependencies", {})
        if len(tasks) > 3 and not dependencies:
            missing.append(
                "Complex plan with no declared dependencies — ordering may be incorrect"
            )
        return missing

    def _detect_risky_decisions(self, plan: dict, reflection: dict) -> list[str]:
        """Detect decisions that carry elevated risk."""
        risky: list[str] = []
        overall = reflection.get("overall", 0.0)
        if overall < 0.5:
            risky.append(
                f"Reflection overall score is low ({overall:.2f}) — plan quality questionable"
            )
        risk_info = plan.get("risk", {})
        if risk_info.get("overall_risk", 0.0) > 0.7:
            risky.append("Overall risk exceeds 0.7 — consider risk mitigation")
        return risky

    def get_severity(self, critiques: list[str]) -> str:
        """Determine overall severity of critiques.

        Args:
            critiques: List of critique strings.

        Returns:
            Severity level: low, medium, high, or critical.
        """
        count = len(critiques)
        if count == 0:
            return "low"
        if count <= 2:
            return "medium"
        if count <= 5:
            return "high"
        return "critical"
