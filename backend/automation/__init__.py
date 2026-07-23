"""Automation Engine — actions, scheduling, history, templates, macros."""

from automation.api_automation import APIAutomation
from automation.browser_automation import BrowserAutomation
from automation.desktop_automation import DesktopAutomation
from automation.engine import AutomationEngine
from automation.history import AutomationHistory
from automation.macro import MacroRecorder
from automation.retry import RetryHandler
from automation.scheduler_engine import SchedulerEngine
from automation.templates import AutomationTemplates

__all__ = [
    "APIAutomation",
    "AutomationEngine",
    "AutomationHistory",
    "AutomationTemplates",
    "BrowserAutomation",
    "DesktopAutomation",
    "MacroRecorder",
    "RetryHandler",
    "SchedulerEngine",
]
