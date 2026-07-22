"""Plugin permission validation and enforcement."""

from __future__ import annotations

from config.logging import get_logger
from plugins.schemas import Permission, PluginManifest

logger = get_logger(__name__)

# Default maximum permissions per plugin type
_TYPE_MAX_PERMISSIONS: dict[str, set[Permission]] = {
    "ai": {Permission.AI_COMPLETE, Permission.MEMORY_READ, Permission.NETWORK},
    "research": {Permission.NETWORK, Permission.MEMORY_WRITE, Permission.RESEARCH},
    "vision": {Permission.FILESYSTEM_READ, Permission.VISION},
    "voice": {Permission.VOICE, Permission.AI_COMPLETE},
    "memory": {Permission.MEMORY_READ, Permission.MEMORY_WRITE},
    "automation": {
        Permission.TERMINAL,
        Permission.FILESYSTEM_READ,
        Permission.FILESYSTEM_WRITE,
        Permission.NETWORK,
    },
    "github": {Permission.NETWORK},
    "terminal": {Permission.TERMINAL, Permission.FILESYSTEM_READ},
    "general": {Permission.MEMORY_READ},
}


def validate_permissions(manifest: PluginManifest) -> list[str]:
    """Validate plugin permissions against its type constraints.

    Returns list of violation messages (empty = valid).
    """
    violations: list[str] = []
    allowed = _TYPE_MAX_PERMISSIONS.get(manifest.plugin_type.value, set())

    for perm in manifest.permissions:
        if perm not in allowed:
            violations.append(
                f"Permission '{perm.value}' not allowed for "
                f"plugin type '{manifest.plugin_type.value}'"
            )

    return violations


def check_permission(granted: list[Permission], required: Permission) -> bool:
    """Check if a specific permission is granted."""
    return required in granted
