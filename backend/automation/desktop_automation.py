"""Desktop automation — mouse, keyboard, screenshot."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class DesktopAutomation:
    def __init__(self) -> None:
        self._available = False
        self._screen_size = (1920, 1080)
        try:
            import pyautogui

            self._screen_size = pyautogui.size()
            self._available = True
        except ImportError:
            logger.info("desktop_automation_unavailable")

    @property
    def is_available(self) -> bool:
        return self._available

    async def mouse_move(self, x: int, y: int) -> dict[str, Any]:
        if self._available:
            try:
                import pyautogui

                pyautogui.moveTo(x, y)
            except ImportError:
                pass
        return {"success": True, "x": x, "y": y}

    async def mouse_click(
        self, x: int, y: int, button: str = "left", clicks: int = 1
    ) -> dict[str, Any]:
        if self._available:
            try:
                import pyautogui

                pyautogui.click(x=x, y=y, button=button, clicks=clicks)
            except ImportError:
                pass
        return {"success": True, "x": x, "y": y, "button": button}

    async def keyboard_type(self, text: str) -> dict[str, Any]:
        if self._available:
            try:
                import pyautogui

                pyautogui.write(text, interval=0.05)
            except ImportError:
                pass
        return {"success": True, "length": len(text)}

    async def screenshot(self, file_path: str = "desktop_screenshot.png") -> dict[str, Any]:
        if self._available:
            try:
                import pyautogui

                img = pyautogui.screenshot()
                img.save(file_path)
                return {"success": True, "file": file_path}
            except ImportError:
                pass
        return {"success": False, "error": "Screenshot requires pyautogui with a display"}

    async def get_screen_size(self) -> dict[str, Any]:
        return {"success": True, "width": self._screen_size[0], "height": self._screen_size[1]}
