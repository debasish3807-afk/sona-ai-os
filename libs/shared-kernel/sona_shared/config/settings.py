"""Service configuration schemas for Sona AI OS.

Provides Pydantic-based configuration models for all backend services,
covering database, caching, vector DB, LLM providers, and service-level settings.
"""

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class Environment(StrEnum):
    """Deployment environment identifier."""

    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseConfig(BaseModel):  # type: ignore[misc]
    """PostgreSQL database connection configuration."""

    host: str = "localhost"
    port: int = Field(default=5432, ge=1, le=65535)
    name: str = "sona_db"
    user: str = "sona"
    password: str = Field(exclude=True)
    pool_size: int = Field(default=20, gt=0)
    pool_overflow: int = 10
    ssl_mode: str = "prefer"


class RedisConfig(BaseModel):  # type: ignore[misc]
    """Redis connection configuration."""

    url: str = "redis://localhost:6379/0"
    max_connections: int = 50
    decode_responses: bool = True
    socket_timeout: float = 5.0


class VectorDBConfig(BaseModel):  # type: ignore[misc]
    """Qdrant vector database configuration."""

    url: str = "http://localhost:6333"
    collection_prefix: str = "sona_"
    embedding_dimension: int = 1536
    distance_metric: str = "cosine"


class LLMProviderConfig(BaseModel):  # type: ignore[misc]
    """LLM provider connection configuration."""

    provider: str
    api_key: str = Field(exclude=True)
    base_url: str | None = None
    model_id: str
    max_tokens: int = 4096
    timeout_seconds: int = 60
    retry_count: int = 3


class ServiceConfig(BaseModel):  # type: ignore[misc]
    """Root service configuration aggregating all subsystem configs."""

    service_name: str
    environment: Environment = Environment.LOCAL
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    database: DatabaseConfig | None = None
    redis: RedisConfig | None = None
    vector_db: VectorDBConfig | None = None
    llm_providers: list[LLMProviderConfig] = []
    log_level: str = "info"
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("log_level")  # type: ignore[untyped-decorator]
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is a recognized value."""
        allowed = {"debug", "info", "warning", "error", "critical"}
        if v.lower() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got '{v}'")
        return v.lower()
