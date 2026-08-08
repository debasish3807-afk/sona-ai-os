"""Domain events for the Security Layer service.

Captures important security-related occurrences for audit, monitoring,
and event-driven processing.
"""

from dataclasses import dataclass

from sona_shared.domain.primitives import DomainEvent


@dataclass(frozen=True)
class AuthenticationSucceededEvent(DomainEvent):
    """Emitted when a user successfully authenticates."""

    user_id: str = ""
    method: str = ""


@dataclass(frozen=True)
class AuthenticationFailedEvent(DomainEvent):
    """Emitted when an authentication attempt fails."""

    username: str = ""
    reason: str = ""
    ip_address: str = ""


@dataclass(frozen=True)
class TokenRevokedEvent(DomainEvent):
    """Emitted when a token is revoked."""

    user_id: str = ""
    token_id: str = ""


@dataclass(frozen=True)
class PermissionDeniedEvent(DomainEvent):
    """Emitted when a permission check fails."""

    user_id: str = ""
    resource: str = ""
    action: str = ""


@dataclass(frozen=True)
class SecurityThreatEvent(DomainEvent):
    """Emitted when a security threat is detected."""

    threat_type: str = ""
    content_hash: str = ""
    user_id: str = ""
    blocked: bool = True
