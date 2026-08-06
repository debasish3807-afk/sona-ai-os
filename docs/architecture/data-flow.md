# Data Flow

This document describes how data flows between services for the key scenarios in Sona AI OS.

## Scenario 1: User Chat Request

A user sends a chat message through the web dashboard or Android app.

```
User (Web/Android)
    │
    ▼
API Gateway (/api/v1/chat)
    │  1. Authenticate JWT (→ Security service)
    │  2. Rate-limit check
    │  3. Validate ChatRequest model (Pydantic)
    │
    ▼
Thalamus Router
    │  4. Classify intent → IntentCategory (CHAT, RESEARCH, CODE, ...)
    │  5. Load-balance → select healthy Brain OS instance
    │  6. Return RoutingDecision
    │
    ▼
Brain OS (pipeline execution)
    │  7. Retrieve memory context (→ Memory OS)
    │     - Working memory (Redis, <5ms)
    │     - Short-term memory (Redis, <10ms)
    │     - Long-term/Semantic memory (Qdrant vector search, <100ms)
    │
    │  8. Select model (→ AI Kernel)
    │     - Analyze request complexity
    │     - Check provider availability
    │     - Return ModelConfig
    │
    │  9. [Optional] Dispatch agents (→ Workforce OS)
    │     - Parallel dispatch if requires_agents is non-empty
    │     - Each agent executes independently
    │     - Results merged into augmented_context
    │
    │  10. Execute LLM call (→ AI Kernel → LLM Provider)
    │      - Assemble prompt with memory + agent context
    │      - Stream tokens (SSE) or buffer full response
    │
    │  11. Store interaction (→ Memory OS)
    │      - Save to SHORT_TERM memory
    │      - Background consolidation job (→ LONG_TERM)
    │
    ▼
API Gateway
    │  12. Wrap in ChatResponse envelope
    │  13. Log trace span (→ Observability)
    │
    ▼
User ← JSON response (or SSE stream)
```

**Latency Budget** (P95, excluding LLM provider):
- Auth + rate-limit: ~5ms
- Thalamus routing: ~50ms
- Memory retrieval: ~100ms
- Model selection: ~10ms
- Response assembly: ~20ms
- **Total gateway overhead**: ~185ms

---

## Scenario 2: Document Ingestion (RAG)

A user uploads a document to a knowledge base.

```
User → POST /api/v1/knowledge/ingest
    │
    ▼
API Gateway → Knowledge OS
    │  1. Validate document type (PDF, MD, TXT, HTML, CODE, JSON)
    │  2. Extract text (DocumentProcessorPort.extract_text())
    │  3. Chunk document (DocumentProcessorPort.process())
    │     - Each chunk ~512 tokens with 50-token overlap
    │  4. Generate embeddings for each chunk (EmbeddingPort.embed_batch())
    │     - Calls LLM Client → embedding model (Ollama or OpenAI)
    │  5. Index chunks in Qdrant (KnowledgeBasePort.ingest())
    │     - Upsert vectors with document_id, chunk_index metadata
    │  6. Persist document metadata in PostgreSQL
    │
    ▼
User ← { document_id, chunks_indexed, status: "indexed" }
```

---

## Scenario 3: Knowledge Query (RAG Retrieval)

Brain OS requests relevant context during a research request.

```
Brain OS → Knowledge OS (KnowledgeBasePort.query())
    │  1. Preprocess query (clean, normalize)
    │  2. Generate query embedding (EmbeddingPort.embed())
    │  3. Vector similarity search in Qdrant (top_k=5, min_similarity=0.7)
    │  4. Re-rank results (optional, cross-encoder)
    │  5. Compile augmented_context string from top chunks
    │  6. Return RAGResult with chunks, context, sources, confidence
    │
Brain OS ← RAGResult
    │  7. Inject context into LLM prompt
    │  8. Generate grounded response
```

---

## Scenario 4: Multi-Agent Parallel Execution

A complex request requires multiple specialized agents.

```
Brain OS (routing.requires_agents = ["CODING", "RESEARCH"])
    │
    ├──▶ Workforce OS → Coding Agent
    │       - AgentTask { instruction, context, timeout=120s }
    │       - Executes code generation task
    │       - Returns AgentResult { output, artifacts }
    │
    └──▶ Workforce OS → Research Agent
            - AgentTask { instruction, context, timeout=120s }
            - Calls Research OS (web search, summarize)
            - Returns AgentResult { output, sources }
    │
    ▼ (both results arrive via asyncio.gather)
Brain OS
    │  - Merge agent outputs into augmented_context
    │  - Execute final LLM synthesis call
    │
    ▼
Response with combined coding + research output
```

---

## Scenario 5: Authentication Flow

```
User → POST /api/v1/auth/login
    │
    ▼
API Gateway → Security Service (AuthenticationPort.authenticate())
    │  1. Validate credentials (username/password or OAuth)
    │  2. Look up user in PostgreSQL
    │  3. Verify password hash (bcrypt)
    │  4. Generate JWT access token (15-min expiry)
    │  5. Generate refresh token (7-day expiry)
    │  6. Store refresh token in Redis
    │  7. Audit log the login event
    │
    ▼
User ← { access_token, refresh_token, expires_in: 900 }

Subsequent requests:
User → GET /api/v1/chat (Authorization: Bearer <token>)
    │
    ▼
API Gateway → Security (AuthenticationPort.validate_token())
    │  1. Decode JWT (verify signature, expiry)
    │  2. Check token revocation list (Redis)
    │  3. Load user roles
    │
    ▼
Request proceeds if valid; 401 if invalid/expired/revoked
```

---

## Data Persistence Map

| Service | PostgreSQL | Redis | Qdrant |
|---|:---:|:---:|:---:|
| memory-os | Long-term memory | Working/Short-term | Semantic/Episodic vectors |
| knowledge-os | Document metadata | Query cache | Document chunk embeddings |
| security | Users, roles, tokens | Token cache, revocation | - |
| workflow-engine | Workflow definitions, executions | - | - |
| observability | Audit logs | Metrics cache | - |

---

## Event Flow (Domain Events)

Services emit domain events via the `sona-event-bus` library for asynchronous side effects:

```
Memory OS → MemoryConsolidatedEvent
    └──▶ Observability: log consolidation metrics

Brain OS → PipelineCompletedEvent
    └──▶ Evaluation OS: record quality metrics
    └──▶ Observability: emit latency histogram

Security → TokenRevokedEvent
    └──▶ All services: invalidate any cached auth state

Plugin System → PluginActivatedEvent / PluginCrashedEvent
    └──▶ Observability: alert on crash
    └──▶ Workforce OS: update available agent capabilities
```
