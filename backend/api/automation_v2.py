"""Automation Engine API — Phase 26 endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from automation.api_automation import APIAutomation
from automation.browser_automation import BrowserAutomation
from automation.desktop_automation import DesktopAutomation
from automation.engine import AutomationEngine
from automation.history import AutomationHistory
from automation.macro import MacroRecorder
from automation.retry import RetryHandler
from automation.scheduler_engine import SchedulerEngine
from automation.schemas import ScheduleConfig
from automation.templates import AutomationTemplates

router = APIRouter(prefix="/automation", tags=["automation-v2"])

_engine = AutomationEngine()
_scheduler = SchedulerEngine(_engine)
_history = AutomationHistory()
_macros = MacroRecorder()
_templates = AutomationTemplates()
_retry = RetryHandler()
_browser = BrowserAutomation()
_desktop = DesktopAutomation()
_api = APIAutomation()


@router.get("/schedules")
async def list_schedules():
    return {
        "schedules": [vars(s) for s in _scheduler.list_schedules()],
        "count": len(_scheduler.list_schedules()),
    }


@router.post("/schedules")
async def create_schedule(cron_expr: str, workflow_id: str, name: str = "", enabled: bool = True):
    config = ScheduleConfig(
        cron_expr=cron_expr, workflow_id=workflow_id, name=name, enabled=enabled
    )
    sid = _scheduler.add_schedule(config)
    return {"schedule_id": sid, "status": "created", "cron": cron_expr}


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    if not _scheduler.remove_schedule(schedule_id):
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"status": "deleted"}


@router.post("/schedules/tick")
async def tick_schedules():
    triggered = _scheduler.tick()
    return {"triggered": triggered, "count": len(triggered)}


@router.get("/history")
async def list_history(limit: int = 50, status: str | None = None):
    return {"entries": [_vars(e) for e in _history.list_entries(limit=limit, status=status)]}


@router.get("/history/stats")
async def history_stats():
    return _history.get_stats()


@router.post("/macro/start")
async def macro_start(name: str = "macro"):
    mid = _macros.start_recording(name)
    return {"macro_id": mid, "recording": True}


@router.post("/macro/stop")
async def macro_stop():
    mid = _macros.stop_recording()
    return {"macro_id": mid, "recording": False, "steps": len(_macros.get_macro(mid) or [])}


@router.get("/macro/list")
async def macro_list():
    return {"macros": _macros.list_macros()}


@router.delete("/macro/{macro_id}")
async def macro_delete(macro_id: str):
    if not _macros.delete_macro(macro_id):
        raise HTTPException(status_code=404, detail="Macro not found")
    return {"status": "deleted"}


@router.post("/macro/{macro_id}/play")
async def macro_play(macro_id: str):
    results = await _macros.play_macro(macro_id)
    return {"status": "completed", "steps": len(results), "results": results}


@router.get("/templates")
async def list_templates(category: str | None = None):
    templates = _templates.list_templates(category)
    return {"templates": [_safe_vars(t) for t in templates], "count": len(templates)}


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    t = _templates.get_template(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return _safe_vars(t)


@router.get("/health")
async def automation_health():
    return {
        "schedules": len(_scheduler.list_schedules()),
        "history_total": _history.get_stats()["total"],
        "macros": len(_macros.list_macros()),
        "templates": len(_templates.list_templates()),
        "desktop_available": _desktop.is_available,
    }


def _safe_vars(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "__dataclass_fields__"):
        result: dict[str, Any] = {}
        for k in obj.__dataclass_fields__:
            result[k] = getattr(obj, k)
        return result
    return dict(vars(obj))


def _vars(obj: Any) -> dict[str, Any]:
    return dict(vars(obj))
