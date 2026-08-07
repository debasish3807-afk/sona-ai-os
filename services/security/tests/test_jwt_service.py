"""Tests for the JWT service."""

from sona_security.infrastructure.jwt_service import JWTConfig, JWTService


class TestJWTService:
    def setup_method(self) -> None:
        self.config = JWTConfig(secret="test-secret-key")
        self.jwt = JWTService(config=self.config)

    def test_generate_access_token(self) -> None:
        token = self.jwt.generate_access_token("user-1", ["user"])
        assert token
        assert token.count(".") == 2

    def test_generate_refresh_token(self) -> None:
        token = self.jwt.generate_refresh_token("user-1", ["user"])
        assert token
        assert token.count(".") == 2

    def test_validate_valid_token(self) -> None:
        token = self.jwt.generate_access_token("user-1", ["admin", "user"])
        claims = self.jwt.validate_token(token)
        assert claims is not None
        assert claims["sub"] == "user-1"
        assert claims["roles"] == ["admin", "user"]
        assert claims["type"] == "access"

    def test_validate_refresh_token(self) -> None:
        token = self.jwt.generate_refresh_token("user-2", ["service"])
        claims = self.jwt.validate_token(token)
        assert claims is not None
        assert claims["sub"] == "user-2"
        assert claims["type"] == "refresh"

    def test_validate_invalid_signature(self) -> None:
        token = self.jwt.generate_access_token("user-1", ["user"])
        # Tamper with the token
        parts = token.split(".")
        parts[2] = "invalid_signature"
        tampered = ".".join(parts)
        assert self.jwt.validate_token(tampered) is None

    def test_validate_expired_token(self) -> None:
        config = JWTConfig(secret="test-secret", access_token_expiry_seconds=-1)
        jwt = JWTService(config=config)
        token = jwt.generate_access_token("user-1", ["user"])
        assert jwt.validate_token(token) is None

    def test_validate_malformed_token(self) -> None:
        assert self.jwt.validate_token("not.a.valid.token") is None
        assert self.jwt.validate_token("") is None
        assert self.jwt.validate_token("noperiods") is None

    def test_decode_token(self) -> None:
        token = self.jwt.generate_access_token("user-1", ["user"])
        claims = self.jwt.decode_token(token)
        assert claims is not None
        assert claims["sub"] == "user-1"

    def test_decode_malformed_token(self) -> None:
        assert self.jwt.decode_token("bad") is None
        assert self.jwt.decode_token("") is None

    def test_revoke_token(self) -> None:
        token = self.jwt.generate_access_token("user-1", ["user"])
        assert self.jwt.validate_token(token) is not None
        self.jwt.revoke_token(token)
        assert self.jwt.validate_token(token) is None

    def test_is_revoked(self) -> None:
        token = self.jwt.generate_access_token("user-1", ["user"])
        assert self.jwt.is_revoked(token) is False
        self.jwt.revoke_token(token)
        assert self.jwt.is_revoked(token) is True

    def test_token_contains_iat(self) -> None:
        token = self.jwt.generate_access_token("user-1", ["user"])
        claims = self.jwt.decode_token(token)
        assert claims is not None
        assert "iat" in claims
        assert isinstance(claims["iat"], int)

    def test_token_contains_exp(self) -> None:
        token = self.jwt.generate_access_token("user-1", ["user"])
        claims = self.jwt.decode_token(token)
        assert claims is not None
        assert "exp" in claims
        iat = claims["iat"]
        exp = claims["exp"]
        assert isinstance(iat, int)
        assert isinstance(exp, int)
        assert exp - iat == 900  # 15 minutes

    def test_refresh_token_expiry(self) -> None:
        token = self.jwt.generate_refresh_token("user-1", ["user"])
        claims = self.jwt.decode_token(token)
        assert claims is not None
        iat = claims["iat"]
        exp = claims["exp"]
        assert isinstance(iat, int)
        assert isinstance(exp, int)
        assert exp - iat == 604800  # 7 days

    def test_token_contains_issuer(self) -> None:
        token = self.jwt.generate_access_token("user-1", ["user"])
        claims = self.jwt.decode_token(token)
        assert claims is not None
        assert claims["iss"] == "sona-security"

    def test_extra_claims(self) -> None:
        token = self.jwt.generate_access_token("user-1", ["user"], extra_claims={"org": "test-org"})
        claims = self.jwt.decode_token(token)
        assert claims is not None
        assert claims["org"] == "test-org"

    def test_different_secrets_fail_validation(self) -> None:
        jwt2 = JWTService(config=JWTConfig(secret="different-secret"))
        token = self.jwt.generate_access_token("user-1", ["user"])
        assert jwt2.validate_token(token) is None

    def test_default_config(self) -> None:
        jwt = JWTService()
        token = jwt.generate_access_token("user-1", ["user"])
        assert jwt.validate_token(token) is not None
