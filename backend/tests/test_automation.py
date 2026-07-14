"""Tests for Automation Engine (Phase 20.5)."""

from __future__ import annotations

import pytest

from automation.engine import AutomationEngine
from automation.executor import WorkflowExecutor
from automation.schemas import (
    ActionStep,
    ActionType,
    Condition,
    StepType,
    TriggerType,
    Workflow,
    WorkflowStatus,
    WorkflowStep,
)


class TestSchemas:
    def test_trigger_types(self):
        assert TriggerType.TIME.value == "time"
        assert TriggerType.MANUAL.value == "manual"
        assert TriggerType.FILE_CHANGE.value == "file_change"

    def test_action_types(self):
        assert ActionType.AI_CHAT.value == "ai_chat"
        assert ActionType.TERMINAL.value == "terminal"
        assert ActionType.NOTIFICATION.value == "notification"

    def test_workflow_status(self):
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"

    def test_action_step(self):
        step = ActionStep(action_type=ActionType.AI_CHAT, params={"message": "hi"})
        assert step.retry == 0
        assert step.timeout_seconds == 30.0

    def test_workflow(self):
        wf = Workflow(workflow_id="w1", name="Test")
        assert wf.enabled is True
        assert wf.steps == []


class TestAutomationEngine:
    def test_create_workflow(self):
        engine = AutomationEngine()
        steps = [
            WorkflowStep(
                step_type=StepType.ACTION, action=ActionStep(action_type=ActionType.NOTIFICATION)
            )
        ]
        wf = engine.create_workflow("Test WF", steps)
        assert wf.workflow_id != ""
        assert wf.name == "Test WF"
        assert len(wf.steps) == 1

    def test_list_workflows(self):
        engine = AutomationEngine()
        engine.create_workflow("WF1", [])
        engine.create_workflow("WF2", [])
        assert len(engine.list_workflows()) == 2

    def test_get_workflow(self):
        engine = AutomationEngine()
        wf = engine.create_workflow("Get Me", [])
        found = engine.get_workflow(wf.workflow_id)
        assert found is not None
        assert found.name == "Get Me"

    def test_get_workflow_missing(self):
        engine = AutomationEngine()
        assert engine.get_workflow("fake") is None

    def test_delete_workflow(self):
        engine = AutomationEngine()
        wf = engine.create_workflow("Delete Me", [])
        assert engine.delete_workflow(wf.workflow_id) is True
        assert engine.get_workflow(wf.workflow_id) is None

    def test_delete_nonexistent(self):
        engine = AutomationEngine()
        assert engine.delete_workflow("fake") is False

    @pytest.mark.asyncio
    async def test_run_workflow_simple(self):
        engine = AutomationEngine()
        steps = [
            WorkflowStep(
                step_type=StepType.ACTION,
                action=ActionStep(action_type=ActionType.NOTIFICATION, params={"message": "test"}),
            )
        ]
        wf = engine.create_workflow("Run Me", steps)
        run = await engine.run_workflow(wf.workflow_id)
        assert run.status == WorkflowStatus.COMPLETED
        assert run.steps_completed == 1

    @pytest.mark.asyncio
    async def test_run_workflow_not_found(self):
        engine = AutomationEngine()
        run = await engine.run_workflow("nonexistent")
        assert run.status == WorkflowStatus.FAILED
        assert "not found" in run.error.lower()

    def test_get_templates(self):
        engine = AutomationEngine()
        templates = engine.get_templates()
        assert len(templates) >= 3
        assert templates[0]["id"] == "daily_research"

    def test_get_status(self):
        engine = AutomationEngine()
        status = engine.get_status()
        assert "workflows" in status
        assert "runs_total" in status

    def test_get_history_empty(self):
        engine = AutomationEngine()
        assert engine.get_history() == []

    @pytest.mark.asyncio
    async def test_history_after_run(self):
        engine = AutomationEngine()
        wf = engine.create_workflow(
            "History",
            [
                WorkflowStep(
                    step_type=StepType.ACTION,
                    action=ActionStep(action_type=ActionType.NOTIFICATION),
                )
            ],
        )
        await engine.run_workflow(wf.workflow_id)
        assert len(engine.get_history()) == 1


