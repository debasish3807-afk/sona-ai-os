"""Tests for the password service."""

from sona_security.infrastructure.password_service import PasswordService


class TestPasswordService:
    def setup_method(self) -> None:
        self.svc = PasswordService(iterations=1000)  # Faster for tests

    def test_generate_salt(self) -> None:
        salt = self.svc.generate_salt()
        assert len(salt) == 64  # 32 bytes hex
        assert all(c in "0123456789abcdef" for c in salt)

    def test_generate_salt_unique(self) -> None:
        salts = {self.svc.generate_salt() for _ in range(10)}
        assert len(salts) == 10  # All unique

    def test_hash_password(self) -> None:
        hashed = self.svc.hash_password("password123")
        assert "$" in hashed
        parts = hashed.split("$")
        assert len(parts) == 2
        assert len(parts[0]) == 64  # salt
        assert len(parts[1]) == 64  # hash

    def test_hash_with_explicit_salt(self) -> None:
        salt = "a" * 64
        hashed = self.svc.hash_password("test", salt=salt)
        assert hashed.startswith(salt + "$")

    def test_same_password_different_salts(self) -> None:
        h1 = self.svc.hash_password("password")
        h2 = self.svc.hash_password("password")
        assert h1 != h2  # Different salts

    def test_verify_correct_password(self) -> None:
        hashed = self.svc.hash_password("secure123")
        assert self.svc.verify_password("secure123", hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = self.svc.hash_password("secure123")
        assert self.svc.verify_password("wrong", hashed) is False

    def test_verify_empty_password(self) -> None:
        hashed = self.svc.hash_password("")
        assert self.svc.verify_password("", hashed) is True
        assert self.svc.verify_password("notempty", hashed) is False

    def test_verify_invalid_hash_format(self) -> None:
        assert self.svc.verify_password("pass", "nodoIlarsign") is False
        assert self.svc.verify_password("pass", "") is False

    def test_deterministic_with_same_salt(self) -> None:
        salt = self.svc.generate_salt()
        h1 = self.svc.hash_password("password", salt=salt)
        h2 = self.svc.hash_password("password", salt=salt)
        assert h1 == h2

    def test_different_passwords_different_hashes(self) -> None:
        salt = self.svc.generate_salt()
        h1 = self.svc.hash_password("pass1", salt=salt)
        h2 = self.svc.hash_password("pass2", salt=salt)
        assert h1 != h2

    def test_unicode_password(self) -> None:
        hashed = self.svc.hash_password("pässwörd🔑")
        assert self.svc.verify_password("pässwörd🔑", hashed) is True
        assert self.svc.verify_password("password", hashed) is False

    def test_long_password(self) -> None:
        long_pass = "a" * 1000
        hashed = self.svc.hash_password(long_pass)
        assert self.svc.verify_password(long_pass, hashed) is True
