# Design Document: Sona AI OS — Production-Grade Monorepo Restructuring

## Overview

Sona AI OS is a next-generation personal AI operating system that combines multi-model intelligence, long-term memory, multi-agent orchestration, automation, research, coding assistance, voice, vision, and secure integrations into a unified platform. The project currently has a substantial Python backend (383+ modules, 32 packages, 1915 tests), a prototype React 19 web frontend, a Kotlin Android skeleton, and basic Docker/CI infrastructure.

This design defines the production-grade monorepo restructuring that transforms the existing codebase into a modular, scalable, and maintainable architecture following Clean Architecture and Domain-Driven Design principles. The first milestone focuses exclusively on scaffolding, interfaces, configuration, and infrastructure — no AI logic implementation.

The restructuring preserves all existing functionality while introducing clear module boundaries, shared libraries, comprehensive Docker orchestration, expanded CI/CD pipelines, and proper dependency management across Python, TypeScript, and Kotlin workspaces.


## Architecture

### System Context Diagram

```mermaid
graph TD
    subgraph Users
        WebUser[Web User]
        MobileUser[Android User]
        APIClient[API Client]
    end

    subgraph "Sona AI OS Monorepo"
        Gateway[API Gateway / Nginx]
        WebApp[Web Dashboard<br/>React + TypeScript]
        Backend[Backend Services<br/>FastAPI + Python 3.12]
        Android[Android App<br/>Kotlin + Jetpack Compose]
    end

    subgraph "Infrastructure"
        PG[(PostgreSQL 16)]
        Redis[(Redis 7)]
        Qdrant[(Qdrant Vector DB)]
        Ollama[Ollama LLM Server]
    end

    subgraph "External Providers"
        OpenAI[OpenAI API]
        Anthropic[Anthropic API]
        Google[Google AI API]
    end

    WebUser --> WebApp
    MobileUser --> Android
    APIClient --> Gateway
    WebApp --> Gateway
    Android --> Gateway
    Gateway --> Backend
    Backend --> PG
    Backend --> Redis
    Backend --> Qdrant
    Backend --> Ollama
    Backend --> OpenAI
    Backend --> Anthropic
    Backend --> Google
```


### Internal Module Architecture

```mermaid
graph TD
    subgraph "API Layer"
        API[api/]
        Auth[security/]
    end

    subgraph "Orchestration Layer"
        Brain[brain-os/]
        Thalamus[thalamus-router/]
        Workflow[workflow-engine/]
    end

    subgraph "Intelligence Layer"
        Kernel[ai-kernel/]
        Memory[memory-os/]
        Knowledge[knowledge-os/]
        Research[research-os/]
        Engineering[ai-engineering-os/]
    end

    subgraph "Agent Layer"
        Workforce[workforce-os/]
        MCP[mcp-integration/]
        Plugins[plugin-system/]
    end

    subgraph "Cross-Cutting"
        Eval[evaluation-os/]
        Observe[observability/]
        Shared[shared-kernel/]
    end

    API --> Thalamus
    Thalamus --> Brain
    Brain --> Kernel
    Brain --> Workforce
    Brain --> Workflow
    Kernel --> Memory
    Kernel --> Knowledge
    Workforce --> MCP
    Workforce --> Research
    Workforce --> Engineering
    Workflow --> Workforce
    Knowledge --> Qdrant2[(Vector DB)]
    Memory --> Redis2[(Cache)]
    Observe --> API
    Observe --> Brain
    Eval --> Kernel
    Plugins --> MCP
    Auth --> API
    Shared --> Kernel
    Shared --> Memory
    Shared --> Brain
```


## Monorepo Directory Structure

The restructured monorepo follows a workspace-based layout with clear boundaries between services, shared libraries, infrastructure, and client applications.

```
sona-ai-os/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Unified CI pipeline (lint, test, build)
│       ├── ci-backend.yml            # Backend-specific CI
│       ├── ci-frontend.yml           # Frontend-specific CI
│       ├── ci-android.yml            # Android-specific CI
│       ├── deploy-dev.yml            # Dev environment deployment
│       ├── deploy-staging.yml        # Staging deployment
│       └── deploy-prod.yml           # Production deployment
├── services/
│   ├── ai-kernel/                    # Central intelligence engine
│   │   ├── domain/                   # Domain models, entities, value objects
│   │   ├── application/              # Use cases, ports (interfaces)
│   │   ├── infrastructure/           # Adapters, external integrations
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── thalamus-router/              # Request routing & orchestration
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── brain-os/                     # AI Brain orchestrator
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── memory-os/                    # Memory management system
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── knowledge-os/                 # RAG pipeline & knowledge bases
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── workforce-os/                 # Multi-agent system
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── workflow-engine/              # Task automation & workflows
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── mcp-integration/             # Model Context Protocol
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── research-os/                  # Web research & analysis
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── ai-engineering-os/            # Code generation & review
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── evaluation-os/               # Testing & quality evaluation
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── security/                     # Auth, RBAC, encryption
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── observability/                # Metrics, logging, tracing
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── plugin-system/               # Extensibility framework
│       ├── domain/
│       ├── application/
│       ├── infrastructure/
│       ├── tests/
│       └── pyproject.toml
├── libs/
│   ├── shared-kernel/               # Shared domain primitives
│   │   ├── sona_shared/
│   │   │   ├── domain/              # Base entities, value objects, events
│   │   │   ├── ports/               # Common interfaces/protocols
│   │   │   ├── config/              # Shared configuration schemas
│   │   │   └── utils/               # Shared utilities
│   │   ├── tests/
│   │   └── pyproject.toml
│   ├── llm-client/                  # Unified LLM provider client
│   │   ├── sona_llm/
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── event-bus/                   # Internal event/message bus
│       ├── sona_events/
│       ├── tests/
│       └── pyproject.toml
├── gateway/
│   ├── app/                          # FastAPI gateway application
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── middleware/
│   │   └── deps.py
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── apps/
│   ├── web/                          # React + TypeScript dashboard
│   │   ├── src/
│   │   │   ├── app/                  # App shell, routing, providers
│   │   │   ├── features/            # Feature modules
│   │   │   ├── shared/              # Shared components, hooks, utils
│   │   │   └── infrastructure/      # API clients, state management
│   │   ├── public/
│   │   ├── tests/
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── tsconfig.json
│   │   └── Dockerfile
│   └── android/                      # Kotlin + Jetpack Compose app
│       ├── app/
│       │   └── src/main/
│       ├── core/
│       │   ├── domain/
│       │   ├── data/
│       │   └── di/
│       ├── features/
│       │   ├── chat/
│       │   ├── settings/
│       │   └── voice/
│       ├── build.gradle.kts
│       ├── settings.gradle.kts
│       └── gradle.properties
├── infra/
│   ├── docker/
│   │   ├── Dockerfile.gateway
│   │   ├── Dockerfile.service       # Multi-stage service Dockerfile
│   │   ├── Dockerfile.web
│   │   └── Dockerfile.nginx
│   ├── compose/
│   │   ├── docker-compose.yml       # Full stack orchestration
│   │   ├── docker-compose.dev.yml   # Development overrides
│   │   ├── docker-compose.test.yml  # Testing configuration
│   │   └── docker-compose.prod.yml  # Production configuration
│   ├── nginx/
│   │   ├── nginx.conf
│   │   └── conf.d/
│   ├── k8s/                          # Kubernetes manifests (future)
│   │   ├── base/
│   │   └── overlays/
│   └── scripts/
│       ├── setup-dev.sh
│       ├── migrate-db.sh
│       └── seed-data.sh
├── docs/
│   ├── architecture/
│   │   ├── README.md
│   │   ├── system-overview.md
│   │   ├── module-boundaries.md
│   │   └── data-flow.md
│   ├── development/
│   │   ├── getting-started.md
│   │   ├── contributing.md
│   │   ├── coding-standards.md
│   │   └── testing-guide.md
│   ├── api/
│   │   ├── gateway.md
│   │   └── internal-services.md
│   └── deployment/
│       ├── local.md
│       ├── staging.md
│       └── production.md
├── tools/
│   ├── scripts/                      # Developer utility scripts
│   └── generators/                   # Code generators / templates
├── pyproject.toml                    # Root workspace configuration
├── docker-compose.yml                # Quick-start compose (symlink/alias)
├── Makefile                          # Common development commands
└── README.md
```


