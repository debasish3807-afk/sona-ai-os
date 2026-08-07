"""Tests for the environment-based configuration manager."""

import os
from unittest.mock import patch

from sona_shared.config.env import Environment, InfraConfig


class TestEnvironmentEnum:
    """Tests for the Environment enum."""

    def test_all_values(self) -> None:
        assert Environment.LOCAL == "local"
        assert Environment.DEVELOPMENT == "development"
        assert Environment.STAGING == "staging"
        assert Environment.PRODUCTION == "production"

    def test_from_string(self) -> None:
        assert Environment("local") == Environment.LOCAL
        assert Environment("production") == Environment.PRODUCTION


class TestInfraConfig:
    """Tests for InfraConfig dataclass."""

    def test_defaults(self) -> None:
        config = InfraConfig()
        assert config.environment == Environment.LOCAL
        assert config.redis_url == "redis://localhost:6379/0"
        assert config.redis_max_connections == 50
        assert config.redis_socket_timeout == 5.0
        assert config.qdrant_url == "http://localhost:6333"
        assert config.qdrant_collection == "sona_memories"
        assert config.qdrant_vector_size == 384
        assert config.ollama_url == "http://localhost:11434"
        assert config.ollama_timeout == 120.0
        assert config.openai_api_key == ""
        assert config.openai_base_url == "https://api.openai.com/v1"
        assert config.openai_timeout == 60.0
        assert config.log_level == "info"
        assert config.debug is False

    def test_from_env_defaults(self) -> None:
        """from_env returns defaults when no env vars set."""
        with patch.dict(os.environ, {}, clear=True):
            config = InfraConfig.from_env()
        assert config.environment == Environment.LOCAL
        assert config.redis_url == "redis://localhost:6379/0"
        assert config.debug is False

    def test_from_env_custom_values(self) -> None:
        """from_env reads custom values from environment."""
        env = {
            "ENVIRONMENT": "production",
            "REDIS_URL": "redis://prod-redis:6379/1",
            "REDIS_MAX_CONNECTIONS": "100",
            "REDIS_SOCKET_TIMEOUT": "10.0",
            "QDRANT_URL": "http://qdrant-prod:6333",
            "QDRANT_COLLECTION": "prod_memories",
            "QDRANT_VECTOR_SIZE": "768",
            "OLLAMA_URL": "http://gpu-server:11434",
            "OLLAMA_TIMEOUT": "300.0",
            "OPENAI_API_KEY": "sk-test-key",
            "OPENAI_BASE_URL": "https://custom.api.com/v1",
            "OPENAI_TIMEOUT": "90.0",
            "LOG_LEVEL": "debug",
            "DEBUG": "true",
        }
        with patch.dict(os.environ, env, clear=True):
            config = InfraConfig.from_env()

        assert config.environment == Environment.PRODUCTION
        assert config.redis_url == "redis://prod-redis:6379/1"
        assert config.redis_max_connections == 100
        assert config.redis_socket_timeout == 10.0
        assert config.qdrant_url == "http://qdrant-prod:6333"
        assert config.qdrant_collection == "prod_memories"
        assert config.qdrant_vector_size == 768
        assert config.ollama_url == "http://gpu-server:11434"
        assert config.ollama_timeout == 300.0
        assert config.openai_api_key == "sk-test-key"
        assert config.openai_base_url == "https://custom.api.com/v1"
        assert config.openai_timeout == 90.0
        assert config.log_level == "debug"
        assert config.debug is True

    def test_from_env_debug_false_variants(self) -> None:
        """DEBUG must be 'true' (case-insensitive) to be True."""
        for val in ("false", "0", "no", ""):
            with patch.dict(os.environ, {"DEBUG": val}, clear=True):
                config = InfraConfig.from_env()
            assert config.debug is False

        with patch.dict(os.environ, {"DEBUG": "True"}, clear=True):
            config = InfraConfig.from_env()
        assert config.debug is True

    def test_frozen_dataclass(self) -> None:
        """InfraConfig is immutable (frozen)."""
        config = InfraConfig()
        import dataclasses

        with __import__("pytest").raises(dataclasses.FrozenInstanceError):
            config.redis_url = "redis://other:6379/0"  # type: ignore[misc]
