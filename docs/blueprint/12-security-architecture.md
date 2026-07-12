# 12 — Security Architecture

> The Security Architecture provides defense-in-depth for Sona AI OS, covering authentication, authorization, secrets management, encryption, auditing, sandboxing, policy enforcement, and threat modeling — with specific considerations for AI system security.

---

## Overview

Security is treated as a cross-cutting concern that permeates every layer of the system.

| Principle | Description |
|-----------|-------------|
| **Zero Trust** | No implicit trust between components; verify every request |
| **Least Privilege** | Components receive only the permissions they need |
| **Defense in Depth** | Multiple layers of security controls |
| **Fail Secure** | On failure, default to deny |
| **Audit Everything** | All security-relevant actions are logged immutably |

---

## Authentication

### Authentication Methods

| Method | Use Case | Token Lifetime |
|--------|----------|----------------|
| **JWT (Access Token)** | API authentication | 15 minutes |
| **Refresh Token** | Token renewal | 7 days |
| **API Keys** | Service-to-service, CI/CD | Until revoked |
| **Session Cookies** | Web UI | 24 hours |
| **MFA-ready** | Optional second factor | N/A |

### JWT Structure

| Claim | Description |
|-------|-------------|
| `sub` | User identifier |
| `iss` | Token issuer |
| `exp` | Expiration timestamp |
| `iat` | Issued-at timestamp |
| `scope` | Granted permissions |
| `session_id` | Active session reference |
| `org_id` | Organization (multi-tenant) |

### Token Lifecycle

```text
1. User authenticates with credentials
2. Server validates credentials
3. Issue access token (short-lived) + refresh token (long-lived)
4. Client uses access token for requests
5. On expiry, client exchanges refresh token for new access token
6. On logout or security event, revoke all tokens
```

### API Key Management

- Scoped to specific permissions and endpoints
- SHA-256 hashed storage (never stored in plaintext)
- Rotation support with grace period for old keys
- Usage tracking and anomaly detection

---

## Authorization

### RBAC Model

| Role | Description | Scope |
|------|-------------|-------|
| `owner` | Full system control | Organization |
| `admin` | Configuration and user management | Organization |
| `developer` | Full AI and code capabilities | Project |
| `viewer` | Read-only access | Project |
| `service` | Automated service account | Specific API |

### Permission Granularity

| Category | Permissions |
|----------|-------------|
| **AI** | `ai.chat`, `ai.execute`, `ai.configure` |
| **Code** | `code.read`, `code.write`, `code.execute`, `code.deploy` |
| **Memory** | `memory.read`, `memory.write`, `memory.delete` |
| **Admin** | `admin.users`, `admin.config`, `admin.audit` |
| **Capabilities** | `capability.install`, `capability.execute`, `capability.configure` |

### Permission Resolution

```text
1. Identify authenticated user
2. Resolve user's roles (direct + inherited)
3. Aggregate permissions from all roles
4. Check requested permission against aggregated set
5. If permission found → ALLOW
6. If not found → DENY (fail secure)
7. Log decision for audit
```

### Resource-Level Access Control

Beyond role-based permissions, resources have ownership:

- Projects have owner + collaborator lists
- Files inherit project permissions
- Conversations are private to their owner
- Shared resources require explicit grants

---

## Secrets Management

### Architecture

| Component | Description |
|-----------|-------------|
| **Vault Integration** | HashiCorp Vault or compatible secret store |
| **Env-based Fallback** | Environment variables for simple deployments |
| **Runtime Injection** | Secrets injected at process start, never on disk |
| **Rotation** | Automatic rotation with zero-downtime handoff |

### Secret Types

| Type | Storage | Rotation Interval |
|------|---------|-------------------|
| Database credentials | Vault | 24 hours |
| API provider keys | Vault | 90 days |
| JWT signing key | Vault | 30 days |
| Encryption keys | KMS | Annual |
| User API keys | Hashed in DB | User-managed |

