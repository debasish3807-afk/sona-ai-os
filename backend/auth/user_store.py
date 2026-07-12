"""User store — in-memory user persistence for authentication.

Production: replace with database-backed repository.
"""

from __future__ import annotations

from datetime import UTC, datetime

from auth.passwords import hash_password, verify_password
from config.logging import get_logger
from models.user import User, UserRole

logger = get_logger(__name__)

# In-memory user store (production: use PostgreSQL)
_users: dict[str, User] = {}
_username_index: dict[str, str] = {}  # username → user_id
_email_index: dict[str, str] = {}  # email → user_id

# Rate limiting: track failed login attempts
_login_attempts: dict[str, list[float]] = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300


def _is_rate_limited(identifier: str) -> bool:
    """Check if login attempts are rate-limited."""
    now = datetime.now(UTC).timestamp()
    attempts = _login_attempts.get(identifier, [])
    # Remove attempts older than lockout window
    recent = [t for t in attempts if now - t < LOCKOUT_SECONDS]
    _login_attempts[identifier] = recent
    return len(recent) >= MAX_LOGIN_ATTEMPTS


def _record_failed_attempt(identifier: str) -> None:
    """Record a failed login attempt."""
    now = datetime.now(UTC).timestamp()
    if identifier not in _login_attempts:
        _login_attempts[identifier] = []
    _login_attempts[identifier].append(now)


def _clear_attempts(identifier: str) -> None:
    """Clear login attempts on successful login."""
    _login_attempts.pop(identifier, None)


def create_user(
    username: str,
    email: str,
    password: str,
    role: UserRole = UserRole.USER,
) -> User | None:
    """Create a new user.

    Args:
        username: Unique username.
        email: Unique email address.
        password: Plaintext password (will be hashed).
        role: User role.

    Returns:
        Created User or None if username/email exists.
    """
    if username.lower() in _username_index:
        return None
    if email.lower() in _email_index:
        return None

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    _users[user.user_id] = user
    _username_index[username.lower()] = user.user_id
    _email_index[email.lower()] = user.user_id

    logger.info("User created", username=username, role=role.value)
    return user


def authenticate_user(username: str, password: str) -> User | None:
    """Authenticate a user by username and password.

    Implements rate limiting and constant-time verification.

    Args:
        username: The username to authenticate.
        password: The plaintext password.

    Returns:
        Authenticated User or None if invalid.
    """
    if _is_rate_limited(username.lower()):
        logger.warning("Login rate-limited", username=username)
        return None

    user_id = _username_index.get(username.lower())
    if user_id is None:
        # Constant-time: still verify against dummy hash
        verify_password(password, hash_password("dummy"))
        _record_failed_attempt(username.lower())
        return None

    user = _users.get(user_id)
    if user is None or not user.is_active:
        _record_failed_attempt(username.lower())
        return None

    if not verify_password(password, user.password_hash):
        _record_failed_attempt(username.lower())
        return None

    # Success
    _clear_attempts(username.lower())
    user.last_login = datetime.now(UTC).isoformat()
    user.updated_at = datetime.now(UTC).isoformat()
    return user


def get_user_by_id(user_id: str) -> User | None:
    """Get user by ID."""
    return _users.get(user_id)


def get_user_by_username(username: str) -> User | None:
    """Get user by username."""
    user_id = _username_index.get(username.lower())
    if user_id:
        return _users.get(user_id)
    return None


def change_password(user_id: str, old_password: str, new_password: str) -> bool:
    """Change a user's password.

    Args:
        user_id: The user's ID.
        old_password: Current password for verification.
        new_password: New password to set.

    Returns:
        True if password was changed.
    """
    user = _users.get(user_id)
    if user is None:
        return False
    if not verify_password(old_password, user.password_hash):
        return False
    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.now(UTC).isoformat()
    return True


def list_users() -> list[User]:
    """List all users (admin only)."""
    return list(_users.values())


def reset_store() -> None:
    """Reset the user store (for testing)."""
    _users.clear()
    _username_index.clear()
    _email_index.clear()
    _login_attempts.clear()
