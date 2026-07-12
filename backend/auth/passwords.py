"""Password hashing with Argon2.

Uses argon2-cffi for secure, constant-time password hashing
and verification. Never stores plaintext passwords.
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
)


def hash_password(password: str) -> str:
    """Hash a password using Argon2id.

    Args:
        password: The plaintext password.

    Returns:
        The Argon2 hash string.
    """
    hashed: str = str(_hasher.hash(password))
    return hashed


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash (constant-time).

    Args:
        password: The plaintext password to check.
        password_hash: The stored Argon2 hash.

    Returns:
        True if the password matches.
    """
    try:
        result: bool = bool(_hasher.verify(password_hash, password))
        return result
    except VerifyMismatchError:
        return False