## Sequence Diagrams

### Request Flow: User Chat Interaction

```mermaid
sequenceDiagram
    participant U as User (Web/Android)
    participant GW as API Gateway
    participant TH as Thalamus Router
    participant BR as Brain OS
    participant KR as AI Kernel
    participant MEM as Memory OS
    participant WF as Workforce OS
    participant LLM as LLM Provider

    U->>GW: POST /api/v1/chat
    GW->>GW: Authenticate & rate-limit
    GW->>TH: Route request
    TH->>TH: Classify intent
    TH->>BR: Dispatch to Brain OS
    BR->>MEM: Retrieve context (history, preferences)
    MEM-->>BR: Context payload
    BR->>KR: Assemble prompt + select model
    KR->>WF: Delegate to agent (if multi-step)
    WF->>LLM: Execute LLM call
    LLM-->>WF: Response tokens
    WF-->>KR: Agent result
    KR-->>BR: Processed response
    BR->>MEM: Store interaction
    BR-->>TH: Final response
    TH-->>GW: Response envelope
    GW-->>U: JSON response
```

### Request Flow: Knowledge Retrieval (RAG)

```mermaid
sequenceDiagram
    participant BR as Brain OS
    participant KN as Knowledge OS
    participant VDB as Qdrant (Vector DB)
    participant LLM as LLM Provider

    BR->>KN: Query knowledge base
    KN->>KN: Preprocess query (chunking, embedding)
    KN->>VDB: Similarity search (top-k)
    VDB-->>KN: Relevant documents
    KN->>KN: Re-rank & filter
    KN-->>BR: Augmented context
    BR->>LLM: Generate with context
    LLM-->>BR: Grounded response
```

### Service Startup Sequence

```mermaid
sequenceDiagram
    participant DC as Docker Compose
    participant PG as PostgreSQL
    participant RD as Redis
    participant QD as Qdrant
    participant GW as Gateway
    participant SVC as Backend Services

    DC->>PG: Start (healthcheck: pg_isready)
    DC->>RD: Start (healthcheck: redis-cli ping)
    DC->>QD: Start (healthcheck: HTTP 200)
    PG-->>DC: Healthy
    RD-->>DC: Healthy
    QD-->>DC: Healthy
    DC->>GW: Start gateway
    GW->>GW: Load config, connect to PG/Redis
    GW-->>DC: Healthy (HTTP 200 /health)
    DC->>SVC: Start service workers
    SVC->>PG: Verify connection
    SVC->>RD: Verify connection
    SVC-->>DC: All services healthy
```


## Components and Interfaces

### Component 1: Shared Kernel (`libs/shared-kernel/`)

**Purpose**: Provides domain primitives, base classes, value objects, and common interfaces shared across all services. Ensures consistency and reduces duplication.

**Interface**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4


# --- Value Objects ---

@dataclass(frozen=True)
class EntityId:
    """Immutable unique identifier for all domain entities."""
    value: UUID = field(default_factory=uuid4)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Timestamp:
    """Immutable timestamp value object."""
    value: datetime = field(default_factory=datetime.utcnow)


# --- Base Entity ---

@dataclass
class Entity:
    """Base class for all domain entities."""
    id: EntityId = field(default_factory=EntityId)
    created_at: Timestamp = field(default_factory=Timestamp)
    updated_at: Timestamp = field(default_factory=Timestamp)


# --- Domain Events ---

@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""
    event_id: EntityId = field(default_factory=EntityId)
    occurred_at: Timestamp = field(default_factory=Timestamp)
    aggregate_id: EntityId | None = None


