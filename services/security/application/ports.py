"""Abstract port interfaces for the Security Layer service.

Defines the contracts that infrastructure adapters must implement
to provide authentication, authorization, and AI safety capabilities.
"""

from abc import ABC, abstractmethod
from typing import Any

from domain.models import AuthToken, Permission, Role


class AuthenticationPort(ABC):
    """Port for authentication operations.

    Infrastructure adapters implement this port to provide user/service
    authentication, token management, and session lifecycle operations.
    """

    @abstractmethod
    async def authenticate(self, credentials: dict[str, Any]) -> AuthToken:
        """Authenticate a user or service with the provided credentials.

        Args:
            credentials: A dictionary containing authentication credentials
                (e.g., username/password, API key, OAuth token).

        Returns:
            An AuthToken representing the authenticated session.

        Raises:
            AuthenticationError: If the credentials are invalid.
        """
        ...

    @abstractmethod
    async def validate_token(self, token: str) -> AuthToken | None:
        """Validate an existing authentication token.

        Args:
            token: The token string to validate.

        Returns:
            The AuthToken if valid and not expired, or None if invalid.
        """
        ...

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> AuthToken:
        """Refresh an expired or expiring token.

        Args:
            refresh_token: The refresh token used to obtain a new auth token.

        Returns:
            A new AuthToken with updated expiration.

        Raises:
            AuthenticationError: If the refresh token is invalid or revoked.
        """
        ...

    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """Revoke an authentication token, invalidating it immediately.

        Args:
            token: The token string to revoke.

        Returns:
            True if the token was successfully revoked, False otherwise.
        """
        ...


class AuthorizationPort(ABC):
    """Port for authorization operations.

    Infrastructure adapters implement this port to provide role-based
    access control (RBAC), permission checking, and role management.
    """

    @abstractmethod
    async def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if a user has a specific permission.

        Args:
            user_id: The unique identifier of the user to check.
            permission: The Permission to verify against the user's roles.

        Returns:
            True if the user has the permission, False otherwise.
        """
        ...

    @abstractmethod
    async def get_user_roles(self, user_id: str) -> list[Role]:
        """Get all roles assigned to a user.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            A list of Role values assigned to the user.
        """
        ...

    @abstractmethod
    async def assign_role(self, user_id: str, role: Role) -> bool:
        """Assign a role to a user.

        Args:
            user_id: The unique identifier of the user.
            role: The Role to assign.

        Returns:
            True if the role was successfully assigned, False otherwise.
        """
        ...


class AISafetyPort(ABC):
    """Port for AI safety and content moderation operations.

    Infrastructure adapters implement this port to provide input/output
    content safety checks and audit logging for AI interactions.
    """

    @abstractmethod
    async def check_input(self, content: str) -> tuple[bool, str | None]:
        """Check if input content is safe for AI processing.

        Args:
            content: The input content to check for safety violations.

        Returns:
            A tuple of (is_safe, reason). If safe, reason is None.
            If unsafe, reason contains a description of the violation.
        """
        ...

    @abstractmethod
    async def check_output(self, content: str) -> tuple[bool, str | None]:
        """Check if AI-generated output content is safe for delivery.

        Args:
            content: The output content to check for safety violations.

        Returns:
            A tuple of (is_safe, reason). If safe, reason is None.
            If unsafe, reason contains a description of the violation.
        """
        ...

    @abstractmethod
    async def audit_log(self, event: dict[str, Any]) -> None:
        """Record an audit log entry for AI safety events.

        Args:
            event: A dictionary containing event details such as
                event_type, timestamp, user_id, content_hash, and outcome.
        """
        ...
