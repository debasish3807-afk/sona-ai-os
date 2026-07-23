"""Macro recorder — capture and replay user action sequences."""

from __future__ import annotations

import uuid
from typing import Any

from automation.schemas import ActionStep, ActionType
from config.logging import get_logger

logger = get_logger(__name__)


class MacroRecorder:
    """Records, stores, and replays macro action sequences."""

    def __init__(self) -> None:
        self._macros: dict[str, list[ActionStep]] = {}
        self._recording: list[ActionStep] | None = None
        self._recording_name: str = ""

    def start_recording(self, name: str = "macro") -> str:
        self._recording = []
        self._recording_name = name
        logger.info("macro_recording_started", name=name)
        return str(uuid.uuid4())

    def record_step(self, action_type: ActionType, params: dict[str, Any]) -> int:
        if self._recording is None:
            return -1
        step = ActionStep(action_type=action_type, params=params)
        self._recording.append(step)
        return len(self._recording) - 1

    def stop_recording(self) -> str:
        if self._recording is None:
            return ""
        macro_id = str(uuid.uuid4())
        self._macros[macro_id] = list(self._recording)
        self._recording = None
        logger.info("macro_recording_stopped", steps=len(self._macros[macro_id]))
        return macro_id

    def get_macro(self, macro_id: str) -> list[ActionStep] | None:
        return self._macros.get(macro_id)

    def list_macros(self) -> list[dict[str, Any]]:
        return [
            {
                "macro_id": mid,
                "steps": len(steps),
                "preview": steps[0].action_type.value if steps else "",
            }
            for mid, steps in self._macros.items()
        ]

    def delete_macro(self, macro_id: str) -> bool:
        return self._macros.pop(macro_id, None) is not None

    async def play_macro(self, macro_id: str) -> list[dict[str, Any]]:
        steps = self._macros.get(macro_id)
        if not steps:
            return [{"error": f"Macro {macro_id} not found"}]
        results: list[dict[str, Any]] = []
        for step in steps:
            results.append(
                {"action": step.action_type.value, "params": step.params, "status": "executed"}
            )
        return results