# --- Result Pattern ---

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Encapsulates success/failure without exceptions."""
    _value: T | None = None
    _error: E | None = None

    @classmethod
    def ok(cls, value: T) -> "Result[T, E]":
        return cls(_value=value)

    @classmethod
    def fail(cls, error: E) -> "Result[T, E]":
        return cls(_error=error)

    @property
    def is_success(self) -> bool:
        return self._error is None

    @property
    def value(self) -> T:
        if self._error is not None:
            raise ValueError("Cannot access value of failed Result")
        return self._value  # type: ignore

    @property
    def error(self) -> E:
        if self._error is None:
            raise ValueError("Cannot access error of successful Result")
        return self._error
```

**Responsibilities**:
- Define base `Entity`, `ValueObject`, `AggregateRoot` classes
- Provide the `Result[T, E]` pattern for error handling without exceptions
- Define `DomainEvent` base for event-driven communication
- Provide common ports: `Repository`, `EventPublisher`, `UnitOfWork`
- Configuration schema base classes


### Component 2: AI Kernel (`services/ai-kernel/`)

**Purpose**: Central intelligence engine that manages reasoning chains, model selection, context assembly, and response generation. Acts as the "CPU" of the AI OS.

**Interface**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import AsyncIterator


class ReasoningStrategy(StrEnum):
    DIRECT = "direct"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHT = "tree_of_thought"
    REFLECTION = "reflection"


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model_id: str
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0


@dataclass(frozen=True)
class KernelRequest:
    session_id: str
    user_id: str
    content: str
    context: dict[str, any] | None = None
    model_override: ModelConfig | None = None
    strategy: ReasoningStrategy = ReasoningStrategy.DIRECT


@dataclass(frozen=True)
class KernelResponse:
    content: str
    model_used: str
    tokens_input: int
    tokens_output: int
    latency_ms: float
    reasoning_trace: list[str] | None = None


class AIKernelPort(ABC):
    """Primary port for the AI Kernel service."""

    @abstractmethod
    async def process(self, request: KernelRequest) -> KernelResponse:
        """Process a single request through the kernel pipeline."""
        ...

    @abstractmethod
    async def stream(self, request: KernelRequest) -> AsyncIterator[str]:
        """Stream response tokens."""
        ...

    @abstractmethod
    async def select_model(self, request: KernelRequest) -> ModelConfig:
        """Select optimal model based on request characteristics."""
        ...


class ReasoningEnginePort(ABC):
    """Port for pluggable reasoning strategies."""

    @abstractmethod
    async def reason(
        self, prompt: str, context: dict, strategy: ReasoningStrategy
    ) -> list[str]:
        """Execute reasoning chain and return trace."""
        ...


class ModelRouterPort(ABC):
    """Port for model selection and routing."""

    @abstractmethod
    async def route(self, request: KernelRequest) -> ModelConfig:
        """Determine best model for the request."""
        ...

    @abstractmethod
    async def list_available(self) -> list[ModelConfig]:
        """List all available models across providers."""
        ...
```

**Responsibilities**:
- Intent recognition and classification
- Reasoning chain management (CoT, ToT, reflection)
- Context assembly with token budgeting
- Model selection and routing across providers
- Response generation and quality validation


### Component 3: Thalamus Router (`services/thalamus-router/`)

**Purpose**: Named after the brain's thalamus (relay center), this service routes incoming requests to the appropriate downstream services based on intent classification, priority, and system load.

**Interface**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class RequestPriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


class IntentCategory(StrEnum):
    CHAT = "chat"
    RESEARCH = "research"
    CODE = "code"
    AUTOMATION = "automation"
    MEMORY = "memory"
    SYSTEM = "system"


@dataclass(frozen=True)
class RoutingDecision:
    target_service: str
    intent: IntentCategory
    priority: RequestPriority
    requires_agents: list[str]
    estimated_latency_ms: int
    fallback_service: str | None = None


class ThalamusRouterPort(ABC):
    """Primary port for the Thalamus Router."""

    @abstractmethod
    async def classify_intent(self, content: str, context: dict) -> IntentCategory:
        """Classify the intent of incoming content."""
        ...

    @abstractmethod
    async def route(self, request: dict) -> RoutingDecision:
        """Determine routing for a request."""
        ...

    @abstractmethod
    async def health_check(self) -> dict[str, bool]:
        """Check health of all downstream services."""
        ...


class LoadBalancerPort(ABC):
    """Port for load-aware routing decisions."""

    @abstractmethod
    async def get_service_load(self, service_name: str) -> float:
        """Get current load factor (0.0 to 1.0) for a service."""
        ...

    @abstractmethod
    async def select_instance(self, service_name: str) -> str:
        """Select least-loaded instance of a service."""
        ...
```

**Responsibilities**:
- Intent classification and routing decisions
- Load-aware request distribution
- Circuit breaking and fallback management
- Request priority queueing
- Service discovery and health monitoring


### Component 4: Brain OS (`services/brain-os/`)

**Purpose**: The central orchestrator that connects all subsystems. It manages the full execution pipeline from request ingestion through memory retrieval, agent selection, model execution, and response delivery.

**Interface**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass(frozen=True)
class BrainRequest:
    session_id: str
    user_id: str
    messages: list[dict[str, str]]
    stream: bool = False
    metadata: dict | None = None


@dataclass(frozen=True)
class BrainResponse:
    content: str
    session_id: str
    model_used: str
    tokens: dict[str, int]
    latency_ms: float
    agent_used: str | None = None
    memory_updated: bool = False


class BrainOrchestratorPort(ABC):
    """Primary port for the Brain OS orchestrator."""

    @abstractmethod
    async def execute(self, request: BrainRequest) -> BrainResponse:
        """Execute the full brain pipeline for a request."""
        ...

    @abstractmethod
    async def execute_stream(self, request: BrainRequest) -> AsyncIterator[str]:
        """Stream the brain pipeline execution."""
        ...

    @abstractmethod
    async def get_session_context(self, session_id: str) -> dict:
        """Retrieve full context for a session."""
        ...


class PipelineStagePort(ABC):
    """Port for individual pipeline stages (composable)."""

    @abstractmethod
    async def execute(self, context: dict) -> dict:
        """Execute this pipeline stage, enriching context."""
        ...

    @abstractmethod
    def should_skip(self, context: dict) -> bool:
        """Determine if this stage should be skipped."""
        ...
```

**Responsibilities**:
- Full execution pipeline orchestration
- Memory retrieval and context injection
- Agent routing and delegation
- Response assembly and quality checks
- Session state management


### Component 5: Memory OS (`services/memory-os/`)

**Purpose**: Manages all forms of memory — working, short-term, long-term, episodic, and semantic. Provides retrieval, consolidation, and forgetting capabilities.

**Interface**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class MemoryType(StrEnum):
    WORKING = "working"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


@dataclass(frozen=True)
class MemoryEntry:
    id: str
    memory_type: MemoryType
    content: str
    embedding: list[float] | None = None
    metadata: dict | None = None
    importance: float = 0.5
    created_at: datetime | None = None
    expires_at: datetime | None = None
    tags: list[str] = ()


@dataclass(frozen=True)
class MemoryQuery:
    user_id: str
    query: str
    memory_types: list[MemoryType] | None = None
    top_k: int = 10
    min_importance: float = 0.0
    time_range: tuple[datetime, datetime] | None = None


class MemoryStorePort(ABC):
    """Port for memory storage operations."""

    @abstractmethod
    async def store(self, user_id: str, entry: MemoryEntry) -> str:
        """Store a memory entry, return ID."""
        ...

    @abstractmethod
    async def retrieve(self, query: MemoryQuery) -> list[MemoryEntry]:
        """Retrieve memories matching the query."""
        ...

    @abstractmethod
    async def consolidate(self, user_id: str) -> int:
        """Consolidate short-term memories into long-term. Returns count."""
        ...

    @abstractmethod
    async def forget(self, user_id: str, memory_id: str) -> bool:
        """Remove a specific memory."""
        ...

    @abstractmethod
    async def get_conversation_history(
        self, session_id: str, limit: int = 50
    ) -> list[MemoryEntry]:
        """Get recent conversation history for a session."""
        ...


class EmbeddingPort(ABC):
    """Port for generating embeddings for memory entries."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding vector for text."""
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        ...
```

**Responsibilities**:
- Multi-type memory storage and retrieval
- Embedding generation and vector similarity search
- Memory consolidation (short-term → long-term)
- Importance scoring and eviction policies
- Conversation history management with session isolation


### Component 6: Knowledge OS (`services/knowledge-os/`)

**Purpose**: Manages the RAG (Retrieval-Augmented Generation) pipeline, knowledge bases, document processing, indexing, and context augmentation for grounded responses.

**Interface**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class DocumentType(StrEnum):
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"
    CODE = "code"
    JSON = "json"


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    content: str
    doc_type: DocumentType
    metadata: dict | None = None
    source_url: str | None = None


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    document_id: str
    content: str
    embedding: list[float]
    chunk_index: int
    metadata: dict | None = None


@dataclass(frozen=True)
class RAGQuery:
    query: str
    knowledge_base_id: str | None = None
    top_k: int = 5
    min_similarity: float = 0.7
    rerank: bool = True


@dataclass(frozen=True)
class RAGResult:
    chunks: list[DocumentChunk]
    augmented_context: str
    sources: list[str]
    confidence: float


class KnowledgeBasePort(ABC):
    """Port for knowledge base management."""

    @abstractmethod
    async def ingest(self, document: Document, kb_id: str) -> str:
        """Ingest a document into a knowledge base."""
        ...

    @abstractmethod
    async def query(self, rag_query: RAGQuery) -> RAGResult:
        """Query knowledge base with RAG pipeline."""
        ...

    @abstractmethod
    async def list_knowledge_bases(self, user_id: str) -> list[dict]:
        """List available knowledge bases for a user."""
        ...

    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """Remove a document from the knowledge base."""
        ...


class DocumentProcessorPort(ABC):
    """Port for document processing and chunking."""

    @abstractmethod
    async def process(self, document: Document) -> list[DocumentChunk]:
        """Process document into indexed chunks."""
        ...

    @abstractmethod
    async def extract_text(self, raw_content: bytes, doc_type: DocumentType) -> str:
        """Extract text from raw document content."""
        ...
```

**Responsibilities**:
- Document ingestion, processing, and chunking
- Vector embedding and indexing in Qdrant
- RAG query pipeline with re-ranking
- Knowledge base CRUD operations
- Source attribution and confidence scoring


### Component 7: Workforce OS (`services/workforce-os/`)

**Purpose**: Multi-agent system providing specialized AI agents for different task domains. Manages agent lifecycle, inter-agent communication, and collaborative problem solving.

**Interface**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class AgentType(StrEnum):
    CODING = "coding"
    RESEARCH = "research"
    PLANNER = "planner"
    AUTOMATION = "automation"
    COMMUNICATION = "communication"
    SYSTEM = "system"
    VOICE = "voice"
    VISION = "vision"
    WEB = "web"
    ANDROID = "android"
    CUSTOM = "custom"


