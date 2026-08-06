# Internal Service Communication

This document describes how services communicate internally within the Sona AI OS monorepo.

## Communication Patterns

### 1. Direct Port Invocation (In-Process)

For the current monorepo milestone, services communicate through **port interfaces** resolved via dependency injection. No network calls are needed when services run in the same process.

```python
# Brain OS invokes Memory OS through its port interface
class BrainPipeline:
    def __init__(self, memory_store: MemoryStorePort):
        self.memory_store = memory_store

    async def execute(self, request: BrainRequest):
        context = await self.memory_store.retrieve(
            MemoryQuery(user_id=request.user_id, query=request.messages[-1]["content"])
        )
        # ...
```

### 2. Domain Events (Asynchronous)

Services emit and subscribe to domain events via the `sona-event-bus` library. This decouples producers from consumers.

```python
# Publisher (Brain OS)
await event_bus.publish(PipelineCompletedEvent(
    session_id=request.session_id,
    latency_ms=response.latency_ms,
))

# Subscriber (Observability)
@event_bus.subscribe(PipelineCompletedEvent)
async def handle_pipeline_completed(event: PipelineCompletedEvent):
    metrics.histogram("pipeline_latency_ms", event.latency_ms)
```

### 3. HTTP (Future: Distributed Deployment)

When services are deployed as independent containers, they communicate over HTTP with service discovery. The routing uses the same port interfaces but with HTTP adapters.

---

## Service Contracts

Each service exposes port interfaces (ABCs) that define its contract. All inter-service communication must go through these ports.

### AI Kernel

| Method | Input | Output | Purpose |
|---|---|---|---|
| `process()` | `KernelRequest` | `KernelResponse` | Process a request through the kernel |
| `stream()` | `KernelRequest` | `AsyncIterator[str]` | Stream response tokens |
| `select_model()` | `KernelRequest` | `ModelConfig` | Choose the best model |

### Memory OS

| Method | Input | Output | Purpose |
|---|---|---|---|
| `store()` | `user_id`, `MemoryEntry` | `str` (ID) | Store a memory |
| `retrieve()` | `MemoryQuery` | `list[MemoryEntry]` | Retrieve matching memories |
| `consolidate()` | `user_id` | `int` (count) | Consolidate short-term to long-term |
| `forget()` | `user_id`, `memory_id` | `bool` | Delete a memory |
| `get_conversation_history()` | `session_id`, `limit` | `list[MemoryEntry]` | Get conversation history |

### Knowledge OS

| Method | Input | Output | Purpose |
|---|---|---|---|
| `ingest()` | `Document`, `kb_id` | `str` (doc ID) | Ingest a document |
| `query()` | `RAGQuery` | `RAGResult` | RAG retrieval query |
| `list_knowledge_bases()` | `user_id` | `list[dict]` | List user's knowledge bases |
| `delete_document()` | `document_id` | `bool` | Remove a document |

### Workforce OS

| Method | Input | Output | Purpose |
|---|---|---|---|
| `dispatch()` | `AgentTask` | `AgentResult` | Dispatch to best agent |
| `dispatch_parallel()` | `list[AgentTask]` | `list[AgentResult]` | Parallel multi-agent |
| `register_agent()` | `AgentType`, `AgentPort` | `None` | Register an agent |
| `list_agents()` | — | `dict[AgentType, AgentStatus]` | List agents and status |

### Security

| Method | Input | Output | Purpose |
|---|---|---|---|
| `authenticate()` | `credentials` | `AuthToken` | Login/authenticate |
| `validate_token()` | `token` | `AuthToken \| None` | Validate a JWT |
| `check_permission()` | `user_id`, `Permission` | `bool` | RBAC check |
| `check_input()` | `content` | `(bool, str \| None)` | AI safety on input |
| `check_output()` | `content` | `(bool, str \| None)` | AI safety on output |

---

## Error Handling Between Services

All inter-service calls use the `Result[T, E]` pattern:

```python
result = await memory_store.retrieve(query)
if not result.is_success:
    # Graceful degradation — continue without memory
    logger.warning(f"Memory retrieval failed: {result.error}")
    memory_context = []
else:
    memory_context = result.value
```

### Timeout & Retry Policy

| Service | Timeout | Retries | Backoff |
|---|---|---|---|
| Memory OS | 500ms | 2 | Exponential |
| Knowledge OS | 2000ms | 2 | Exponential |
| AI Kernel (LLM) | 60000ms | 1 | None |
| Workforce OS agents | 120000ms | 0 | N/A (task-level) |
| Security (auth) | 200ms | 3 | Linear |

### Circuit Breaker

Each service connection has a circuit breaker:
- **Opens** after 5 consecutive failures
- **Half-open** after 30 seconds
- **Closes** after 3 successful requests in half-open state

---

## Tracing & Correlation

All inter-service calls carry a trace context:

```python
# Automatically injected via observability middleware
headers = {
    "X-Trace-Id": "abc-123",
    "X-Span-Id": "span-456",
    "X-Parent-Span-Id": "span-789",
}
```

This enables end-to-end request tracing across all services.