### Security Controls

- Secrets never appear in logs, traces, or error messages
- Secrets never persist to disk unencrypted
- Access to secrets is audited
- Compromised secrets trigger automatic rotation
- Secret references use URIs (`vault://path/to/secret`)

---

## Encryption

### At Rest

| Data | Algorithm | Key Management |
|------|-----------|----------------|
| Database | AES-256-GCM | KMS-managed DEK/KEK |
| File storage | AES-256-GCM | Per-file keys |
| Memory snapshots | AES-256-GCM | Session-derived key |
| Backups | AES-256-GCM | Backup-specific key |

### In Transit

| Channel | Protocol | Minimum Version |
|---------|----------|-----------------|
| API (external) | TLS 1.3 | Required |
| Service-to-service | mTLS | TLS 1.2+ |
| WebSocket | WSS (TLS) | TLS 1.2+ |
| Database connections | TLS | TLS 1.2+ |

### Field-Level Encryption

Sensitive fields encrypted independently of full-record encryption:

| Field Type | Encryption | Searchable |
|------------|------------|------------|
| PII (email, name) | AES-256-GCM | Blind index |
| API keys | AES-256-GCM | No |
| Conversation content | AES-256-GCM | Encrypted search |
| Financial data | AES-256-GCM | No |

---

## Audit Trail

### Properties

| Property | Description |
|----------|-------------|
| **Immutability** | Append-only log, no deletion or modification |
| **Tamper Detection** | Hash chain linking entries |
| **Completeness** | All security-relevant events captured |
| **Compliance** | Retention meets regulatory requirements |
| **Searchable** | Indexed for investigation and reporting |

### Audit Event Structure

| Field | Description |
|-------|-------------|
| `event_id` | Unique identifier |
| `timestamp` | UTC timestamp (nanosecond precision) |
| `actor` | Who performed the action (user, service, system) |
| `action` | What was done |
| `resource` | What was affected |
| `outcome` | SUCCESS, FAILURE, DENIED |
| `context` | Session, IP, user agent |
| `prev_hash` | Hash of previous entry (chain integrity) |

### Audited Events

- Authentication attempts (success and failure)
- Authorization decisions (grants and denials)
- Secret access
- Configuration changes
- Data access and modifications
- AI actions (tool invocations, code generation)
- Administrative operations

---

## Sandbox

### Capability Isolation

Each capability (plugin, tool) runs in an isolated sandbox:

| Boundary | Enforcement | Mechanism |
|----------|-------------|-----------|
| **Filesystem** | Restricted to declared paths | Namespace/chroot |
| **Network** | Allowlisted destinations only | Network policy |
| **Processes** | Cannot spawn unrestricted child processes | Seccomp/AppArmor |
| **Memory** | Hard memory limit | cgroups |
| **CPU** | Time-sliced execution | cgroups |
| **IPC** | Only kernel-mediated communication | Capability-based |

### Resource Limits

| Resource | Default Limit | Configurable |
|----------|---------------|-------------|
| Memory | 512 MB | Yes |
| CPU time | 30 seconds | Yes |
| Disk write | 100 MB | Yes |
| Network bandwidth | 10 MB/s | Yes |
| Open files | 256 | Yes |
| Child processes | 4 | Yes |

### Filesystem Boundaries

```text
Capability can access:
  ✓ Its own package directory (read-only)
  ✓ Declared workspace paths (read/write)
  ✓ Temp directory (read/write, cleaned on exit)
  ✗ System directories
  ✗ Other capabilities' directories
  ✗ Secret storage
  ✗ Kernel internals
```

---

## Policy Engine

### Declarative Rules

Policies are expressed as declarative rules:

```text
Policy: no-secrets-in-output
  When: output contains pattern matching secret_regex
  Then: BLOCK output, emit security_alert
  Severity: CRITICAL

Policy: max-file-modifications
  When: single request modifies > 20 files
  Then: REQUIRE user confirmation
  Severity: HIGH

Policy: no-external-network-in-sandbox
  When: capability attempts network call to non-allowlisted host
  Then: DENY request, log violation
  Severity: HIGH
```

### Enforcement Points

| Point | Description |
|-------|-------------|
| **Request Intake** | Validate request structure and permissions |
| **Pre-execution** | Check budget, rate limits, policy compliance |
| **During Execution** | Monitor real-time for policy violations |
| **Pre-output** | Verify output passes all policies |
| **Post-output** | Audit and detect delayed violations |

### Policy Composition

- Policies are evaluated in priority order
- First matching BLOCK policy terminates with rejection
- ALLOW policies grant specific exceptions
- Default action: DENY (fail secure)

---

## Rate Limiting

### Strategy: Sliding Window

| Scope | Window | Limit | Burst |
|-------|--------|-------|-------|
| Per-user (API) | 1 minute | 60 requests | 10 |
| Per-user (AI) | 1 minute | 10 requests | 3 |
| Per-endpoint | 1 second | 100 requests | 20 |
| Per-IP | 1 minute | 120 requests | 30 |
| Global | 1 second | 1000 requests | 200 |

### Rate Limit Response

| Status | Description |
|--------|-------------|
| Under limit | Normal processing |
| Near limit (80%) | Warning header in response |
| At limit | 429 Too Many Requests |
| Far over limit | Temporary block (5 minutes) |

### Headers

```text
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1620000060
Retry-After: 30 (when limited)
```

---

## Threat Model

### STRIDE Analysis for AI Systems

| Threat | AI-Specific Risks | Mitigations |
|--------|-------------------|-------------|
| **Spoofing** | Prompt injection impersonating system, fake tool responses | Input validation, signed messages, tool authentication |
| **Tampering** | Memory poisoning, training data manipulation, context injection | Immutable audit log, input sanitization, memory validation |
| **Repudiation** | Deny generating harmful output, deny destructive actions | Complete audit trail, output signing, execution recording |
| **Information Disclosure** | Leaking secrets via output, exposing training data, memory exfiltration | Output filtering, secret scanning, memory access controls |
| **Denial of Service** | Token exhaustion, infinite loops, resource starvation | Rate limiting, timeouts, budget enforcement, circuit breakers |
| **Elevation of Privilege** | Jailbreak via prompt, capability escape, sandbox breakout | Constitutional AI, capability isolation, defense in depth |

### AI-Specific Threats

| Threat | Description | Mitigation |
|--------|-------------|------------|
| **Prompt Injection** | Malicious instructions embedded in user input or retrieved content | Input sanitization, instruction hierarchy, output verification |
| **Context Poisoning** | Injecting false information into memory/context | Source validation, confidence scoring, memory integrity checks |
| **Goal Hijacking** | Manipulating the system to pursue unintended goals | Constitutional constraints, goal validation, human-in-the-loop |
| **Capability Abuse** | Using legitimate capabilities for unauthorized purposes | Permission scoping, action auditing, anomaly detection |
| **Data Exfiltration** | Extracting sensitive data through AI-generated outputs | Output scanning, DLP policies, data classification |

---

## Security Monitoring

### Real-time Detection

| Signal | Threshold | Action |
|--------|-----------|--------|
| Failed auth attempts | 5 in 5 minutes | Temporary account lock |
| Permission denials | 10 in 1 minute | Alert + investigation |
| Secret access anomaly | Unusual pattern | Alert + session review |
| Sandbox escape attempt | Any | Block + critical alert |
| Output policy violation | Any | Block + audit entry |

### Security Metrics

- Authentication failure rate
- Authorization denial rate
- Secret rotation compliance
- Vulnerability count by severity
- Time to patch (TTP)
- Mean time to detect (MTTD)
- Mean time to respond (MTTR)

---

*Next: [13 — Observability](./13-observability.md)*
