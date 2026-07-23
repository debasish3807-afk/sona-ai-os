"""Tests for Phase 26: Automation Engine."""

import pytest

from automation.api_automation import APIAutomation
from automation.browser_automation import BrowserAutomation
from automation.desktop_automation import DesktopAutomation
from automation.history import AutomationHistory
from automation.macro import MacroRecorder
from automation.retry import RetryHandler
from automation.scheduler_engine import SchedulerEngine
from automation.schemas import (
    ActionStep,
    ActionType,
    AutomationTemplate,
    ScheduleConfig,
    WorkflowStatus,
)
from automation.templates import AutomationTemplates


class TestSchedulerEngine:
    def test_add_and_list_schedules(self):
        eng = SchedulerEngine(None)
        eng.add_schedule(ScheduleConfig(cron_expr="0 9 * * 1-5", name="weekday"))
        assert len(eng.list_schedules()) == 1

    def test_remove_schedule(self):
        eng = SchedulerEngine(None)
        sid = eng.add_schedule(ScheduleConfig(cron_expr="0 0 * * *"))
        assert eng.remove_schedule(sid) is True
        assert eng.remove_schedule("nonexistent") is False


class TestAutomationHistory:
    def test_record_and_retrieve(self):
        h = AutomationHistory()
        eid = h.record_start("wf-1", "test")
        assert eid is not None
        h.record_complete(eid, WorkflowStatus.COMPLETED)
        entry = h.get_entry(eid)
        assert entry is not None
        assert entry.status == WorkflowStatus.COMPLETED
        assert entry.duration_ms > 0

    def test_list_with_filters(self):
        h = AutomationHistory()
        eid = h.record_start("wf-2", "fail-test")
        h.record_complete(eid, WorkflowStatus.FAILED, "error occurred")
        entries = h.list_entries(status="failed")
        assert len(entries) == 1
        assert entries[0].error == "error occurred"

    def test_stats(self):
        h = AutomationHistory()
        for i in range(3):
            eid = h.record_start(f"wf-{i}", f"test-{i}")
            h.record_complete(eid, WorkflowStatus.COMPLETED)
        stats = h.get_stats()
        assert stats["total"] == 3
        assert stats["completed"] == 3


class TestMacroRecorder:
    def test_record_and_stop(self):
        m = MacroRecorder()
        m.start_recording("test-macro")
        m.record_step(ActionType.BROWSER_NAVIGATE, {"url": "https://example.com"})
        m.record_step(ActionType.TERMINAL, {"command": "echo hello"})
        final_id = m.stop_recording()
        assert final_id is not None
        steps = m.get_macro(final_id)
        assert steps is not None
        assert len(steps) == 2

    def test_list_and_delete(self):
        m = MacroRecorder()
        m.start_recording("m1")
        m.stop_recording()
        m.start_recording("m2")
        m.stop_recording()
        assert len(m.list_macros()) == 2
        first_mid = m.list_macros()[0]["macro_id"]
        assert m.delete_macro(first_mid) is True

    @pytest.mark.asyncio
    async def test_play(self):
        m = MacroRecorder()
        mid = m.start_recording()
        m.record_step(ActionType.NOTIFICATION, {"message": "test"})
        m.stop_recording()
        results = await m.play_macro(mid)
        assert len(results) == 1


class TestAutomationTemplates:
    def test_builtin_templates(self):
        t = AutomationTemplates()
        count = len(t.list_templates())
        assert count >= 4, "Should have at least 4 built-in templates"

    def test_get_template(self):
        t = AutomationTemplates()
        tmpl = t.get_template("daily-report")
        assert tmpl is not None
        assert tmpl.name == "Daily Report"

    def test_filter_by_category(self):
        t = AutomationTemplates()
        tmpls = t.list_templates(category="development")
        assert len(tmpls) >= 1

    def test_add_custom_template(self):
        t = AutomationTemplates()
        tmpl = AutomationTemplate(
            name="custom",
            category="custom",
            steps=[ActionStep(action_type=ActionType.AI_CHAT, params={"message": "hello"})],
        )
        tid = t.add_template(tmpl)
        assert t.get_template(tid) is not None

    def test_delete_template(self):
        t = AutomationTemplates()
        tid = t.add_template(AutomationTemplate(name="tmp"))
        assert t.delete_template(tid) is True


class TestRetryHandler:
    @pytest.mark.asyncio
    async def test_retry_success(self):
        handler = RetryHandler(max_retries=2)
        call_count = 0

        async def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await handler.execute_with_retry(succeed)
        assert result["success"] is True
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_failure(self):
        handler = RetryHandler(max_retries=1, base_delay=0.01)

        async def fail():
            raise ValueError("always fails")

        result = await handler.execute_with_retry(fail)
        assert result["success"] is False
        assert "always fails" in result["error"]


class TestBrowserAutomation:
    @pytest.mark.asyncio
    async def test_navigate_invalid(self):
        b = BrowserAutomation()
        result = await b.navigate("")
        assert result["success"] is False

    def test_history(self):
        b = BrowserAutomation()
        assert b.get_history() == []


class TestDesktopAutomation:
    @pytest.mark.asyncio
    async def test_screen_size(self):
        d = DesktopAutomation()
        result = await d.get_screen_size()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_mouse_click(self):
        d = DesktopAutomation()
        result = await d.mouse_click(100, 100)
        assert result["success"] is True


class TestAPIAutomation:
    def test_set_header(self):
        api = APIAutomation("https://example.com")
        api.set_header("Authorization", "Bearer test")
        assert api._headers["Authorization"] == "Bearer test"
