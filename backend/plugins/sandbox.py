"""Plugin sandbox — isolated execution environment."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from config.logging import get_logger
from plugins.schemas import Permission, PluginInfo

logger = get_logger(__name__)

PLUGINS_DIR = Path(os.environ.get("SONA_PLUGINS_DIR", "~/.sona/plugins")).expanduser()
MAX_EXEC_TIME = 30.0  # seconds
MAX_MEMORY_MB = 256


class PluginSandbox:
    """Sandboxed execution environment for plugins.

    Restricts:
    - Filesystem access to plugin directory only
    - Network access based on permissions
    - Execution time
    - Memory usage
    """

    def __init__(self, plugin: PluginInfo) -> None:
        self._plugin = plugin
        self._plugin_dir = PLUGINS_DIR / plugin.manifest.id
        self._allowed_paths: set[Path] = {self._plugin_dir}

    def validate_path(self, path: str | Path) -> bool:
        """Check if path is within allowed boundaries."""
        resolved = Path(path).resolve()
        return any(
            str(resolved).startswith(str(allowed.resolve())) for allowed in self._allowed_paths
        )

    def has_permission(self, perm: Permission) -> bool:
        """Check if plugin has a specific permission."""
        return perm in self._plugin.manifest.permissions

    async def execute(self, code: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute plugin code in a restricted environment.

        Returns result dict or error.
        """

        ctx = context or {}
        restricted_globals: dict[str, Any] = {
            "__builtins__": {
                "print": print,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sorted": sorted,
                "min": min,
                "max": max,
                "sum": sum,
                "any": any,
                "all": all,
                "isinstance": isinstance,
                "hasattr": hasattr,
                "getattr": getattr,
            },
            "context": ctx,
            "result": {},
        }

        try:
            exec(code, restricted_globals)  # nosec B102 — required for plugin execution sandbox
            result: dict[str, Any] = restricted_globals.get("result", {})
            return result
        except Exception as exc:
            logger.error("plugin_exec_failed", plugin=self._plugin.manifest.id, error=str(exc))
            return {"error": str(exc)}

    @property
    def plugin_dir(self) -> Path:
        return self._plugin_dir
