"""Voice command recognition — maps spoken text to actions.

Detects structured voice commands from transcribed text and routes
them to the appropriate workspace action.
"""

from __future__ import annotations

import re
from typing import Any

from config.logging import get_logger
from voice.schemas import VoiceCommand, VoiceCommandResult

logger = get_logger(__name__)

# Command patterns (compiled regex for performance)
_PATTERNS: list[tuple[VoiceCommand, re.Pattern[str], list[str]]] = [
    (
        VoiceCommand.OPEN_FILE,
        re.compile(r"(?:open|show|read)\s+(?:file|the file)\s+(.+)", re.I),
        ["filename"],
    ),
    (
        VoiceCommand.SEARCH_PROJECT,
        re.compile(
            r"(?:search|find|look for)\s+(?:in )?(?:project|code|files?)\s+(?:for\s+)?(.+)", re.I
        ),
        ["query"],
    ),
    (
        VoiceCommand.START_RESEARCH,
        re.compile(r"(?:research|investigate|look up|find out about)\s+(.+)", re.I),
        ["topic"],
    ),
    (
        VoiceCommand.READ_DOCUMENT,
        re.compile(r"(?:read|read out|read aloud)\s+(?:document|doc|file)\s+(.+)", re.I),
        ["filename"],
    ),
    (
        VoiceCommand.OPEN_TERMINAL,
        re.compile(r"(?:open|show|launch)\s+(?:the\s+)?terminal", re.I),
        [],
    ),
    (
        VoiceCommand.RUN_COMMAND,
        re.compile(r"(?:run|execute|do)\s+(?:command\s+)?(.+)", re.I),
        ["command"],
    ),
    (
        VoiceCommand.GITHUB_SEARCH,
        re.compile(r"(?:search|find|look)\s+(?:on\s+)?github\s+(?:for\s+)?(.+)", re.I),
        ["query"],
    ),
    (
        VoiceCommand.MEMORY_SEARCH,
        re.compile(r"(?:search|find|recall|remember)\s+(?:in\s+)?memory\s+(?:for\s+)?(.+)", re.I),
        ["query"],
    ),
    (
        VoiceCommand.STOP_SPEAKING,
        re.compile(r"(?:stop|quiet|silence|shut up|be quiet|stop speaking|stop talking)", re.I),
        [],
    ),
]


def recognize_command(text: str) -> VoiceCommandResult:
    """Recognize a voice command from transcribed text.

    Args:
        text: The transcribed speech text.

    Returns:
        VoiceCommandResult with the detected command and parameters.
    """
    text = text.strip()
    if not text:
        return VoiceCommandResult(
            command=VoiceCommand.UNKNOWN,
            raw_text=text,
            confidence=0.0,
        )

    for command, pattern, param_names in _PATTERNS:
        match = pattern.search(text)
        if match:
            params: dict[str, Any] = {}
            for i, name in enumerate(param_names):
                if i < len(match.groups()):
                    params[name] = match.group(i + 1).strip()

            logger.debug("voice_command_recognized", command=command.value, params=params)
            return VoiceCommandResult(
                command=command,
                parameters=params,
                confidence=0.85,
                raw_text=text,
            )

    return VoiceCommandResult(
        command=VoiceCommand.UNKNOWN,
        raw_text=text,
        confidence=0.0,
    )


def detect_wake_word(text: str, wake_word: str = "hey sona") -> bool:
    """Check if the text contains the wake word.

    Args:
        text: The transcribed text to check.
        wake_word: The configured wake word phrase.

    Returns:
        True if wake word detected.
    """
    return wake_word.lower() in text.lower()
