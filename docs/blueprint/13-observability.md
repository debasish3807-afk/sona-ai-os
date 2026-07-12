# 13 — Observability

> Observability provides comprehensive insight into Sona AI OS's runtime behavior, performance, and health. It encompasses metrics, tracing, logging, health checks, and specialized AI-system monitoring — reasoning traces, execution timelines, and cost tracking.

---

## Overview

Observability answers three questions:
1. **What happened?** (Logging)
2. **How long did it take?** (Metrics + Tracing)
3. **Why did it happen?** (Reasoning Traces + Correlation)

| Pillar | Technology | Purpose |
|--------|-----------|---------|
| Metrics | Prometheus-compatible | Quantitative system health |
| Tracing | OpenTelemetry | Request flow through components |
| Logging | Structured JSON | Detailed event records |
| Health Checks | Kubernetes-compatible | Operational readiness |
| AI Monitoring | Custom | Reasoning and cost visibility |

---

## Metrics

### Core Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `sona_requests_total` | Counter | method, endpoint, status | Total request count |
| `sona_request_duration_seconds` | Histogram | method, endpoint | Request latency distribution |
| `sona_errors_total` | Counter | type, component | Error count by type |
| `sona_active_requests` | Gauge | — | Currently processing requests |

### Latency Percentiles

| Percentile | Target | Alert Threshold |
|------------|--------|-----------------|
| p50 | < 100 ms | > 200 ms |
| p95 | < 200 ms | > 500 ms |
| p99 | < 1000 ms | > 2000 ms |

### AI-Specific Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `sona_tokens_consumed_total` | Counter | model, direction | Tokens used (input/output) |
| `sona_token_cost_dollars` | Counter | model, provider | Monetary cost of tokens |
| `sona_ai_response_seconds` | Histogram | model, task_type | AI generation latency |
| `sona_ai_first_token_seconds` | Histogram | model | Time to first token |
| `sona_goals_total` | Counter | type, outcome | Goals by type and result |
| `sona_verification_score` | Histogram | pipeline | Verification confidence |
| `sona_memory_entries` | Gauge | type | Memory entries per type |
| `sona_capabilities_active` | Gauge | type | Active capabilities |

### Engine Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `sona_engine_invocations_total` | Counter | engine, status | Engine call count |
| `sona_engine_duration_seconds` | Histogram | engine | Engine execution time |
| `sona_engine_queue_depth` | Gauge | engine | Pending tasks per engine |
| `sona_engine_health` | Gauge | engine | Health status (0/1) |

### Alerting Rules

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| High Error Rate | error_rate > 5% for 5m | Critical | Page on-call |
| Latency Spike | p95 > 500ms for 5m | Warning | Alert channel |
| Budget Exhaustion | remaining < 10% | Warning | Notify user |
| Engine Down | health = 0 for 2m | Critical | Auto-failover |
| Memory Pressure | usage > 80% | Warning | Trigger consolidation |

---

## Tracing

### Distributed Traces

Every request generates a trace spanning all involved components.

| Field | Description |
|-------|-------------|
| `trace_id` | Unique trace identifier (128-bit) |
| `span_id` | Individual operation identifier |
| `parent_span_id` | Parent operation (tree structure) |
| `operation` | Human-readable operation name |
| `start_time` | Span start timestamp |
| `duration` | Span duration |
| `status` | OK, ERROR, UNSET |
| `attributes` | Key-value metadata |
| `events` | Timestamped log entries within span |

### Span Hierarchy

```text
[request.process]
  ├── [intent.analyze]
  │     ├── [memory.retrieve_context]
  │     └── [llm.classify_intent]
  ├── [goal.plan]
  │     ├── [memory.retrieve_strategies]
  │     └── [llm.generate_plan]
  ├── [execution.run]
  │     ├── [task.1.execute]
  │     │     └── [tool.invoke]
  │     ├── [task.2.execute]
  │     │     └── [llm.generate_code]
  │     └── [task.3.execute]
  │           └── [tool.invoke]
  └── [verification.run]
        ├── [verify.security]
        ├── [verify.logic]
        └── [verify.hallucination]
```

### Context Propagation

| Protocol | Header | Format |
|----------|--------|--------|
| HTTP | `traceparent` | W3C Trace Context |
| gRPC | Metadata | OpenTelemetry |
| Message Queue | Message attributes | Custom carrier |
| Internal | Context object | Direct reference |

### Sampling Strategy

| Mode | Rate | Use Case |
|------|------|----------|
| Always-on | 100% | Development, staging |
| Probabilistic | 10% | Production (normal) |
| Rate-limited | 100 traces/s | Production (high traffic) |
| Error-biased | 100% errors, 10% success | Debugging |
| Tail-based | Retain slow/error traces | Production (cost-sensitive) |

---

## Logging

### Structured Format

All logs are structured JSON:

```text
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "message": "Goal completed successfully",
  "service": "kernel",
  "component": "goal_manager",
  "trace_id": "abc123...",
  "span_id": "def456...",
  "request_id": "req_789...",
  "user_id": "user_012...",
  "goal_id": "goal_345...",
  "duration_ms": 1250,
  "metadata": { ... }
}
```

### Correlation IDs

| ID | Scope | Propagation |
|----|-------|-------------|
| `trace_id` | Entire request flow | All components |
| `request_id` | Single API request | Within request |
| `session_id` | User session | Across requests |
| `goal_id` | Goal lifecycle | Across tasks |

### Log Levels

