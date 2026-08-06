"""Tests for the shared configuration schemas."""

import pytest
from pydantic import ValidationError

from sona_shared.config import (
    DatabaseConfig,
    Environment,
    LLMProviderConfig,
    RedisConfig,
    ServiceConfig,
    VectorDBConfig,
)


class TestEnvironment:
    """Tests for the Environment enum."""

    def test_all_environments_defined(self):
        assert Environment.LOCAL == "local"
        assert Environment.DEVELOPMENT == "development"
        assert Environment.STAGING == "staging"
        assert Environment.PRODUCTION == "production"

    def test_enum_values(self):
        assert len(Environment) == 4


class TestDatabaseConfig:
    """Tests for DatabaseConfig model."""

    def test_defaults(self):
        cfg = DatabaseConfig(password="secret")
        assert cfg.host == "localhost"
        assert cfg.port == 5432
        assert cfg.name == "sona_db"
        assert cfg.user == "sona"
        assert cfg.pool_size == 20
        assert cfg.pool_overflow == 10
        assert cfg.ssl_mode == "prefer"

    def test_password_excluded_from_serialization(self):
        cfg = DatabaseConfig(password="secret")
        data = cfg.model_dump()
        assert "password" not in data

    def test_port_validation_min(self):
        with pytest.raises(ValidationError):
            DatabaseConfig(password="secret", port=0)

    def test_port_validation_max(self):
        with pytest.raises(ValidationError):
            DatabaseConfig(password="secret", port=70000)

    def test_pool_size_must_be_positive(self):
        with pytest.raises(ValidationError):
            DatabaseConfig(password="secret", pool_size=0)

    def test_custom_values(self):
        cfg = DatabaseConfig(
            host="db.prod.internal",
            port=5433,
            name="sona_prod",
            user="admin",
            password="prodpass",
            pool_size=50,
            pool_overflow=20,
            ssl_mode="require",
        )
        assert cfg.host == "db.prod.internal"
        assert cfg.port == 5433
        assert cfg.name == "sona_prod"


class TestRedisConfig:
    """Tests for RedisConfig model."""

    def test_defaults(self):
        cfg = RedisConfig()
        assert cfg.url == "redis://localhost:6379/0"
        assert cfg.max_connections == 50
        assert cfg.decode_responses is True
        assert cfg.socket_timeout == 5.0

    def test_custom_url(self):
        cfg = RedisConfig(url="redis://redis-cluster:6380/1")
        assert cfg.url == "redis://redis-cluster:6380/1"


class TestVectorDBConfig:
    """Tests for VectorDBConfig model."""

    def test_defaults(self):
        cfg = VectorDBConfig()
        assert cfg.url == "http://localhost:6333"
        assert cfg.collection_prefix == "sona_"
        assert cfg.embedding_dimension == 1536
        assert cfg.distance_metric == "cosine"

    def test_custom_values(self):
        cfg = VectorDBConfig(
            url="http://qdrant:6333",
            collection_prefix="prod_",
            embedding_dimension=768,
            distance_metric="euclid",
        )
        assert cfg.embedding_dimension == 768
        assert cfg.distance_metric == "euclid"


class TestLLMProviderConfig:
    """Tests for LLMProviderConfig model."""

    def test_required_fields(self):
        cfg = LLMProviderConfig(
            provider="openai",
            api_key="sk-test123",
            model_id="gpt-4o",
        )
        assert cfg.provider == "openai"
        assert cfg.model_id == "gpt-4o"
        assert cfg.max_tokens == 4096
        assert cfg.timeout_seconds == 60
        assert cfg.retry_count == 3

    def test_api_key_excluded_from_serialization(self):
        cfg = LLMProviderConfig(
            provider="openai",
            api_key="sk-test123",
            model_id="gpt-4o",
        )
        data = cfg.model_dump()
        assert "api_key" not in data

    def test_optional_base_url(self):
        cfg = LLMProviderConfig(
            provider="ollama",
            api_key="none",
            model_id="llama3",
            base_url="http://localhost:11434",
        )
        assert cfg.base_url == "http://localhost:11434"


class TestServiceConfig:
    """Tests for the root ServiceConfig model."""

    def test_minimal_config(self):
        cfg = ServiceConfig(service_name="ai-kernel")
        assert cfg.service_name == "ai-kernel"
        assert cfg.environment == Environment.LOCAL
        assert cfg.debug is False
        assert cfg.host == "0.0.0.0"
        assert cfg.port == 8000
        assert cfg.database is None
        assert cfg.redis is None
        assert cfg.vector_db is None
        assert cfg.llm_providers == []
        assert cfg.log_level == "info"
        assert cfg.cors_origins == ["http://localhost:3000"]

    def test_full_config(self):
        cfg = ServiceConfig(
            service_name="brain-os",
            environment=Environment.PRODUCTION,
            debug=False,
            port=8001,
            database=DatabaseConfig(password="dbpass"),
            redis=RedisConfig(url="redis://prod:6379/0"),
            vector_db=VectorDBConfig(url="http://qdrant:6333"),
            llm_providers=[
                LLMProviderConfig(
                    provider="openai",
                    api_key="sk-xxx",
                    model_id="gpt-4o",
                )
            ],
            log_level="warning",
            cors_origins=["https://sona.ai"],
        )
        assert cfg.environment == Environment.PRODUCTION
        assert cfg.database is not None
        assert cfg.database.host == "localhost"
        assert len(cfg.llm_providers) == 1

    def test_log_level_validation_invalid(self):
        with pytest.raises(ValidationError):
            ServiceConfig(service_name="test", log_level="verbose")

    def test_log_level_normalized_to_lower(self):
        cfg = ServiceConfig(service_name="test", log_level="WARNING")
        assert cfg.log_level == "warning"

    def test_port_validation(self):
        with pytest.raises(ValidationError):
            ServiceConfig(service_name="test", port=0)
        with pytest.raises(ValidationError):
            ServiceConfig(service_name="test", port=70000)
