"""AI Safety service implementing the AISafetyPort.

Provides prompt injection detection, jailbreak detection, and output safety
validation using pattern matching.
"""

import base64
import hashlib
import re
import time
from typing import Any

import structlog

from sona_security.application.ports import AISafetyPort
from sona_security.domain.events import SecurityThreatEvent

logger = structlog.get_logger()

# Prompt injection patterns (at least 10)
INJECTION_PATTERNS: list[tuple[str, str]] = [
    (r"ignore\s+(all\s+)?previous\s+instructions", "ignore_previous_instructions"),
    (r"you\s+are\s+now", "identity_override"),
    (r"system\s*prompt\s*:", "system_prompt_leak"),
    (r"pretend\s+(you\s+are|to\s+be)", "pretend_identity"),
    (r"\bbypass\b", "bypass_attempt"),
    (r"\boverride\b", "override_attempt"),
    (r"\bhack\b", "hack_attempt"),
    (r"disregard\s+(all\s+)?(previous|above|prior)", "disregard_instructions"),
    (r"forget\s+(all\s+)?(your|previous|prior)", "forget_instructions"),
    (r"new\s+instructions?\s*:", "new_instructions"),
    (r"do\s+not\s+follow\s+(your|any|the)\s+(rules|instructions|guidelines)", "rule_override"),
    (r"act\s+as\s+(if|though)\s+you", "act_as_override"),
    (r"reveal\s+(your|the)\s+(system|hidden|secret)", "reveal_system"),
    (r"jailbreak", "jailbreak_keyword"),
    (r"DAN\s+mode", "dan_mode"),
]

# Compiled patterns for efficiency
COMPILED_INJECTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(pattern, re.IGNORECASE), name) for pattern, name in INJECTION_PATTERNS
]

# Output safety patterns
OUTPUT_UNSAFE_PATTERNS: list[tuple[str, str]] = [
    (r"(password|secret|api.?key)\s*[:=]\s*\S+", "credential_leak"),
    (r"ssh-rsa\s+[A-Za-z0-9+/]+", "ssh_key_leak"),
    (r"BEGIN\s+(RSA|DSA|EC)\s+PRIVATE\s+KEY", "private_key_leak"),
]

COMPILED_OUTPUT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(pattern, re.IGNORECASE), name) for pattern, name in OUTPUT_UNSAFE_PATTERNS
]


class AISafetyService(AISafetyPort):
    """AI Safety service implementing AISafetyPort.

    Detects prompt injections, jailbreak attempts, and validates output safety.
    """

    def __init__(self) -> None:
        self._audit_entries: list[dict[str, Any]] = []
        self._events: list[object] = []
        self._max_special_char_ratio: float = 0.4
        self._max_input_length: int = 50000

    @property
    def events(self) -> list[object]:
        """Access collected domain events."""
        return self._events

    def clear_events(self) -> None:
        """Clear collected domain events."""
        self._events.clear()

    @property
    def audit_entries(self) -> list[dict[str, Any]]:
        """Access audit log entries."""
        return self._audit_entries

    async def check_input(self, content: str) -> tuple[bool, str | None]:
        """Check if input content is safe for AI processing."""
        if not content:
            return (True, None)

        # Check length
        if len(content) > self._max_input_length:
            return (False, "Input exceeds maximum length")

        # Check for prompt injection patterns
        for pattern, threat_name in COMPILED_INJECTION_PATTERNS:
            if pattern.search(content):
                self._events.append(
                    SecurityThreatEvent(
                        threat_type=f"prompt_injection:{threat_name}",
                        content_hash=self._hash_content(content),
                        blocked=True,
                    )
                )
                logger.warning("prompt_injection_detected", pattern=threat_name)
                return (False, f"Prompt injection detected: {threat_name}")

        # Check for excessive special characters (encoding attacks)
        if self._has_excessive_special_chars(content):
            self._events.append(
                SecurityThreatEvent(
                    threat_type="encoding_attack",
                    content_hash=self._hash_content(content),
                    blocked=True,
                )
            )
            return (False, "Suspicious encoding pattern detected")

        # Check for base64-encoded instructions
        if self._contains_base64_instructions(content):
            self._events.append(
                SecurityThreatEvent(
                    threat_type="base64_injection",
                    content_hash=self._hash_content(content),
                    blocked=True,
                )
            )
            return (False, "Base64-encoded instruction detected")

        return (True, None)

    async def check_output(self, content: str) -> tuple[bool, str | None]:
        """Check if AI-generated output is safe for delivery."""
        if not content:
            return (True, None)

        # Check for credential/key leaks
        for pattern, threat_name in COMPILED_OUTPUT_PATTERNS:
            if pattern.search(content):
                self._events.append(
                    SecurityThreatEvent(
                        threat_type=f"output_unsafe:{threat_name}",
                        content_hash=self._hash_content(content),
                        blocked=True,
                    )
                )
                logger.warning("unsafe_output_detected", pattern=threat_name)
                return (False, f"Unsafe output detected: {threat_name}")

        return (True, None)

    async def audit_log(self, event: dict[str, Any]) -> None:
        """Record an audit log entry for AI safety events."""
        event.setdefault("timestamp", time.time())
        self._audit_entries.append(event)
        logger.info("ai_safety_audit", **event)

    def _hash_content(self, content: str) -> str:
        """Create a SHA-256 hash of content for audit purposes."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _has_excessive_special_chars(self, content: str) -> bool:
        """Check if content has an excessive ratio of special characters."""
        if len(content) < 10:
            return False
        special_count = sum(1 for c in content if not c.isalnum() and not c.isspace())
        ratio = special_count / len(content)
        return ratio > self._max_special_char_ratio

    def _contains_base64_instructions(self, content: str) -> bool:
        """Check if content contains base64-encoded instructions."""
        # Look for base64 strings of sufficient length
        b64_pattern = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")
        matches = b64_pattern.findall(content)
        for match in matches:
            try:
                decoded = base64.b64decode(match).decode("utf-8", errors="ignore")
                # Check if decoded content looks like instructions
                for pattern, _name in COMPILED_INJECTION_PATTERNS:
                    if pattern.search(decoded):
                        return True
            except (ValueError, UnicodeDecodeError):
                continue
        return False