class AgentStatus(StrEnum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass(frozen=True)
class AgentTask:
    task_id: str
    agent_type: AgentType
    instruction: str
    context: dict | None = None
    timeout_seconds: int = 120
    priority: int = 5


@dataclass(frozen=True)
class AgentResult:
    task_id: str
    agent_type: AgentType
    output: str
    status: str
    tokens_used: int = 0
    duration_ms: float = 0.0
    artifacts: list[dict] | None = None


class AgentPort(ABC):
    """Port for individual agent implementation."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize agent resources."""
        ...

    @abstractmethod
    async def process(self, task: AgentTask) -> AgentResult:
        """Process an assigned task."""
        ...

    @abstractmethod
    async def get_capabilities(self) -> list[str]:
        """Return list of capabilities this agent provides."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check agent health."""
        ...


class AgentCoordinatorPort(ABC):
    """Port for agent coordination and dispatch."""

    @abstractmethod
    async def dispatch(self, task: AgentTask) -> AgentResult:
        """Dispatch task to the most suitable agent."""
        ...

    @abstractmethod
    async def dispatch_parallel(self, tasks: list[AgentTask]) -> list[AgentResult]:
        """Dispatch multiple tasks in parallel."""
        ...

    @abstractmethod
    async def register_agent(self, agent_type: AgentType, agent: AgentPort) -> None:
        """Register a new agent instance."""
        ...

    @abstractmethod
    async def list_agents(self) -> dict[AgentType, AgentStatus]:
        """List all agents and their current status."""
        ...
```

**Responsibilities**:
- Agent lifecycle management (init, start, stop, health)
- Task dispatch and routing to specialized agents
- Parallel and sequential multi-agent execution
- Inter-agent communication bus
- Agent capability discovery and registration


### Component 8: Workflow Engine (`services/workflow-engine/`)

**Purpose**: Task automation and workflow orchestration. Manages complex multi-step workflows with conditional branching, retries, and human-in-the-loop capabilities.

**Interface**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting_for_input"


@dataclass(frozen=True)
class WorkflowStep:
    step_id: str
    name: str
    action: str
    params: dict
    depends_on: list[str] = ()
    retry_count: int = 3
    timeout_seconds: int = 300
    condition: str | None = None


@dataclass(frozen=True)
class WorkflowDefinition:
    workflow_id: str
    name: str
    description: str
    steps: list[WorkflowStep]
    trigger: str | None = None
    schedule: str | None = None


@dataclass
class WorkflowExecution:
    execution_id: str
    workflow_id: str
    status: StepStatus
    current_step: str | None = None
    results: dict[str, any] = None
    started_at: str | None = None
    completed_at: str | None = None


class WorkflowEnginePort(ABC):
    """Port for workflow execution."""

    @abstractmethod
    async def create_workflow(self, definition: WorkflowDefinition) -> str:
        """Create a workflow definition. Returns workflow_id."""
        ...

    @abstractmethod
    async def execute(self, workflow_id: str, inputs: dict) -> str:
        """Start workflow execution. Returns execution_id."""
        ...

    @abstractmethod
    async def get_status(self, execution_id: str) -> WorkflowExecution:
        """Get current workflow execution status."""
        ...

    @abstractmethod
    async def cancel(self, execution_id: str) -> bool:
        """Cancel a running workflow."""
        ...

    @abstractmethod
    async def resume(self, execution_id: str, input_data: dict) -> bool:
        """Resume a workflow waiting for human input."""
        ...
```

**Responsibilities**:
- Workflow definition and persistence
- Step execution with dependency resolution
- Conditional branching and parallel execution
- Retry logic with exponential backoff
- Human-in-the-loop pause/resume
- Scheduled and event-triggered workflows


### Component 9: MCP Integration (`services/mcp-integration/`)

**Purpose**: Implements the Model Context Protocol for connecting to external tools, services, and resources through a standardized interface.

**Interface**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class MCPTransport(StrEnum):
    STDIO = "stdio"
    SSE = "sse"
    WEBSOCKET = "websocket"


class ToolPermission(StrEnum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


@dataclass(frozen=True)
class MCPTool:
    name: str
    description: str
    input_schema: dict
    permissions: list[ToolPermission]
    server_id: str


@dataclass(frozen=True)
class MCPServer:
    server_id: str
    name: str
    transport: MCPTransport
    command: str | None = None
    url: str | None = None
    tools: list[MCPTool] = ()


@dataclass(frozen=True)
class ToolCallResult:
    tool_name: str
    output: any
    success: bool
    error: str | None = None
    duration_ms: float = 0.0


class MCPManagerPort(ABC):
    """Port for MCP server management."""

    @abstractmethod
    async def register_server(self, server: MCPServer) -> str:
        """Register an MCP server."""
        ...

    @abstractmethod
    async def discover_tools(self, server_id: str) -> list[MCPTool]:
        """Discover available tools from a server."""
        ...

    @abstractmethod
    async def call_tool(
        self, tool_name: str, arguments: dict, user_id: str
    ) -> ToolCallResult:
        """Execute a tool call with permission checking."""
        ...

    @abstractmethod
    async def list_servers(self) -> list[MCPServer]:
        """List all registered MCP servers."""
        ...

    @abstractmethod
    async def health_check(self, server_id: str) -> bool:
        """Check if an MCP server is responding."""
        ...
```

**Responsibilities**:
- MCP server lifecycle management
- Tool discovery and capability negotiation
- Permission-gated tool execution
- Transport management (stdio, SSE, WebSocket)
- Sandboxed execution and audit logging


### Component 10: Security Layer (`services/security/`)

**Purpose**: Provides authentication, authorization (RBAC), encryption, API key management, and AI safety guardrails across the entire system.

**Interface**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    USER = "user"
    SERVICE = "service"
    READONLY = "readonly"


@dataclass(frozen=True)
class AuthToken:
    token: str
    user_id: str
    roles: list[Role]
    expires_at: str
    issued_at: str


@dataclass(frozen=True)
class Permission:
    resource: str
    action: str
    conditions: dict | None = None


class AuthenticationPort(ABC):
    """Port for authentication operations."""

    @abstractmethod
    async def authenticate(self, credentials: dict) -> AuthToken:
        """Authenticate user/service and return token."""
        ...

    @abstractmethod
    async def validate_token(self, token: str) -> AuthToken | None:
        """Validate and decode a token."""
        ...

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> AuthToken:
        """Refresh an expired token."""
        ...

    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """Revoke a token."""
        ...


class AuthorizationPort(ABC):
    """Port for RBAC authorization."""

    @abstractmethod
    async def check_permission(
        self, user_id: str, permission: Permission
    ) -> bool:
        """Check if user has the required permission."""
        ...

    @abstractmethod
    async def get_user_roles(self, user_id: str) -> list[Role]:
        """Get all roles for a user."""
        ...

    @abstractmethod
    async def assign_role(self, user_id: str, role: Role) -> bool:
        """Assign a role to a user."""
        ...


class AISafetyPort(ABC):
    """Port for AI safety guardrails."""

    @abstractmethod
    async def check_input(self, content: str) -> tuple[bool, str | None]:
        """Check input for prompt injection / harmful content."""
        ...

    @abstractmethod
    async def check_output(self, content: str) -> tuple[bool, str | None]:
        """Check AI output for safety compliance."""
        ...

    @abstractmethod
    async def audit_log(self, event: dict) -> None:
        """Log a security-relevant event."""
        ...
```

**Responsibilities**:
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- API key management for external integrations
- Prompt injection detection and prevention
- Output safety filtering
- Audit logging for all security events


### Component 11: Observability (`services/observability/`)

**Purpose**: Provides structured logging, distributed tracing, metrics collection, and alerting for all services in the monorepo.

**Interface**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class MetricType(StrEnum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class LogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True)
class SpanContext:
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    service_name: str = ""
    operation: str = ""


class MetricsPort(ABC):
    """Port for metrics collection."""

    @abstractmethod
    def increment(self, name: str, value: float = 1.0, tags: dict | None = None) -> None:
        """Increment a counter metric."""
        ...

    @abstractmethod
    def gauge(self, name: str, value: float, tags: dict | None = None) -> None:
        """Set a gauge metric."""
        ...

    @abstractmethod
    def histogram(self, name: str, value: float, tags: dict | None = None) -> None:
        """Record a histogram observation."""
        ...


class TracingPort(ABC):
    """Port for distributed tracing."""

    @abstractmethod
    def start_span(self, operation: str, parent: SpanContext | None = None) -> SpanContext:
        """Start a new trace span."""
        ...

    @abstractmethod
    def end_span(self, span: SpanContext, status: str = "ok") -> None:
        """End a trace span."""
        ...

    @abstractmethod
    def inject_context(self, span: SpanContext) -> dict[str, str]:
        """Inject span context into headers for propagation."""
        ...


class LoggingPort(ABC):
    """Port for structured logging."""

    @abstractmethod
    def log(
        self, level: LogLevel, message: str, context: dict | None = None
    ) -> None:
        """Emit a structured log entry."""
        ...

    @abstractmethod
    def with_context(self, **kwargs) -> "LoggingPort":
        """Create a logger with bound context fields."""
        ...
```

**Responsibilities**:
- Structured JSON logging with correlation IDs
- Distributed tracing with context propagation
- Prometheus-compatible metrics export
- Health check aggregation across services
- Alerting threshold definitions


### Component 12: Plugin System (`services/plugin-system/`)

**Purpose**: Provides extensibility through a plugin architecture that allows third-party extensions to register capabilities, tools, and integrations without modifying core services.

**Interface**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class PluginStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    LOADING = "loading"


@dataclass(frozen=True)
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    author: str
    description: str
    entry_point: str
    permissions: list[str]
    dependencies: list[str] = ()


@dataclass
class PluginInstance:
    manifest: PluginManifest
    status: PluginStatus
    error: str | None = None


class PluginPort(ABC):
    """Port that all plugins must implement."""

    @abstractmethod
    async def activate(self) -> None:
        """Activate plugin and register capabilities."""
        ...

    @abstractmethod
    async def deactivate(self) -> None:
        """Deactivate plugin and cleanup resources."""
        ...

    @abstractmethod
    async def get_capabilities(self) -> list[str]:
        """Return capabilities provided by this plugin."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check plugin health."""
        ...


class PluginRegistryPort(ABC):
    """Port for plugin lifecycle management."""

    @abstractmethod
    async def install(self, manifest: PluginManifest) -> str:
        """Install a plugin from its manifest."""
        ...

    @abstractmethod
    async def uninstall(self, plugin_id: str) -> bool:
        """Uninstall a plugin."""
        ...

    @abstractmethod
    async def activate(self, plugin_id: str) -> bool:
        """Activate an installed plugin."""
        ...

    @abstractmethod
    async def deactivate(self, plugin_id: str) -> bool:
        """Deactivate a running plugin."""
        ...

    @abstractmethod
    async def list_plugins(self) -> list[PluginInstance]:
        """List all installed plugins."""
        ...
```

**Responsibilities**:
- Plugin discovery, installation, and activation
- Sandboxed plugin execution
- Permission-gated access to system capabilities
- Plugin dependency resolution
- Version compatibility checking


## Data Models

### Model 1: Service Configuration Schema

```python
from pydantic import BaseModel, Field
from enum import StrEnum


class Environment(StrEnum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "sona_db"
    user: str = "sona"
    password: str = Field(exclude=True)
    pool_size: int = 20
    pool_overflow: int = 10
    ssl_mode: str = "prefer"


class RedisConfig(BaseModel):
    url: str = "redis://localhost:6379/0"
    max_connections: int = 50
    decode_responses: bool = True
    socket_timeout: float = 5.0


class VectorDBConfig(BaseModel):
    url: str = "http://localhost:6333"
    collection_prefix: str = "sona_"
    embedding_dimension: int = 1536
    distance_metric: str = "cosine"


class LLMProviderConfig(BaseModel):
    provider: str
    api_key: str = Field(exclude=True)
    base_url: str | None = None
    model_id: str
    max_tokens: int = 4096
    timeout_seconds: int = 60
    retry_count: int = 3


class ServiceConfig(BaseModel):
    """Root configuration for any service in the monorepo."""
    service_name: str
    environment: Environment = Environment.LOCAL
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    database: DatabaseConfig | None = None
    redis: RedisConfig | None = None
    vector_db: VectorDBConfig | None = None
    llm_providers: list[LLMProviderConfig] = []
    log_level: str = "info"
    cors_origins: list[str] = ["http://localhost:3000"]
```

**Validation Rules**:
- `password` fields are excluded from serialization
- `port` must be between 1 and 65535
- `pool_size` must be positive
- `environment` determines default values for debug, log_level, cors_origins
- LLM provider configs are validated for required fields per provider type

### Model 2: API Gateway Request/Response

```python
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str = Field(min_length=1, max_length=100_000)
    name: str | None = None
    timestamp: datetime | None = None


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    model: str | None = None
    stream: bool = False
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=128_000)
    session_id: str | None = None
    metadata: dict | None = None


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    content: str
    model_used: str
    usage: TokenUsage
    session_id: str
    latency_ms: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**Validation Rules**:
- `role` must be one of: user, assistant, system
- `content` must be non-empty, max 100K characters
- `temperature` must be between 0.0 and 2.0
- `max_tokens` must be between 1 and 128,000
- `messages` must contain at least one message


## Algorithmic Pseudocode

### Request Processing Pipeline Algorithm

```python
async def execute_brain_pipeline(request: BrainRequest) -> BrainResponse:
    """
    Main Brain OS execution pipeline.
    Orchestrates the full request lifecycle through all subsystems.
    """
    # PRECONDITIONS:
    # - request is validated and authenticated
    # - session_id refers to an existing or new session
    # - all downstream services are healthy

    # Step 1: Retrieve memory context
    memory_context = await memory_os.retrieve(
        MemoryQuery(
            user_id=request.user_id,
            query=request.messages[-1].content,
            memory_types=[MemoryType.WORKING, MemoryType.SHORT_TERM, MemoryType.LONG_TERM],
            top_k=10,
        )
    )

    # Step 2: Route through Thalamus
    routing = await thalamus.route({
        "content": request.messages[-1].content,
        "context": memory_context,
        "user_id": request.user_id,
    })

    # Step 3: Select model and assemble context
    model_config = await kernel.select_model(
        KernelRequest(
            session_id=request.session_id,
            user_id=request.user_id,
            content=request.messages[-1].content,
            context={"memory": memory_context, "routing": routing},
        )
    )

    # Step 4: Delegate to agent if multi-step task
    if routing.requires_agents:
        agent_results = await workforce.dispatch_parallel([
            AgentTask(
                task_id=f"{request.session_id}_{i}",
                agent_type=AgentType(agent_name),
                instruction=request.messages[-1].content,
                context={"memory": memory_context},
            )
            for i, agent_name in enumerate(routing.requires_agents)
        ])
        augmented_context = merge_agent_results(agent_results)
    else:
        augmented_context = {}

    # Step 5: Execute LLM call through kernel
    kernel_response = await kernel.process(
        KernelRequest(
            session_id=request.session_id,
            user_id=request.user_id,
            content=request.messages[-1].content,
            context={**memory_context, **augmented_context},
            model_override=model_config,
        )
    )

    # Step 6: Store interaction in memory
    await memory_os.store(
        user_id=request.user_id,
        entry=MemoryEntry(
            id=generate_id(),
            memory_type=MemoryType.SHORT_TERM,
            content=kernel_response.content,
            importance=0.7,
        ),
    )

    # POSTCONDITIONS:
    # - Response content is non-empty
    # - Token usage is accurately reported
    # - Memory is updated with the interaction
    # - Latency is within acceptable bounds

    return BrainResponse(
        content=kernel_response.content,
        session_id=request.session_id,
        model_used=kernel_response.model_used,
        tokens={"input": kernel_response.tokens_input, "output": kernel_response.tokens_output},
        latency_ms=kernel_response.latency_ms,
        agent_used=routing.requires_agents[0] if routing.requires_agents else None,
        memory_updated=True,
    )
```

**Preconditions:**
- Request has passed authentication and validation at the gateway
- Session exists or will be created on first use
- At least one LLM provider is available and healthy
- Memory store is accessible

**Postconditions:**
- Returns a valid BrainResponse with non-empty content
- Token usage reflects actual consumption
- Conversation is persisted to memory
- Trace spans are emitted for observability

**Loop Invariants:** N/A (pipeline is sequential, not iterative)


### Service Discovery and Health Check Algorithm

```python
async def check_all_services_health() -> dict[str, bool]:
    """
    Performs concurrent health checks on all registered services.
    Used by the gateway and observability layer.
    """
    # PRECONDITIONS:
    # - Service registry is populated with service endpoints
    # - Network connectivity to all service endpoints

    registered_services = await service_registry.list_all()
    health_results: dict[str, bool] = {}

    # Parallel health check with timeout
    # LOOP INVARIANT: All checked services have a boolean result
    tasks = []
    for service in registered_services:
        tasks.append(check_single_service(service))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for service, result in zip(registered_services, results):
        if isinstance(result, Exception):
            health_results[service.name] = False
            await observability.log(
                LogLevel.ERROR,
                f"Health check failed for {service.name}",
                {"error": str(result)},
            )
        else:
            health_results[service.name] = result

    # POSTCONDITIONS:
    # - Every registered service has exactly one health result
    # - Failed services are logged at ERROR level
    # - Result dict length == registered service count
    assert len(health_results) == len(registered_services)

    return health_results


async def check_single_service(service: ServiceEntry) -> bool:
    """Check health of a single service with timeout and retry."""
    # PRECONDITIONS:
    # - service.health_endpoint is a valid URL
    # - service.timeout_ms is positive

    for attempt in range(3):
        # LOOP INVARIANT: attempt < 3 and no successful response yet
        try:
            response = await http_client.get(
                service.health_endpoint,
                timeout=service.timeout_ms / 1000,
            )
            if response.status_code == 200:
                return True
        except (TimeoutError, ConnectionError):
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    return False
```

**Preconditions:**
- Service registry contains at least the gateway service
- HTTP client is configured with appropriate connection pooling

**Postconditions:**
- Returns complete health map for all registered services
- Unhealthy services are logged with error details
- Total execution time bounded by max(service.timeout_ms) * 3 retries

**Loop Invariants:**
- `health_results` dictionary grows monotonically (one entry per service)
- Each retry attempt uses exponential backoff (1s, 2s, 4s)


## Key Functions with Formal Specifications

### Function 1: thalamus_route()

```python
async def thalamus_route(content: str, context: dict, user_id: str) -> RoutingDecision:
    """Route a request to the appropriate downstream service."""
```

**Preconditions:**
- `content` is a non-empty string (already validated at gateway)
- `context` contains at minimum `{"session_id": str}`
- `user_id` is authenticated and authorized
- At least one downstream service is healthy

**Postconditions:**
- Returns a valid `RoutingDecision` with a reachable `target_service`
- `intent` is one of the defined `IntentCategory` values
- `priority` is assigned based on intent classification confidence
- If primary target is unhealthy, `fallback_service` is non-None
- Routing decision is recorded for observability

**Loop Invariants:** N/A

### Function 2: memory_retrieve()

```python
async def memory_retrieve(query: MemoryQuery) -> list[MemoryEntry]:
    """Retrieve relevant memories using vector similarity search."""
```

**Preconditions:**
- `query.user_id` is valid and has associated memories
- `query.query` is non-empty
- Vector database is healthy and contains indexed embeddings
- `query.top_k` > 0

**Postconditions:**
- Returns list of length <= `query.top_k`
- All returned entries belong to the queried `user_id`
- Entries are sorted by relevance (descending similarity score)
- All entries have `importance >= query.min_importance`
- If `time_range` is specified, all entries fall within that range
- Empty list is valid (no relevant memories found)

**Loop Invariants:**
- During re-ranking: previously scored entries maintain their computed relevance score

### Function 3: workflow_execute_step()

```python
async def workflow_execute_step(
    step: WorkflowStep, context: dict
) -> tuple[StepStatus, dict]:
    """Execute a single workflow step with retry and timeout."""
```

**Preconditions:**
- All `depends_on` steps have completed successfully
- `step.action` maps to a registered action handler
- `step.timeout_seconds` > 0
- `step.retry_count` >= 0
- `context` contains outputs from all dependency steps

**Postconditions:**
- Returns `(StepStatus.COMPLETED, outputs)` on success
- Returns `(StepStatus.FAILED, {"error": str})` after exhausting retries
- Returns `(StepStatus.SKIPPED, {})` if condition evaluates to false
- Total execution time <= `step.timeout_seconds * (step.retry_count + 1)`
- Each retry attempt is logged with attempt number and error

**Loop Invariants:**
- `attempts_remaining` decreases by 1 each iteration
- Backoff duration doubles each retry: `delay = 2^attempt` seconds
- Previous attempt errors are accumulated in the error list


## Example Usage

### Example 1: Service Module Setup (pyproject.toml for a service)

```python
# services/ai-kernel/pyproject.toml
"""
[project]
name = "sona-ai-kernel"
version = "1.0.0"
description = "AI Kernel - Central intelligence engine for Sona AI OS"
requires-python = ">=3.12"
dependencies = [
    "sona-shared-kernel",
    "sona-llm-client",
    "sona-event-bus",
    "fastapi>=0.115",
    "pydantic>=2.0",
    "structlog>=24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "ruff>=0.4",
    "mypy>=1.10",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
"""
```

### Example 2: Implementing a Service with Ports/Adapters

```python
# services/ai-kernel/application/use_cases/process_request.py
from dataclasses import dataclass

from sona_shared.ports import UnitOfWork
from ai_kernel.domain.models import KernelRequest, KernelResponse
from ai_kernel.application.ports import (
    AIKernelPort,
    ModelRouterPort,
    ReasoningEnginePort,
)


@dataclass
class ProcessRequestUseCase:
    """Use case: Process an AI request through the kernel pipeline."""

    model_router: ModelRouterPort
    reasoning_engine: ReasoningEnginePort
    unit_of_work: UnitOfWork

    async def execute(self, request: KernelRequest) -> KernelResponse:
        model_config = await self.model_router.route(request)

        reasoning_trace = await self.reasoning_engine.reason(
            prompt=request.content,
            context=request.context or {},
            strategy=request.strategy,
        )

        # Execute LLM call (delegated to infrastructure adapter)
        async with self.unit_of_work:
            response = await self._call_llm(model_config, request, reasoning_trace)
            await self.unit_of_work.commit()

        return response

    async def _call_llm(self, model_config, request, trace) -> KernelResponse:
        """Delegate to LLM client adapter."""
        ...
```

### Example 3: Docker Compose Service Definition

```python
# infra/compose/docker-compose.yml (represented as YAML structure)
"""
services:
  gateway:
    build:
      context: ../../
      dockerfile: infra/docker/Dockerfile.gateway
    ports: ["8000:8000"]
    environment:
      - SERVICE_NAME=gateway
      - DATABASE_URL=postgresql://sona:${POSTGRES_PASSWORD}@postgres:5432/sona_db
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
      qdrant: { condition: service_healthy }
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  ai-kernel:
    build:
      context: ../../
      dockerfile: infra/docker/Dockerfile.service
      args:
        SERVICE_NAME: ai-kernel
    environment:
      - SERVICE_NAME=ai-kernel
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      gateway: { condition: service_healthy }

  web:
    build:
      context: ../../apps/web
      dockerfile: ../../infra/docker/Dockerfile.web
    ports: ["3000:3000"]
    depends_on:
      gateway: { condition: service_healthy }

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: sona
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: sona_db
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sona"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes: ["redisdata:/data"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes: ["qdrantdata:/qdrant/storage"]

  nginx:
    build:
      context: ../../infra/nginx
      dockerfile: ../docker/Dockerfile.nginx
    ports: ["80:80", "443:443"]
    depends_on:
      gateway: { condition: service_healthy }
      web: { condition: service_started }
"""
```

### Example 4: GitHub Actions CI Pipeline (Monorepo-Aware)

```python
# .github/workflows/ci.yml (represented as YAML structure)
"""
name: CI Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      backend: ${{ steps.changes.outputs.backend }}
      frontend: ${{ steps.changes.outputs.frontend }}
      android: ${{ steps.changes.outputs.android }}
      infra: ${{ steps.changes.outputs.infra }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: changes
        with:
          filters: |
            backend:
              - 'services/**'
              - 'libs/**'
              - 'gateway/**'
            frontend:
              - 'apps/web/**'
            android:
              - 'apps/android/**'
            infra:
              - 'infra/**'
              - 'docker-compose.yml'

  backend-lint:
    needs: detect-changes
    if: needs.detect-changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install ruff mypy
      - run: ruff check services/ libs/ gateway/
      - run: ruff format --check services/ libs/ gateway/

  backend-test:
    needs: [detect-changes, backend-lint]
    if: needs.detect-changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: { POSTGRES_PASSWORD: test }
        ports: ['5432:5432']
      redis:
        image: redis:7-alpine
        ports: ['6379:6379']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -e libs/shared-kernel[dev]
      - run: pip install -e libs/llm-client[dev]
      - run: pip install -e libs/event-bus[dev]
      - run: |
          for service in services/*/; do
            pip install -e "$service[dev]"
          done
      - run: pytest --cov --cov-report=xml -v

  frontend-ci:
    needs: detect-changes
    if: needs.detect-changes.outputs.frontend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
        working-directory: apps/web
      - run: npm run lint
        working-directory: apps/web
      - run: npm run test -- --run
        working-directory: apps/web
      - run: npm run build
        working-directory: apps/web

  android-ci:
    needs: detect-changes
    if: needs.detect-changes.outputs.android == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { java-version: '17', distribution: 'temurin' }
      - run: ./gradlew lint test
        working-directory: apps/android
"""
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Result Type Round-Trip

*For any* value T, creating a Result via Result.ok(T) SHALL yield is_success == True and .value == T. *For any* error E, creating a Result via Result.fail(E) SHALL yield is_success == False and .error == E.

**Validates: Requirements 1.3**

### Property 2: Result Access Safety

*For any* failed Result (created via Result.fail(e)), accessing .value SHALL raise ValueError. *For any* successful Result (created via Result.ok(v)), accessing .error SHALL raise ValueError.

**Validates: Requirements 1.7, 1.8**

### Property 3: Configuration Password Exclusion

*For any* ServiceConfig, DatabaseConfig, or LLMProviderConfig instance containing a password field, serializing the model to dict or JSON SHALL never include the password value in the output.

**Validates: Requirement 19.4**

### Property 4: Configuration Validation Rejects Invalid Numerics

*For any* integer outside the range [1, 65535], setting it as a port value SHALL produce a validation error. *For any* integer less than or equal to zero, setting it as pool_size SHALL produce a validation error.

**Validates: Requirements 19.5, 19.6**

### Property 5: API Model Validation Rejects Out-of-Bound Values

*For any* string not in the set {"user", "assistant", "system"}, setting it as ChatMessage.role SHALL produce a validation error. *For any* float outside [0.0, 2.0], setting it as ChatRequest.temperature SHALL produce a validation error. *For any* integer outside [1, 128000], setting it as ChatRequest.max_tokens SHALL produce a validation error.

**Validates: Requirements 20.4, 20.6**

### Property 6: Pipeline Ordering Invariant

*For any* request processed through Brain_OS, memory retrieval SHALL always complete before model execution begins, model selection SHALL always complete before the LLM call, and response storage SHALL always occur after response generation completes.

**Validates: Requirements 27.3, 27.4, 27.5**

### Property 7: Memory Retrieval User Isolation

*For any* user U1 and any MemoryQuery issued by U1, the returned MemoryEntry list SHALL contain only entries where entry.user_id == U1. No entry belonging to any other user SHALL appear in the results.

**Validates: Requirement 31.1**

### Property 8: Token Validation Invariant

*For any* expired JWT token, calling validate_token() SHALL return None (rejection). *For any* revoked token, calling validate_token() SHALL return None (rejection). Only valid, non-expired, non-revoked tokens SHALL pass validation.

**Validates: Requirements 29.3, 29.4**

### Property 9: Memory Store-Retrieve Consistency

*For any* valid MemoryEntry stored via store(user_id, entry), a subsequent retrieve() with a matching query for that user_id SHALL include the stored entry in its results (within the consistency window).

**Validates: Requirement 31.1**

### Property 10: Memory Forget Exclusion

*For any* MemoryEntry that has been removed via forget(user_id, memory_id), all subsequent retrieve() calls SHALL never return that entry regardless of query parameters.

**Validates: Requirement 31.1**

### Property 11: Request Session Isolation

*For any* two concurrent requests R1 and R2 with different session_ids, processing R1 SHALL have no observable side effects on R2's memory retrieval, token attribution, or response content.

**Validates: Requirements 27.7, 31.1**

### Property 12: Health Check Retry With Backoff

*For any* service health check that fails, the system SHALL retry up to 3 times with exponential backoff (delay doubling each attempt). The total attempts SHALL never exceed the configured retry count.

**Validates: Requirement 28.4**


## Error Handling

### Error Scenario 1: LLM Provider Failure

**Condition**: Primary LLM provider returns timeout or 5xx error.
**Response**: Model router activates fallback chain — tries next provider in priority order (e.g., Ollama → OpenAI → Anthropic → Google AI).
**Recovery**: Circuit breaker opens for failed provider, closes after configurable cool-down period (default 60s). Health checks resume automatically.

### Error Scenario 2: Memory Store Unavailable

**Condition**: Redis or Qdrant is unreachable during request processing.
**Response**: Brain OS continues with degraded mode — processes request without memory context, logs warning. Response includes `memory_updated: false`.
**Recovery**: Background health checker detects recovery, resumes normal memory operations. Missing memories from degraded period are not retroactively stored.

### Error Scenario 3: Agent Timeout

**Condition**: A Workforce OS agent exceeds its `timeout_seconds` during task execution.
**Response**: Agent task is cancelled, partial results (if any) are returned. Orchestrator falls back to direct kernel processing without agent augmentation.
**Recovery**: Agent is marked as potentially unhealthy. If timeouts recur (3x in 5min), agent is restarted. Persistent failures trigger alerting.

### Error Scenario 4: Database Connection Exhaustion

**Condition**: PostgreSQL connection pool reaches maximum capacity.
**Response**: New requests receive 503 Service Unavailable with `Retry-After` header. Existing in-flight requests complete normally.
**Recovery**: Connection pool auto-recovers as in-flight requests complete. If sustained, horizontal scaling triggers (K8s HPA or manual intervention).

### Error Scenario 5: Plugin Crash

**Condition**: A plugin throws an unhandled exception during execution.
**Response**: Plugin is automatically deactivated, error is logged. Core system continues without plugin capabilities. User is notified of degraded functionality.
**Recovery**: Plugin remains deactivated until manual re-activation. Crash dump is stored for debugging.


## Testing Strategy

### Unit Testing Approach

Each service has isolated unit tests in its `tests/` directory. Tests use dependency injection to mock all ports (interfaces), ensuring no external dependencies are needed.

**Key test cases per service:**
- Domain model validation (entity creation, value object constraints)
- Use case logic (happy path, error paths, edge cases)
- Port adapter contracts (mock implementations verify interface compliance)

**Coverage goals:** Minimum 80% line coverage per service, 90% for shared-kernel.

**Tooling:** `pytest`, `pytest-asyncio`, `pytest-cov`, `factory_boy` for fixtures.

### Property-Based Testing Approach

Property-based tests validate system invariants across randomized inputs.

**Property Test Library:** `hypothesis` (Python)

**Key properties to test:**
- Serialization round-trip: `deserialize(serialize(x)) == x` for all domain models
- Memory retrieval ordering: results always sorted by relevance score descending
- Configuration validation: all valid configs pass, all invalid configs raise specific errors
- Token generation: tokens always decode to original payload within expiry

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=1000))
def test_memory_embedding_deterministic(text: str):
    """Same input always produces same embedding."""
    embedding1 = embed_sync(text)
    embedding2 = embed_sync(text)
    assert embedding1 == embedding2

