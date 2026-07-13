# Phase 18 Test Suite

## Overview

Comprehensive test suite for the Sona AI OS Phase 18.0 AI Intelligence Platform.

**401 tests** covering all major subsystems:

| Module | Tests | Description |
|--------|-------|-------------|
| AI Schemas | 18 | Data models for AI requests/responses |
| OpenAI Provider | 16 | OpenAI provider integration |
| Gemini Provider | 11 | Gemini provider integration |
| Claude Provider | 11 | Claude/Anthropic provider integration |
| Ollama Provider | 11 | Local Ollama provider integration |
| OpenRouter Provider | 9 | OpenRouter aggregator provider |
| Provider Manager | 16 | Multi-provider management |
| Unified AI | 15 | Unified AI interface with failover |
| Token Tracker | 10 | Token usage tracking |
| AI Retry | 8 | Retry policy with exponential backoff |
| Embeddings | 10 | Simple embedding provider |
| Vector Store | 15 | In-memory vector search |
| Semantic Search | 12 | Semantic search over vectors |
| Knowledge Engine | 15 | Knowledge ingestion & retrieval |
| Chunking Engine | 10 | Document chunking strategies |
| Document Processor | 10 | Multi-format document processing |
| Knowledge Store | 12 | Document storage backend |
| Knowledge Search | 10 | Knowledge search with citations |
| Web Search | 11 | Web search interface |
| URL Reader | 8 | URL content extraction |
| Search Engine | 10 | Search engine with caching |
| Agent Intelligence | 14 | Collaborative reasoning & delegation |
| Shared Agent Memory | 9 | Inter-agent memory sharing |
| Strategy Learner | 10 | Strategy learning & success tracking |
| Prometheus Metrics | 13 | Metrics collection (Counter, Gauge, Histogram) |
| OTel Exporter | 8 | OpenTelemetry trace/metric export |
| Dashboard Config | 6 | Grafana dashboard generation |
| Vault Client | 12 | Secrets management |
| OIDC Provider | 12 | OpenID Connect authentication |
| Encryption | 10 | At-rest & transit encryption |
| Compliance Auditor | 8 | Security compliance checks |
| Integration Tests | 20 | End-to-end cross-module tests |
| Extra Tests | 36 | Additional edge cases & coverage |

## Running Tests

```bash
# Run all Phase 18 tests
python -m pytest tests/test_phase18.py -v

# Run with coverage
python -m pytest tests/test_phase18.py --cov=. --cov-report=term-missing

# Run a specific test class
python -m pytest tests/test_phase18.py::TestUnifiedAI -v
```

## Quality Gates

All quality gates pass:

- **Pytest**: 401/401 tests passing
- **Ruff**: Zero lint errors, zero format issues
- **Mypy**: Zero type errors (with `--ignore-missing-imports`)
- **Bandit**: Zero medium/high severity findings (only expected B101 assert usage in tests)

## Dependencies

Test runtime requires:
- pytest >= 8.0
- pytest-asyncio >= 0.23
- pytest-cov >= 5.0
- structlog
- pydantic >= 2.9
- pydantic-settings >= 2.6
- httpx >= 0.27
- fastapi >= 0.115
- python-jose[cryptography]
- argon2-cffi
