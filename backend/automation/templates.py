"""Automation templates — reusable workflow stencils."""

from __future__ import annotations

from automation.schemas import ActionStep, ActionType, AutomationTemplate


class AutomationTemplates:
    """Built-in and custom automation workflow templates."""

    def __init__(self) -> None:
        self._templates: dict[str, AutomationTemplate] = {}
        self._load_builtins()

    def _load_builtins(self) -> None:
        builtins = [
            AutomationTemplate(
                template_id="daily-report",
                name="Daily Report",
                description="Gather research and generate a daily report",
                category="reporting",
                tags=["daily", "research"],
                steps=[
                    ActionStep(action_type=ActionType.DEEP_RESEARCH, params={"query": "{{topic}}"}),
                    ActionStep(
                        action_type=ActionType.AI_CHAT,
                        params={"message": "Summarize the research findings"},
                    ),
                    ActionStep(
                        action_type=ActionType.FILE_WRITE,
                        params={"path": "{{output_path}}/report.md"},
                    ),
                ],
                variables={"topic": "Research topic", "output_path": "Output directory"},
            ),
            AutomationTemplate(
                template_id="code-review",
                name="Code Review Pipeline",
                description="Analyze and review source code",
                category="development",
                tags=["code", "review"],
                steps=[
                    ActionStep(
                        action_type=ActionType.TERMINAL,
                        params={"command": "ruff check {{file_path}}"},
                    ),
                    ActionStep(
                        action_type=ActionType.TERMINAL, params={"command": "mypy {{file_path}}"}
                    ),
                ],
                variables={"file_path": "Path to source file"},
            ),
            AutomationTemplate(
                template_id="backup-files",
                name="Backup Files",
                description="Copy important files to a backup location",
                category="system",
                tags=["backup", "files"],
                steps=[
                    ActionStep(
                        action_type=ActionType.FILE_READ, params={"path": "{{source_path}}"}
                    ),
                    ActionStep(
                        action_type=ActionType.FILE_WRITE,
                        params={"path": "{{dest_path}}/backup.md"},
                    ),
                ],
                variables={"source_path": "Source file path", "dest_path": "Destination directory"},
            ),
            AutomationTemplate(
                template_id="http-monitor",
                name="HTTP Endpoint Monitor",
                description="Check an HTTP endpoint and store results",
                category="monitoring",
                tags=["http", "monitoring"],
                steps=[
                    ActionStep(
                        action_type=ActionType.HTTP_REQUEST,
                        params={"url": "{{url}}", "method": "GET"},
                    ),
                    ActionStep(
                        action_type=ActionType.MEMORY_STORE,
                        params={"content": "Endpoint {{url}} checked"},
                    ),
                ],
                variables={"url": "URL to monitor"},
            ),
        ]
        for t in builtins:
            self._templates[t.template_id] = t

    def get_template(self, template_id: str) -> AutomationTemplate | None:
        return self._templates.get(template_id)

    def list_templates(self, category: str | None = None) -> list[AutomationTemplate]:
        if category:
            return [t for t in self._templates.values() if t.category == category]
        return list(self._templates.values())

    def add_template(self, template: AutomationTemplate) -> str:
        import uuid

        if not template.template_id:
            template.template_id = str(uuid.uuid4())
        self._templates[template.template_id] = template
        return template.template_id

    def delete_template(self, template_id: str) -> bool:
        return self._templates.pop(template_id, None) is not None