@given(st.integers(min_value=1, max_value=100))
def test_memory_retrieve_respects_top_k(top_k: int):
    """Retrieval never returns more than top_k results."""
    results = retrieve_sync(query="test", top_k=top_k)
    assert len(results) <= top_k
```

### Integration Testing Approach

Integration tests run against real infrastructure (Docker Compose test environment) to verify service-to-service communication.

**Strategy:**
- Use `docker-compose.test.yml` to spin up PostgreSQL, Redis, Qdrant
- Test gateway → service routing end-to-end
- Verify health check propagation
- Test circuit breaker behavior under simulated failure

**Tooling:** `pytest`, `testcontainers-python`, `httpx` for async HTTP testing.

### Frontend Testing

**Web (React + TypeScript):**
- Unit tests: Vitest + React Testing Library
- Component tests: Storybook + visual regression
- E2E: Playwright for critical user flows

**Android (Kotlin):**
- Unit tests: JUnit 5 + MockK
- UI tests: Compose UI Testing
- Integration: Espresso for full-flow testing


## Performance Considerations

### Latency Requirements
- Gateway → Response: P95 < 3000ms for chat completions
- Memory retrieval (vector search): P95 < 100ms
- Intent classification (Thalamus): P95 < 50ms
- Health check round-trip: P95 < 500ms

### Scalability Strategy
- **Horizontal scaling**: Gateway and service instances scale independently
- **Connection pooling**: PostgreSQL (20 connections per instance), Redis (50 connections)
- **Caching**: Redis caches frequently accessed memories, model configs, and session state
- **Async-first**: All I/O operations use asyncio for non-blocking execution
- **Streaming**: SSE-based streaming reduces time-to-first-token perception

### Resource Budgets
- **Per-service container**: 512MB RAM, 0.5 CPU (base), auto-scale to 2GB / 2 CPU
- **PostgreSQL**: 1GB RAM, dedicated connection pool
- **Redis**: 512MB max-memory with LRU eviction
- **Qdrant**: Scales with document count, 1GB baseline

### Token Budget Management
- Context window managed by AI Kernel (max 128K tokens for capable models)
- Memory retrieval capped at configurable token budget (default 4K tokens of context)
- Conversation history truncated with sliding window (last N turns + summarized history)

## Security Considerations

### Authentication Flow
- JWT tokens with short expiry (15 min access, 7 day refresh)
- API keys for service-to-service communication (rotated monthly)
- OAuth 2.0 support for third-party integrations

### Data Protection
- Encryption at rest: PostgreSQL TDE, Redis encryption (production)
- Encryption in transit: TLS 1.3 for all inter-service communication
- Secrets management: Environment variables in dev, vault in production
- User data isolation: Row-level security in PostgreSQL

### AI Safety
- Input sanitization: Prompt injection detection before model execution
- Output filtering: Content safety checks on all AI-generated responses
- Rate limiting: Per-user, per-API-key, and per-IP limits at gateway
- Audit trail: All AI operations logged with full request/response (configurable retention)

### Container Security
- Non-root containers (UID 1000)
- Read-only filesystem where possible
- No privileged mode
- Minimal base images (slim/alpine)
- Vulnerability scanning in CI (Trivy/Snyk)


## Dependencies

### Python Backend Services

| Dependency | Version | Purpose |
|-----------|---------|---------|
| FastAPI | >=0.115 | HTTP framework, OpenAPI generation |
| Pydantic | >=2.0 | Data validation, settings management |
| uvicorn | >=0.30 | ASGI server |
| structlog | >=24.0 | Structured logging |
| httpx | >=0.27 | Async HTTP client |
| sqlalchemy | >=2.0 | Database ORM (async) |
| asyncpg | >=0.29 | PostgreSQL async driver |
| redis[hiredis] | >=5.0 | Redis async client |
| qdrant-client | >=1.9 | Vector database client |
| openai | >=1.30 | OpenAI API client |
| anthropic | >=0.25 | Anthropic API client |
| google-generativeai | >=0.5 | Google AI client |
| pyjwt | >=2.8 | JWT token handling |
| cryptography | >=42.0 | Encryption utilities |
| prometheus-client | >=0.20 | Metrics export |
| opentelemetry-api | >=1.24 | Distributed tracing |

### Web Frontend (React + TypeScript)

| Dependency | Version | Purpose |
|-----------|---------|---------|
| React | ^19 | UI framework |
| TypeScript | ~6.0 | Type safety |
| Vite | ^8 | Build tool |
| Vitest | ^4 | Test framework |
| TanStack Query | ^5 | Server state management |
| React Router | ^7 | Client-side routing |
| Tailwind CSS | ^4 | Utility-first styling |
| Zustand | ^5 | Client state management |
| Axios | ^1 | HTTP client |

### Android (Kotlin + Jetpack Compose)

| Dependency | Version | Purpose |
|-----------|---------|---------|
| Kotlin | 2.0+ | Programming language |
| Jetpack Compose | BOM 2024 | UI framework |
| Hilt | 2.51+ | Dependency injection |
| Retrofit | 2.11+ | HTTP client |
| Room | 2.6+ | Local database |
| Coroutines | 1.8+ | Async programming |
| DataStore | 1.1+ | Preferences storage |

### Infrastructure

| Dependency | Version | Purpose |
|-----------|---------|---------|
| PostgreSQL | 16 | Primary relational database |
| Redis | 7 | Cache, session store, pub/sub |
| Qdrant | latest | Vector similarity search |
| Nginx | alpine | Reverse proxy, static serving |
| Docker | 25+ | Containerization |
| Docker Compose | 2.24+ | Multi-service orchestration |

## Migration Strategy

### Phase 1: Scaffolding (This Milestone)
1. Create new directory structure under `services/`, `libs/`, `apps/`, `infra/`
2. Extract shared interfaces into `libs/shared-kernel/`
3. Create `pyproject.toml` for each service with proper dependencies
4. Set up Docker Compose with all infrastructure services
5. Create monorepo-aware CI/CD pipelines
6. Migrate frontend to `apps/web/`
7. Migrate Android to `apps/android/`

### Phase 2: Service Extraction (Future)
1. Extract existing backend modules into their respective services
2. Establish inter-service communication patterns
3. Implement service discovery
4. Run both old and new systems in parallel for validation

### Phase 3: Full Migration (Future)
1. Complete extraction of all services
2. Remove legacy `backend/` directory
3. Enable independent service deployment
4. Full integration testing suite

### Backward Compatibility
- The existing `backend/` directory remains functional during migration
- New services can import from existing modules during transition
- Docker Compose supports running old and new architectures simultaneously
- CI/CD pipelines test both old and new paths until migration completes
