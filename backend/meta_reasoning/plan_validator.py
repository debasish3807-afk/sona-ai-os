"""Meta Reasoning & Self Reflection Engine — plan validation."""

from __future__ import annotations

from config.logging import get_logger

logger = get_logger(__name__)


class PlanValidator:
    """Validates execution plans against constraints and policies."""

    def validate(self, plan: dict, context: dict) -> tuple[bool, list[str]]:
        """Validate a plan against the given context.

        Args:
            plan: The execution plan to validate.
            context: Environment context including budget, capabilities, etc.

        Returns:
            Tuple of (is_valid, list_of_issues).
        """
        issues: list[str] = []
        issues.extend(self._check_dependencies(plan))
        issues.extend(self._check_capabilities(plan))
        issues.extend(self._check_permissions(plan))
        issues.extend(self._check_budget(plan, context))
        issues.extend(self._check_risk_threshold(plan, context))
        issues.extend(self._check_policies(plan))
        valid = len(issues) == 0
        logger.info("plan_validation_complete", valid=valid, issue_count=len(issues))
        return valid, issues

    def _check_dependencies(self, plan: dict) -> list[str]:
        """Check that all task dependencies are satisfiable."""
        issues: list[str] = []
        tasks = plan.get("tasks", [])
        dependencies = plan.get("dependencies", {})
        for dep_target, dep_sources in dependencies.items():
            if dep_target not in tasks:
                issues.append(f"Dependency target '{dep_target}' not found in tasks")
            for src in dep_sources:
                if src not in tasks:
                    issues.append(f"Dependency source '{src}' not found in tasks")
        return issues

    def _check_capabilities(self, plan: dict) -> list[str]:
        """Check that required capabilities are available."""
        issues: list[str] = []
        required = plan.get("capabilities", [])
        if not required:
            issues.append("Plan declares no required capabilities")
        return issues

    def _check_permissions(self, plan: dict) -> list[str]:
        """Check that required permissions are granted."""
        issues: list[str] = []
        permissions = plan.get("permissions", [])
        restricted = {"admin_write", "system_override", "delete_all"}
        for perm in permissions:
            if perm in restricted:
                issues.append(f"Restricted permission required: '{perm}'")
        return issues

    def _check_budget(self, plan: dict, context: dict) -> list[str]:
        """Check that plan cost fits within budget."""
        issues: list[str] = []
        budget = context.get("budget", float("inf"))
        cost_info = plan.get("cost", {})
        estimated_cost = cost_info.get("total_estimated", 0.0)
        if estimated_cost > budget:
            issues.append(
                f"Estimated cost ({estimated_cost:.4f}) exceeds budget ({budget:.4f})"
            )
        return issues

    def _check_risk_threshold(self, plan: dict, context: dict) -> list[str]:
        """Check that plan risk is within acceptable threshold."""
        issues: list[str] = []
        max_risk = context.get("max_risk", 1.0)
        risk_info = plan.get("risk", {})
        overall_risk = risk_info.get("overall_risk", 0.0)
        if overall_risk > max_risk:
            issues.append(
                f"Plan risk ({overall_risk:.2f}) exceeds threshold ({max_risk:.2f})"
            )
        return issues

    def _check_policies(self, plan: dict) -> list[str]:
        """Check plan against system policies."""
        issues: list[str] = []
        execution_mode = plan.get("execution_mode", "sequential")
        valid_modes = {"sequential", "parallel", "hybrid", "adaptive"}
        if execution_mode not in valid_modes:
            issues.append(f"Invalid execution mode: '{execution_mode}'")
        tasks = plan.get("tasks", [])
        if not tasks:
            issues.append("Plan has no tasks defined")
        return issues
