# Future Roadmap Review — Sona AI OS

**Date:** 2026-07-12

---

## Implementation Readiness Assessment

| Phase | Interface Ready | Implementation Ready | Estimated Effort |
|-------|----------------|---------------------|-----------------|
| Memory Engine Impl. | ✅ | Needs storage backend | Medium |
| Provider API Integration | ✅ | Needs HTTP client code | Medium |
| Agent Execution Logic | ✅ | Needs LLM integration | High |
| MCP Integration | Partially | Needs protocol impl. | Medium |
| RAG Pipeline | ✅ (via memory) | Needs vector DB | Medium |
| Database Layer | Placeholder | Needs ORM + migrations | Medium |
| Authentication | Designed | Needs JWT/OAuth impl. | Medium |
| Frontend | Structure only | Needs full build | High |
| Android | Structure only | Needs full build | High |
| Testing | Interfaces testable | Needs mock + tests | High |

---

## Recommended Implementation Order

### Phase 7: Core Implementations
1. In-memory implementations of MemoryStore (for testing)
2. Provider HTTP client wrappers (OpenAI first)
3. Basic agent execution with LLM delegation

### Phase 8: Storage & Persistence
1. SQLAlchemy/SQLite for conversation + session memory
2. Redis for working memory + caching
3. ChromaDB/Qdrant for vector embeddings

### Phase 9: Integration
1. Composition root wiring (adapters connecting modules)
2. End-to-end chat flow: API → Kernel → Provider → Response
3. Memory context assembly in conversation flow

### Phase 10: Operations
1. Docker Compose for local dev
2. GitHub Actions CI/CD
3. Health monitoring dashboard
4. Structured logging pipeline

### Phase 11: Advanced AI
1. Multi-agent workflows (planning + delegation)
2. RAG pipeline with knowledge ingestion
3. MCP tool integration
4. Memory consolidation background tasks

---

## Integration Points Already Defined

| From | To | Via |
|------|-----|-----|
| Kernel.ContextManager | Memory.ContextAssembler | Adapter in app/ |
| Kernel.ProviderRegistry | Providers.ProviderRegistry | Adapter in app/ |
| Kernel.TaskRouter | Agents.AgentRouter | Adapter in app/ |
| Agents.MemoryAgent | Memory.MemoryManager | Direct usage |
| Kernel.EventBus | Agents.AgentEvents | Event bridge |
| Providers.EmbeddingProvider | Memory.EmbeddingProvider | Same interface |

---

## Risk Mitigation

1. Start with in-memory implementations to validate interfaces
2. Use dependency injection to swap backends without code changes
3. Implement one provider end-to-end before scaling to 8
4. Add integration tests alongside each implementation phase
