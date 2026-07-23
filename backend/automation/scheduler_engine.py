"""Schedule engine — cron-based scheduling with in-memory storage."""

from __future__ import annotations

import calendar
import re
import time

from automation.engine import AutomationEngine
from automation.schemas import ScheduleConfig
from config.logging import get_logger

logger = get_logger(__name__)

_cron_re = re.compile(r"^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)$")


def _parse_cron(expr: str) -> dict[str, set[int]] | None:
    """Parse a 5-field cron expression into field sets."""
    m = _cron_re.match(expr)
    if not m:
        return None
    return {
        "minute": _parse_field(m.group(1), 0, 59),
        "hour": _parse_field(m.group(2), 0, 23),
        "day": _parse_field(m.group(3), 1, 31),
        "month": _parse_field(m.group(4), 1, 12),
        "weekday": _parse_field(m.group(5), 0, 6),
    }


def _parse_field(field: str, min_val: int, max_val: int) -> set[int]:
    """Parse a single cron field (supports numbers, *, ranges, steps)."""
    result: set[int] = set()
    if field == "*":
        return set(range(min_val, max_val + 1))
    for part in field.split(","):
        if "/" in part:
            base, step = part.split("/", 1)
            step = int(step)  # type: ignore[assignment]
            if base == "*":
                base_range = range(min_val, max_val + 1)
            elif "-" in base:
                a, b = base.split("-", 1)
                base_range = range(int(a), int(b) + 1)
            else:
                base_range = range(int(base), max_val + 1)
            for v in base_range:
                if (v - min_val) % int(step) == 0:
                    result.add(v)
        elif "-" in part:
            a_str, b_str = part.split("-", 1)
            result.update(range(int(a_str), int(b_str) + 1))
        else:
            result.add(int(part))
    return result


def _next_match(cron_fields: dict[str, set[int]], after: float) -> float | None:
    """Compute the next timestamp matching a cron expression after 'after'."""
    t = time.gmtime(after + 60)
    for _ in range(365 * 24 * 60):
        if t.tm_mon not in cron_fields["month"]:
            t = time.gmtime(calendar.timegm((t.tm_year, t.tm_mon + 1, 1, 0, 0, 0)))
            continue
        if t.tm_mday not in cron_fields["day"] and t.tm_wday not in cron_fields["weekday"]:
            t = time.gmtime(calendar.timegm((t.tm_year, t.tm_mon, t.tm_mday + 1, 0, 0, 0)))
            continue
        if t.tm_hour not in cron_fields["hour"]:
            t = time.gmtime(calendar.timegm((t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour + 1, 0, 0)))
            continue
        if t.tm_min not in cron_fields["minute"]:
            t = time.gmtime(
                calendar.timegm((t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min + 1, 0))
            )
            continue
        return calendar.timegm(t)
    return None


class SchedulerEngine:
    """Cron-based scheduler that triggers workflow execution."""

    def __init__(self, engine: AutomationEngine) -> None:
        self._engine = engine
        self._schedules: dict[str, ScheduleConfig] = {}
        self._running = False

    def add_schedule(self, config: ScheduleConfig) -> str:
        if not config.schedule_id:
            import uuid

            config.schedule_id = str(uuid.uuid4())
        if config.cron_expr:
            parsed = _parse_cron(config.cron_expr)
            if parsed:
                config.next_run = _next_match(parsed, time.time())
        self._schedules[config.schedule_id] = config
        logger.info("schedule_added", id=config.schedule_id, cron=config.cron_expr)
        return config.schedule_id

    def remove_schedule(self, schedule_id: str) -> bool:
        removed = self._schedules.pop(schedule_id, None) is not None
        if removed:
            logger.info("schedule_removed", id=schedule_id)
        return removed

    def get_schedule(self, schedule_id: str) -> ScheduleConfig | None:
        return self._schedules.get(schedule_id)

    def list_schedules(self) -> list[ScheduleConfig]:
        return list(self._schedules.values())

    def tick(self) -> list[str]:
        """Check all schedules and execute any that are due."""
        now = time.time()
        triggered: list[str] = []
        for sid, config in list(self._schedules.items()):
            if not config.enabled or config.next_run is None:
                continue
            if now >= config.next_run:
                config.last_run = now
                parsed = _parse_cron(config.cron_expr)
                if parsed:
                    config.next_run = _next_match(parsed, now)
                triggered.append(sid)
        return triggered
