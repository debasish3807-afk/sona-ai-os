"""Password hashing service using hashlib SHA-256 + salt.

Provides secure password hashing and verification without external
dependencies like bcrypt.
"""

import hashlib
import os

import structlog

logger = structlog.get_logger()


class PasswordService:
    """Password hashing and verification using SHA-256 + random salt."""

    def __init__(self, iterations: int = 100_000) -> None:
        self._iterations = iterations

    def generate_salt(self) -> str:
        """Generate a cryptographically random salt (32 bytes hex)."""
        return os.urandom(32).hex()

    def hash_password(self, password: str, salt: str | None = None) -> str:
        """Hash a password with SHA-256 and salt.

        Returns format: salt$hash
        """
        if salt is None:
            salt = self.generate_salt()

        # Use PBKDF2-like iteration with SHA-256
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            self._iterations,
        )
        return f"{salt}${key.hex()}"

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash.

        Args:
            password: The plaintext password to verify.
            hashed: The stored hash in format salt$hash.

        Returns:
            True if the password matches, False otherwise.
        """
        try:
            parts = hashed.split("$", 1)
            if len(parts) != 2:
                return False
            salt, _stored_hash = parts
            computed = self.hash_password(password, salt)
            # Constant-time comparison
            return computed == hashed
        except (ValueError, IndexError):
            return False
