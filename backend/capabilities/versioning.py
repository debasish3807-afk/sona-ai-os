"""Version Manager — semantic versioning utilities for capabilities."""

from __future__ import annotations


class VersionManager:
    """Provides semantic versioning utilities for capability management.

    Supports parsing, comparison, and compatibility checking
    using caret (^) semver semantics.
    """

    def parse(self, version_str: str) -> tuple[int, int, int]:
        """Parse a semantic version string into components.

        Args:
            version_str: Version string in 'major.minor.patch' format.

        Returns:
            Tuple of (major, minor, patch).

        Raises:
            ValueError: If the version string is invalid.
        """
        parts = version_str.strip().split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: '{version_str}'")
        return (int(parts[0]), int(parts[1]), int(parts[2]))

    def is_compatible(self, required: str, available: str) -> bool:
        """Check if available version satisfies caret requirement.

        Caret semantics: ^1.2.3 means >=1.2.3 and <2.0.0
        For major=0: ^0.2.3 means >=0.2.3 and <0.3.0

        Args:
            required: The required version (minimum).
            available: The available version to check.

        Returns:
            True if available satisfies the requirement.
        """
        req = self.parse(required)
        avail = self.parse(available)

        if req[0] != avail[0]:
            return False
        if req[0] == 0:
            if req[1] != avail[1]:
                return False
            return avail[2] >= req[2]
        return avail >= req

    def compare(self, a: str, b: str) -> int:
        """Compare two version strings.

        Returns:
            -1 if a < b, 0 if a == b, 1 if a > b.
        """
        va = self.parse(a)
        vb = self.parse(b)
        if va < vb:
            return -1
        if va > vb:
            return 1
        return 0

    def latest(self, versions: list[str]) -> str:
        """Find the latest version from a list.

        Args:
            versions: List of version strings.

        Returns:
            The latest (highest) version string.

        Raises:
            ValueError: If the list is empty.
        """
        if not versions:
            raise ValueError("Cannot determine latest from empty list")
        return max(versions, key=lambda v: self.parse(v))
