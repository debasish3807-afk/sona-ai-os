"""Intent Sanitizer — detects and neutralizes malicious input patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SanitizationResult:
    """Result of sanitizing an input string."""

    safe: bool
    threats: list[str] = field(default_factory=list)
    sanitized_input: str = ""
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "safe": self.safe,
            "threats": self.threats,
            "sanitized_input": self.sanitized_input,
            "confidence": self.confidence,
        }


# Compiled regex patterns for threat detection
INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a|an)\s+", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\|?(system|assistant|user)\|?>", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all|your)\s+", re.IGNORECASE),
    re.compile(r"new\s+role\s*:", re.IGNORECASE),
    re.compile(r"override\s+(instructions|rules|policy)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(if|though)\s+you\s+(have\s+)?no\s+restrictions", re.IGNORECASE),
]

COMMAND_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r";\s*(rm|del|drop|shutdown|kill|format)\s+", re.IGNORECASE),
    re.compile(r"\|\s*(bash|sh|cmd|powershell)", re.IGNORECASE),
    re.compile(r"`.*`\s*;", re.IGNORECASE),
    re.compile(r"\$\(.*\)", re.IGNORECASE),
    re.compile(r"&&\s*(rm|del|drop|shutdown)", re.IGNORECASE),
]

PATH_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\.\./", re.IGNORECASE),
    re.compile(r"\.\.\\", re.IGNORECASE),
    re.compile(r"/etc/(passwd|shadow|hosts)", re.IGNORECASE),
    re.compile(r"~/(\.ssh|\.env|\.aws)", re.IGNORECASE),
    re.compile(r"C:\\Windows\\System32", re.IGNORECASE),
]

SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(api[_-]?key|secret[_-]?key|password|token)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"(sk|pk|ak)-[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"AKIA[A-Z0-9]{16}", re.IGNORECASE),
    re.compile(r"(ghp|gho|ghu|ghs)_[A-Za-z0-9]{36,}", re.IGNORECASE),
]

EXFILTRATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(curl|wget|fetch)\s+https?://", re.IGNORECASE),
    re.compile(r"send\s+(data|file|content)\s+to\s+", re.IGNORECASE),
    re.compile(r"upload\s+(to|file|data)\s+", re.IGNORECASE),
    re.compile(r"exfiltrate", re.IGNORECASE),
]

POLICY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(bypass|disable|turn\s+off)\s+(safety|security|filter|guard)", re.IGNORECASE),
    re.compile(r"(jailbreak|uncensor|unrestrict)", re.IGNORECASE),
    re.compile(r"ignore\s+(safety|content)\s+(policy|filter|rules)", re.IGNORECASE),
]


class IntentSanitizer:
    """Detects and neutralizes malicious patterns in user input.

    Scans for prompt injection, command injection, path traversal,
    secret leakage, data exfiltration, and policy violations.
    """

    def sanitize(self, input_text: str) -> SanitizationResult:
        """Analyze input for threats and return sanitization result."""
        if not input_text.strip():
            return SanitizationResult(safe=True, sanitized_input="", confidence=1.0)

        threats: list[str] = []
        threats.extend(self._detect_prompt_injection(input_text))
        threats.extend(self._detect_command_injection(input_text))
        threats.extend(self._detect_path_traversal(input_text))
        threats.extend(self._detect_secret_leakage(input_text))
        threats.extend(self._detect_data_exfiltration(input_text))
        threats.extend(self._detect_policy_violations(input_text))

        safe = len(threats) == 0
        confidence = max(0.0, 1.0 - len(threats) * 0.15)

        if not safe:
            logger.warning("intent_threats_detected", threats=threats, count=len(threats))

        return SanitizationResult(
            safe=safe,
            threats=threats,
            sanitized_input=input_text if safe else "",
            confidence=confidence,
        )

    def _detect_prompt_injection(self, text: str) -> list[str]:
        """Detect prompt injection attempts."""
        found: list[str] = []
        for pattern in INJECTION_PATTERNS:
            if pattern.search(text):
                found.append(f"prompt_injection: {pattern.pattern[:50]}")
        return found

    def _detect_command_injection(self, text: str) -> list[str]:
        """Detect command injection attempts."""
        found: list[str] = []
        for pattern in COMMAND_PATTERNS:
            if pattern.search(text):
                found.append(f"command_injection: {pattern.pattern[:50]}")
        return found

    def _detect_path_traversal(self, text: str) -> list[str]:
        """Detect path traversal attempts."""
        found: list[str] = []
        for pattern in PATH_PATTERNS:
            if pattern.search(text):
                found.append(f"path_traversal: {pattern.pattern[:50]}")
        return found

    def _detect_secret_leakage(self, text: str) -> list[str]:
        """Detect potential secret or credential leakage."""
        found: list[str] = []
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                found.append(f"secret_leakage: {pattern.pattern[:50]}")
        return found

    def _detect_data_exfiltration(self, text: str) -> list[str]:
        """Detect data exfiltration attempts."""
        found: list[str] = []
        for pattern in EXFILTRATION_PATTERNS:
            if pattern.search(text):
                found.append(f"data_exfiltration: {pattern.pattern[:50]}")
        return found

    def _detect_policy_violations(self, text: str) -> list[str]:
        """Detect policy violation attempts."""
        found: list[str] = []
        for pattern in POLICY_PATTERNS:
            if pattern.search(text):
                found.append(f"policy_violation: {pattern.pattern[:50]}")
        return found
