"""Environment-based configuration management.

Provides a dataclass-based configuration loader that reads from
environment variables with sensible defaults for local development.
"""

import os
from dataclasses import dataclass
from enum import StrEnum


class Environment(StrEnum):
    """Deployment environment identifier."""

    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass(frozen=True)
class InfraConfig:
    """Infrastructure connection configuration loaded from environment.

    All fields have sensible defaults for local development.
    In production, values are overridden via environment variables.
    """

    environment: Environment = Environment.LOCAL

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50
    redis_socket_timeout: float = 5.0

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "sona_memories"
    qdrant_vector_size: int = 384

    # Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_timeout: float = 120.0

    # OpenAI-compatible
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_timeout: float = 60.0

    # General
    log_level: str = "info"
    debug: bool = False

    @classmethod
    def from_env(cls) -> "InfraConfig":
        """Load configuration from environment variables.

        Each field maps to an uppercase environment variable name.
        Falls back to class defaults when variables are unset.
        """
        return cls(
            environment=Environment(os.getenv("ENVIRONMENT", "local")),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            redis_max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
            redis_socket_timeout=float(os.getenv("REDIS_SOCKET_TIMEOUT", "5.0")),
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            qdrant_collection=os.getenv("QDRANT_COLLECTION", "sona_memories"),
            qdrant_vector_size=int(os.getenv("QDRANT_VECTOR_SIZE", "384")),
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            ollama_timeout=float(os.getenv("OLLAMA_TIMEOUT", "120.0")),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            openai_timeout=float(os.getenv("OPENAI_TIMEOUT", "60.0")),
            log_level=os.getenv("LOG_LEVEL", "info"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )
