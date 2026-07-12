# 11 — Verification Fabric

> The Verification Fabric provides 10 independent review pipelines that validate AI outputs before delivery. Each pipeline operates autonomously, and their results are aggregated through a confidence-scored consensus mechanism.

---

## Overview

Every AI-generated output passes through the Verification Fabric before being presented to the user or committed to the system. This ensures safety, correctness, and quality.

| Property | Description |
|----------|-------------|
| **Multi-pipeline** | 10 specialized verification pipelines |
| **Parallel** | Pipelines execute concurrently for speed |
| **Veto power** | Any pipeline can block output delivery |
| **Confidence-scored** | Each pipeline produces a confidence score |
| **Configurable** | Pipelines can be enabled/disabled per context |
| **Auditable** | Full verification trace for every output |

---

## Pipeline Overview

| # | Pipeline | Focus | Veto Power |
|---|----------|-------|------------|
| 1 | Security Review | Injection, secrets, unsafe ops | Yes |
| 2 | Logic Review | Correctness, edge cases | Yes |
| 3 | Architecture Review | Dependency rules, coupling | No |
| 4 | Reasoning Review | Logical validity, evidence | No |
| 5 | Performance Review | Complexity, resources | No |
| 6 | Consistency Review | State coherence, contracts | Yes |
| 7 | Compliance Review | Policy, constitutional | Yes |
| 8 | Risk Review | Blast radius, reversibility | Yes |
| 9 | Cost Review | Token usage, budget | No |
| 10 | Hallucination Detection | Fact grounding, sources | Yes |

---

## 1. Security Review

Detects security vulnerabilities and unsafe operations.

### Checks

| Check | Description | Severity |
|-------|-------------|----------|
| **Injection** | SQL, command, template injection vectors | CRITICAL |
| **Secrets Exposure** | Hardcoded keys, tokens, passwords | CRITICAL |
| **Unsafe Operations** | Unrestricted file access, network calls | HIGH |
| **Dependency Vulnerabilities** | Known CVEs in added packages | HIGH |
| **Permission Escalation** | Operations exceeding granted permissions | CRITICAL |
| **Data Leakage** | PII exposure, logging sensitive data | HIGH |
| **Path Traversal** | Unvalidated file paths | HIGH |

### Scoring

```text
Security Score = 1.0 - (Σ severity_weight × finding_count) / max_score
CRITICAL: weight = 0.4  |  HIGH: weight = 0.2  |  MEDIUM: weight = 0.1
Veto threshold: score < 0.6
```

---

## 2. Logic Review

Validates correctness and completeness of generated code/decisions.

### Checks

| Check | Description |
|-------|-------------|
| **Correctness** | Does the output satisfy the stated requirements? |
| **Edge Cases** | Are boundary conditions handled? |
| **Invariant Preservation** | Are existing invariants maintained? |
| **Type Safety** | Are types consistent and correct? |
| **Error Handling** | Are failure paths addressed? |
| **Off-by-one** | Array bounds, loop termination |
| **Null Safety** | None/null handling in all paths |

### Scoring

```text
Logic Score = (checks_passed / total_checks) × confidence_multiplier
Veto threshold: score < 0.5
```

---

## 3. Architecture Review

Ensures structural integrity and design compliance.

### Checks

| Check | Description |
|-------|-------------|
| **Dependency Rules** | No disallowed cross-module imports |
| **Layer Violations** | Proper layer separation respected |
| **Coupling** | Coupling metrics within acceptable bounds |
| **Cohesion** | New code maintains module cohesion |
| **Interface Contracts** | Public APIs follow established patterns |
| **Circular Dependencies** | No new cycles introduced |

### Scoring

```text
Architecture Score = weighted_sum(rule_compliance) 
Advisory only — does not veto
```

---

## 4. Reasoning Review

Validates the quality of AI reasoning chains.

### Checks

| Check | Description |
|-------|-------------|
| **Logical Validity** | Conclusions follow from premises |
| **Evidence Quality** | Claims are supported by sources |
| **Conclusion Support** | Final answer addresses the question |
| **Assumption Transparency** | Assumptions are stated explicitly |
| **Alternative Consideration** | Were other approaches considered? |
| **Bias Detection** | Systematic bias in reasoning |

### Scoring

```text
Reasoning Score = (validity + evidence + support + transparency) / 4.0
Advisory — informs confidence but does not veto
```

---

## 5. Performance Review

Assesses computational efficiency and resource impact.

### Checks

| Check | Description |
|-------|-------------|
| **Time Complexity** | Algorithm complexity analysis |
| **Space Complexity** | Memory usage patterns |
| **Resource Usage** | CPU, I/O, network implications |
| **Latency Impact** | Effect on response times |
| **Scalability** | Behavior under increased load |
| **N+1 Queries** | Database query efficiency |
| **Hot Paths** | Optimization of frequently executed code |

### Scoring

```text
Performance Score = complexity_score × resource_score × latency_score
Advisory — flags but does not veto
```

---

## 6. Consistency Review

Ensures state coherence and data integrity.

### Checks

| Check | Description |
|-------|-------------|
| **State Coherence** | Modified state remains internally consistent |
| **Data Integrity** | No dangling references, orphaned records |
| **Contract Compliance** | API contracts honored (input/output schemas) |
| **Version Consistency** | No mixed-version conflicts |
| **Schema Compliance** | Database schema constraints maintained |
| **Idempotency** | Operations safe to retry |

### Scoring

```text
Consistency Score = 1.0 - (violations / total_checks)
Veto threshold: score < 0.7
```

---

## 7. Compliance Review

Validates adherence to organizational and system policies.

### Checks

| Check | Description |
|-------|-------------|
| **Policy Adherence** | Organizational coding standards met |
| **Constitutional Compliance** | System constitution not violated |
| **License Compliance** | No incompatible licenses introduced |
| **Regulatory** | Industry-specific requirements (GDPR, HIPAA) |
| **Accessibility** | WCAG compliance for UI changes |
| **Documentation** | Required documentation present |

### Scoring

```text
Compliance Score = mandatory_checks_passed / mandatory_checks_total
Veto threshold: any mandatory check fails
```

---

## 8. Risk Review

Evaluates potential negative impact and reversibility.

### Checks

| Check | Description |
|-------|-------------|
| **Blast Radius** | How much of the system is affected? |
| **Reversibility** | Can this be easily undone? |
| **Confidence Threshold** | Is system confidence sufficient for this action? |
| **Destructive Operations** | Deletions, overwrites, migrations |
| **External Effects** | API calls, notifications, deployments |
| **Data Loss Potential** | Risk of irreversible data changes |

### Risk Matrix

| Impact | Reversible | Score | Action |
|--------|-----------|-------|--------|
| Low | Yes | 0.9 | Proceed |
| Low | No | 0.7 | Proceed with warning |
| High | Yes | 0.6 | Require confirmation |
| High | No | 0.3 | Veto — require explicit approval |

### Scoring

```text
Risk Score = (1 - blast_radius) × reversibility × confidence
Veto threshold: score < 0.4
```

---

## 9. Cost Review

Monitors resource consumption against budgets.

### Checks

| Check | Description |
|-------|-------------|
| **Token Usage** | Tokens consumed vs. budget |
| **API Calls** | External API invocations count |
| **Compute Budget** | CPU/GPU time consumed |
| **Cost Projection** | Projected total cost at current rate |
| **Waste Detection** | Redundant or unnecessary operations |
| **Provider Optimization** | Could a cheaper provider suffice? |

### Scoring

```text
Cost Score = 1.0 - (projected_cost / budget_limit)
Advisory — warns at 80%, hard-stop at 100%
```

---

## 10. Hallucination Detection

Ensures outputs are grounded in verifiable sources.

### Checks

| Check | Description |
|-------|-------------|
| **Fact Grounding** | Claims traceable to known sources |
| **Source Verification** | Cited sources exist and support claims |
| **Confidence Scoring** | Self-reported confidence matches evidence |
| **Fabrication Detection** | Invented APIs, functions, or facts |
| **Version Accuracy** | Correct versions cited for packages/APIs |
| **Temporal Accuracy** | Information is current, not outdated |

### Detection Methods

| Method | Description |
|--------|-------------|
| **Source overlap** | Generated text similarity to source material |
| **Knowledge base lookup** | Verify against known facts |
| **Code validation** | Check that referenced APIs/functions exist |
| **Cross-reference** | Multiple sources confirm the claim |
| **Self-consistency** | Check for internal contradictions |

### Scoring

```text
Grounding Score = grounded_claims / total_claims
Veto threshold: score < 0.5
```

---

## Pipeline Orchestration

### Parallel Execution

All 10 pipelines execute concurrently:

```text
Output ──►┬── Security Review ──────►┐
          ├── Logic Review ──────────►│
          ├── Architecture Review ───►│
          ├── Reasoning Review ──────►│
          ├── Performance Review ────►├── Aggregator ──► Decision
          ├── Consistency Review ────►│
          ├── Compliance Review ─────►│
          ├── Risk Review ───────────►│
          ├── Cost Review ───────────►│
          └── Hallucination Detection►┘
```

### Veto Power

Pipelines with veto power can independently block output:

- If ANY veto-pipeline scores below its threshold → output is **REJECTED**
- Rejected outputs include the specific pipeline findings
- The system can attempt auto-remediation and re-verify

### Confidence Aggregation

```text
Overall Confidence = Σ (pipeline_score × pipeline_weight) / Σ pipeline_weight

Pipeline Weights:
  Security: 1.5  |  Logic: 1.3  |  Architecture: 0.8
  Reasoning: 0.7 |  Performance: 0.6  |  Consistency: 1.0
  Compliance: 1.2 |  Risk: 1.1  |  Cost: 0.5
  Hallucination: 1.4
```

### Decision Matrix

| Overall Confidence | Veto Triggered | Decision |
|-------------------|----------------|----------|
| > 0.8 | No | APPROVE — deliver output |
| 0.6 – 0.8 | No | APPROVE WITH WARNINGS |
| < 0.6 | No | REQUEST REVISION |
| Any | Yes | REJECT — block delivery |

### Auto-Remediation

When verification fails, the system can attempt automatic fixes:

1. Identify specific failing checks
2. Generate targeted fixes (e.g., add input validation, remove hardcoded secret)
3. Re-run affected pipelines only
4. If passes → deliver; if fails again → escalate to user

---

## Verification Trace

Every verification produces an auditable trace:

| Field | Description |
|-------|-------------|
| `trace_id` | Unique verification trace identifier |
| `output_id` | The output being verified |
| `timestamp` | When verification ran |
| `pipelines` | Per-pipeline results, scores, findings |
| `decision` | APPROVE, APPROVE_WITH_WARNINGS, REJECT |
| `confidence` | Aggregated confidence score |
| `duration` | Total verification time |
| `remediation` | Any auto-fix attempts and outcomes |

---

*Next: [12 — Security Architecture](./12-security-architecture.md)*