| Level | Usage | Examples |
|-------|-------|----------|
| `ERROR` | Unexpected failures requiring attention | Unhandled exception, engine crash |
| `WARN` | Degraded behavior, approaching limits | Budget at 80%, retry triggered |
| `INFO` | Significant business events | Goal completed, capability loaded |
| `DEBUG` | Detailed operational information | Cache hit/miss, query plan |
| `TRACE` | Very verbose, development only | Full request/response bodies |

### Log Retention

| Level | Retention | Storage |
|-------|-----------|---------|
| ERROR | 90 days | Hot storage |
| WARN | 30 days | Warm storage |
| INFO | 14 days | Warm storage |
| DEBUG | 3 days | Cold storage |
| TRACE | 1 day | Local only |

---

## Health Checks

### Probe Types

| Probe | Purpose | Frequency | Timeout |
|-------|---------|-----------|---------|
| **Liveness** | Is the process alive? | 10s | 3s |
| **Readiness** | Can it accept requests? | 5s | 5s |
| **Startup** | Has initialization completed? | 5s | 60s |

### Liveness Check

Verifies the process is running and not deadlocked:
- Event loop responsive
- No fatal unrecoverable errors
- Memory within bounds

### Readiness Check

Verifies the service can handle requests:
- All required connections established (DB, cache, queue)
- Critical engines loaded and healthy
- Configuration loaded successfully

### Startup Check

Verifies initial setup is complete:
- Database migrations applied
- Engine initialization complete
- Plugin loading finished
- Initial health checks passed

### Health Response

```text
{
  "status": "healthy | degraded | unhealthy",
  "checks": {
    "database": { "status": "up", "latency_ms": 2 },
    "cache": { "status": "up", "latency_ms": 1 },
    "engines": { "status": "degraded", "healthy": 4, "total": 5 },
    "memory": { "status": "up", "usage_percent": 65 }
  },
  "version": "1.2.3",
  "uptime_seconds": 86400
}
```

---

## Performance Monitoring

### Engine Latency

Track per-engine performance:

| Metric | Description | Target |
|--------|-------------|--------|
| Preparation time | Time to prepare a task | < 100 ms |
| Execution time | Time to complete a task | < 5s (AI), < 200ms (tool) |
| Queue wait time | Time spent waiting for engine | < 500 ms |
| Throughput | Tasks per second | > 10/s per engine |

### Memory Pressure

| Indicator | Threshold | Action |
|-----------|-----------|--------|
| Working memory utilization | > 80% | Trigger eviction |
| Vector index size | > 1GB | Trigger consolidation |
| Conversation buffer | > 100 turns | Trigger summarization |
| Total memory footprint | > 4GB | Alert + scale |

### Queue Depth

- Per-engine task queue depth
- Alert when queue depth > 10 (sustained)
- Auto-scaling trigger when depth > 20

---

## Reasoning Trace

Visualization of the AI's thought process.

### Trace Structure

| Field | Description |
|-------|-------------|
| `thought_id` | Unique thought identifier |
| `parent_id` | Previous thought in chain |
| `type` | observation, hypothesis, conclusion, decision |
| `content` | The thought content |
| `confidence` | Confidence in this thought |
| `evidence` | Supporting evidence references |
| `alternatives` | Other options considered |
| `timestamp` | When this thought occurred |

### Decision Audit

Every significant decision records:
- What options were considered
- How each option was evaluated
- Why the chosen option was selected
- What evidence supported the decision
- What confidence level was assigned

---

## Execution Timeline

Gantt-style visualization of task execution.

### Timeline Entry

| Field | Description |
|-------|-------------|
| `task_id` | Task identifier |
| `label` | Human-readable task name |
| `start` | Start timestamp |
| `end` | End timestamp |
| `status` | success, failure, cancelled |
| `engine` | Executing engine |
| `dependencies` | Which tasks blocked this one |
| `parallel_group` | Tasks executing concurrently |

### Visualization Modes

| Mode | Description |
|------|-------------|
| Gantt | Horizontal timeline bars |
| Waterfall | Sequential dependency chain |
| Flame | CPU-time focused |
| Dependency graph | DAG with timing |

---

## Resource Monitoring

### System Resources

| Resource | Metric | Alert Threshold |
|----------|--------|-----------------|
| CPU | Utilization % | > 80% sustained |
| Memory | RSS, heap, working set | > 85% of limit |
| GPU | Utilization, VRAM | > 90% VRAM |
| Disk | Usage, IOPS, latency | > 90% capacity |
| Network | Bandwidth, connections | > 80% capacity |

### Resource Reporting Interval

- Real-time dashboard: 1-second granularity
- Metrics storage: 15-second intervals
- Historical analysis: 1-minute rollups

---

## Cost Monitoring

### Per-Request Cost

| Component | Tracked |
|-----------|---------|
| Input tokens | Count × per-token price |
| Output tokens | Count × per-token price |
| Tool invocations | Count × per-call price |
| External APIs | Count × per-call price |
| Compute time | Duration × per-second price |

### Budget Tracking

| Level | Budget | Alert At | Hard Stop |
|-------|--------|----------|-----------|
| Per-request | $0.50 | 80% | 100% |
| Per-session | $5.00 | 80% | 100% |
| Daily (user) | $20.00 | 70% | 95% |
| Monthly (org) | $500.00 | 60% | 90% |

### Provider Comparison

Track cost across multiple LLM providers to optimize spending:

| Provider | Model | Input $/1K | Output $/1K | Avg Latency |
|----------|-------|------------|-------------|-------------|
| Provider A | Large | — | — | — |
| Provider B | Large | — | — | — |
| Provider A | Small | — | — | — |
| Local | Custom | — | — | — |

*Actual pricing tracked at runtime and reported in dashboards.*

---

*Next: [14 — Deployment](./14-deployment.md)*
