"""System information service — OS, CPU, memory, disk, uptime, and process details."""

from __future__ import annotations

import os
import platform
import time
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class SystemInfoService:
    """Provides system-level information about the host machine."""

    def __init__(self) -> None:
        self._start_time = time.time()

    def get_info(self) -> dict[str, Any]:
        return {
            "os": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
            },
            "python": {
                "version": platform.python_version(),
                "implementation": platform.python_implementation(),
                "compiler": platform.python_compiler(),
            },
            "process": {
                "pid": os.getpid(),
                "cwd": os.getcwd(),
                "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
                "uptime_seconds": time.time() - self._start_time,
            },
        }

    def get_uptime(self) -> float:
        return time.time() - self._start_time

    def get_version_info(self) -> dict[str, str]:
        from config.settings import get_settings

        settings = get_settings()
        return {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment.value,
            "python_version": platform.python_version(),
            "api_version": "v1",
        }