class TestExecutor:
    @pytest.mark.asyncio
    async def test_wait_step(self):
        executor = WorkflowExecutor()
        wf = Workflow(
            workflow_id="w1",
            name="Wait",
            steps=[WorkflowStep(step_type=StepType.WAIT, wait_seconds=0.01)],
        )
        run = await executor.run(wf)
        assert run.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_parallel_steps(self):
        executor = WorkflowExecutor()
        wf = Workflow(
            workflow_id="w2",
            name="Parallel",
            steps=[
                WorkflowStep(
                    step_type=StepType.PARALLEL,
                    steps=[
                        WorkflowStep(
                            step_type=StepType.ACTION,
                            action=ActionStep(
                                action_type=ActionType.NOTIFICATION, params={"message": "a"}
                            ),
                        ),
                        WorkflowStep(
                            step_type=StepType.ACTION,
                            action=ActionStep(
                                action_type=ActionType.NOTIFICATION, params={"message": "b"}
                            ),
                        ),
                    ],
                )
            ],
        )
        run = await executor.run(wf)
        assert run.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_condition_true(self):
        executor = WorkflowExecutor()
        wf = Workflow(
            workflow_id="w3",
            name="Cond",
            steps=[
                WorkflowStep(
                    step_type=StepType.ACTION,
                    action=ActionStep(
                        action_type=ActionType.NOTIFICATION, params={"message": "first"}
                    ),
                ),
                WorkflowStep(
                    step_type=StepType.CONDITION,
                    condition=Condition(field="notified", operator="eq", value=True),
                    on_true=[
                        WorkflowStep(
                            step_type=StepType.ACTION,
                            action=ActionStep(
                                action_type=ActionType.NOTIFICATION, params={"message": "yes"}
                            ),
                        )
                    ],
                ),
            ],
        )
        run = await executor.run(wf)
        assert run.status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_evaluate_operators(self):
        executor = WorkflowExecutor()
        assert executor._evaluate(5, "gt", 3) is True
        assert executor._evaluate(5, "lt", 3) is False
        assert executor._evaluate("hello world", "contains", "world") is True
        assert executor._evaluate(None, "exists", None) is False
        assert executor._evaluate("x", "exists", None) is True


class TestAutomationAPI:
    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from api.automation import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_list_workflows(self, client):
        resp = client.get("/automation/workflows")
        assert resp.status_code == 200
        assert "workflows" in resp.json()

    def test_create_workflow(self, client):
        resp = client.post(
            "/automation/workflows",
            json={
                "name": "Test API WF",
                "steps": [{"type": "notification", "params": {"message": "hello"}}],
            },
        )
        assert resp.status_code == 200
        assert "workflow_id" in resp.json()

    def test_run_workflow(self, client):
        # Create first
        create = client.post(
            "/automation/workflows",
            json={
                "name": "Run API",
                "steps": [{"type": "notification", "params": {"message": "run"}}],
            },
        )
        wf_id = create.json()["workflow_id"]
        # Run
        resp = client.post("/automation/run", json={"workflow_id": wf_id})
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_get_history(self, client):
        resp = client.get("/automation/history")
        assert resp.status_code == 200
        assert "runs" in resp.json()

    def test_get_templates(self, client):
        resp = client.get("/automation/templates")
        assert resp.status_code == 200
        assert len(resp.json()["templates"]) >= 3

    def test_get_status(self, client):
        resp = client.get("/automation/status")
        assert resp.status_code == 200
        assert "workflows" in resp.json()

    def test_delete_workflow(self, client):
        create = client.post("/automation/workflows", json={"name": "Del", "steps": []})
        wf_id = create.json()["workflow_id"]
        resp = client.delete(f"/automation/workflows/{wf_id}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True
