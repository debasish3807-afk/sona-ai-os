"""Task Planner — builds execution plans from user intents.

Takes an analyzed intent and constructs a multi-step execution
plan with tool selection, parameter resolution, and dependencies.
"""

from __future__ import annotations

import re
from typing import Any

from config.logging import get_logger
from planner.intent import IntentAnalyzer, IntentResult, TaskIntent
from planner.plan import ExecutionPlan

logger = get_logger(__name__)


class TaskPlanner:
    """Builds execution plans from user messages.

    Uses intent analysis to determine required tools, then
    constructs ordered execution plans with dependencies.
    """

    def __init__(self) -> None:
        self._analyzer = IntentAnalyzer()

    def analyze_intent(self, message: str) -> IntentResult:
        """Analyze user intent from message text."""
        return self._analyzer.analyze(message)

    def create_plan(self, message: str, intent: IntentResult | None = None) -> ExecutionPlan:
        """Create an execution plan for a user message.

        Args:
            message: The user's request.
            intent: Pre-analyzed intent (optional).

        Returns:
            ExecutionPlan with ordered steps.
        """
        if intent is None:
            intent = self.analyze_intent(message)

        if not intent.requires_tools:
            return ExecutionPlan(description="Chat response (no tools needed)")

        plan = self._build_plan(message, intent)
        logger.info(
            "Plan created",
            intent=intent.intent.value,
            steps=plan.step_count,
            plan_id=plan.plan_id,
        )
        return plan

    def _build_plan(self, message: str, intent: IntentResult) -> ExecutionPlan:
        """Build plan based on detected intent."""
        builders: dict[TaskIntent, Any] = {
            TaskIntent.FILE_OPERATION: self._plan_file_operation,
            TaskIntent.CODE_EXECUTION: self._plan_code_execution,
            TaskIntent.GIT_OPERATION: self._plan_git_operation,
            TaskIntent.GITHUB_OPERATION: self._plan_github_operation,
            TaskIntent.WEB_RESEARCH: self._plan_web_research,
            TaskIntent.DATABASE_OPERATION: self._plan_database_operation,
            TaskIntent.PROJECT_ANALYSIS: self._plan_project_analysis,
            TaskIntent.MULTI_STEP: self._plan_multi_step,
        }
        builder = builders.get(intent.intent, self._plan_generic)
        return builder(message, intent)  # type: ignore[no-any-return]

    def _plan_file_operation(self, message: str, intent: IntentResult) -> ExecutionPlan:
        plan = ExecutionPlan(description=f"File operation: {message[:80]}")
        path = intent.extracted_params.get("path", ".")
        msg_lower = message.lower()

        if any(w in msg_lower for w in ("read", "show", "display", "cat", "view")):
            plan.add_step("file_read", f"Read file: {path}", {"path": path})
        elif any(w in msg_lower for w in ("write", "create", "save")):
            plan.add_step("file_write", f"Write file: {path}", {"path": path, "content": ""})
        elif any(w in msg_lower for w in ("edit", "update", "change", "replace")):
            plan.add_step("file_read", f"Read current content of {path}", {"path": path})
            plan.add_step(
                "file_edit", f"Edit file: {path}", {"path": path, "old_text": "", "new_text": ""}
            )
        elif any(w in msg_lower for w in ("list", "ls", "find", "search")):
            plan.add_step("list_dir", "List directory contents", {"path": path, "recursive": True})
        elif any(w in msg_lower for w in ("delete", "remove")):
            plan.add_step("file_delete", f"Delete: {path}", {"path": path})
        else:
            plan.add_step("file_read", f"Read: {path}", {"path": path})
        return plan

    def _plan_code_execution(self, message: str, intent: IntentResult) -> ExecutionPlan:
        plan = ExecutionPlan(description=f"Code execution: {message[:80]}")
        msg_lower = message.lower()
        if "python" in msg_lower or "py" in msg_lower:
            plan.add_step("python_exec", "Execute Python code", {"code": "", "timeout": 30})
        elif any(w in msg_lower for w in ("test", "pytest")):
            plan.add_step(
                "terminal_exec", "Run tests", {"command": "pytest tests/ -v", "timeout": 60}
            )
        elif any(w in msg_lower for w in ("lint", "ruff")):
            plan.add_step("terminal_exec", "Run linter", {"command": "ruff check .", "timeout": 30})
        else:
            plan.add_step("terminal_exec", "Execute command", {"command": "", "timeout": 30})
        return plan

    def _plan_git_operation(self, message: str, intent: IntentResult) -> ExecutionPlan:
        plan = ExecutionPlan(description=f"Git operation: {message[:80]}")
        msg_lower = message.lower()

        if "commit" in msg_lower:
            s1 = plan.add_step("git_status", "Check working tree status")
            s2 = plan.add_step("git_add", "Stage changes", {"files": "."}, [s1.step_id])
            commit_msg = self._extract_commit_message(message) or "Update"
            plan.add_step("git_commit", "Create commit", {"message": commit_msg}, [s2.step_id])
        elif "push" in msg_lower:
            s1 = plan.add_step("git_status", "Check status before push")
            plan.add_step("git_push", "Push to remote", {}, [s1.step_id])
        elif "pull" in msg_lower:
            plan.add_step("git_pull", "Pull latest changes")
        elif "status" in msg_lower:
            plan.add_step("git_status", "Show git status")
        elif "diff" in msg_lower:
            plan.add_step("git_diff", "Show changes")
        elif "log" in msg_lower:
            plan.add_step("git_log", "Show recent commits", {"count": 10})
        elif "branch" in msg_lower or "checkout" in msg_lower:
            branch = intent.extracted_params.get("branch", "")
            if branch:
                plan.add_step("git_checkout", f"Switch to {branch}", {"target": branch})
            else:
                plan.add_step("git_branch", "List branches")
        else:
            plan.add_step("git_status", "Show git status")
        return plan

    def _plan_github_operation(self, message: str, intent: IntentResult) -> ExecutionPlan:
        plan = ExecutionPlan(description=f"GitHub operation: {message[:80]}")
        msg_lower = message.lower()
        if "pr" in msg_lower or "pull request" in msg_lower:
            plan.add_step("github_pull_requests", "List pull requests", {"owner": "", "repo": ""})
        elif "issue" in msg_lower:
            plan.add_step("github_issues", "List issues", {"owner": "", "repo": ""})
        elif "commit" in msg_lower:
            plan.add_step("github_commits", "List commits", {"owner": "", "repo": ""})
        else:
            plan.add_step("github_repo_info", "Get repository info", {"owner": "", "repo": ""})
        return plan

    def _plan_web_research(self, message: str, intent: IntentResult) -> ExecutionPlan:
        plan = ExecutionPlan(description=f"Web research: {message[:80]}")
        url = intent.extracted_params.get("url")
        if url:
            plan.add_step("browser_fetch", f"Fetch URL: {url}", {"url": url, "format": "markdown"})
        else:
            query = message.replace("search ", "").replace("look up ", "").strip()[:100]
            plan.add_step("browser_search", f"Search: {query}", {"query": query})
        return plan

    def _plan_database_operation(self, message: str, intent: IntentResult) -> ExecutionPlan:
        plan = ExecutionPlan(description=f"Database operation: {message[:80]}")
        msg_lower = message.lower()
        if "schema" in msg_lower or "table" in msg_lower:
            plan.add_step("db_schema", "Show database schema", {"database": ""})
        else:
            plan.add_step("db_query", "Execute SQL query", {"database": "", "query": ""})
        return plan

    def _plan_project_analysis(self, message: str, intent: IntentResult) -> ExecutionPlan:
        plan = ExecutionPlan(description=f"Project analysis: {message[:80]}")
        s1 = plan.add_step(
            "list_dir", "List project structure", {"path": ".", "recursive": True, "max_depth": 3}
        )
        s2 = plan.add_step(
            "file_search", "Find Python files", {"pattern": "*.py", "max_results": 50}, [s1.step_id]
        )
        plan.add_step(
            "terminal_exec",
            "Count lines of code",
            {
                "command": "find . -name '*.py' -not -path './__pycache__/*' | xargs wc -l 2>/dev/null | tail -1"
            },
            [s2.step_id],
        )
        return plan

    def _plan_multi_step(self, message: str, intent: IntentResult) -> ExecutionPlan:
        plan = ExecutionPlan(description=f"Multi-step task: {message[:80]}")
        for tool in intent.suggested_tools[:5]:
            plan.add_step(tool, f"Execute {tool}", {})
        return plan

    def _plan_generic(self, message: str, intent: IntentResult) -> ExecutionPlan:
        plan = ExecutionPlan(description=f"Task: {message[:80]}")
        if intent.suggested_tools:
            plan.add_step(intent.suggested_tools[0], message[:100], intent.extracted_params)
        return plan

    def _extract_commit_message(self, message: str) -> str:
        patterns = [
            re.compile(r'["\']([^"\']+)["\']'),
            re.compile(r"message[:\s]+(.+?)(?:\.|$)", re.I),
            re.compile(r"commit\s+(.+?)(?:\.|$)", re.I),
        ]
        for p in patterns:
            m = p.search(message)
            if m:
                return m.group(1).strip()[:72]
        return ""
