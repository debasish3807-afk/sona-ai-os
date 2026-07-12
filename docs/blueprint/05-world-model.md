# 05 — World Model

> The World Model is the kernel's real-time representation of everything it knows about the current operating context. It is the single source of truth that engines, planners, and verifiers consult when making decisions.

---

## Overview

The World Model is a structured, queryable snapshot that is continuously updated as the system operates. It answers the question: *"What does the AI know about the world right now?"*

| Property | Description |
|----------|-------------|
| **Scope** | Per-session, with shared project-level state across sessions |
| **Update Frequency** | Real-time (event-driven) |
| **Consistency** | Eventually consistent with optimistic reads |
| **Persistence** | Volatile (session-scoped) + durable (project-scoped) |

---

## Current Goal

The active goal being pursued by the kernel.

| Field | Type | Description |
|-------|------|-------------|
| `goal_id` | `UUID` | Unique identifier |
| `intent` | `str` | Natural language description |
| `structured_goal` | `GoalSpec` | Parsed goal with type, scope, constraints |
| `state` | `GoalState` | Current lifecycle state |
| `priority` | `Priority` | Urgency × Importance score |
| `parent_goal` | `UUID | None` | If this is a sub-goal |
| `success_criteria` | `list[Criterion]` | Measurable completion conditions |
| `deadline` | `datetime | None` | Optional time constraint |
| `progress` | `float` | 0.0 – 1.0 completion estimate |

---

## Workspace

Real-time representation of the developer's workspace.

| Field | Type | Description |
|-------|------|-------------|
| `project_path` | `Path` | Root directory of the active project |
| `project_type` | `ProjectType` | Detected project archetype (web, library, CLI, etc.) |
| `git_state` | `GitState` | Branch, clean/dirty, staged changes, stash count |
| `open_files` | `list[OpenFile]` | Files currently being edited (path, cursor, modifications) |
| `recent_files` | `list[RecentFile]` | Last 50 files accessed with timestamps |
| `file_tree` | `FileTree` | Cached directory structure with metadata |
| `active_terminals` | `list[Terminal]` | Running processes and their output buffers |
| `build_state` | `BuildState` | Last build result (pass/fail, errors, warnings) |

### GitState Detail

| Field | Type | Description |
|-------|------|-------------|
| `branch` | `str` | Current branch name |
| `ahead` | `int` | Commits ahead of remote |
| `behind` | `int` | Commits behind remote |
| `staged` | `list[Path]` | Staged file paths |
| `modified` | `list[Path]` | Unstaged modifications |
| `untracked` | `list[Path]` | Untracked files |
| `conflicts` | `list[Path]` | Merge conflict files |
| `last_commit` | `CommitInfo` | Hash, message, author, timestamp |

---

## Repository

Knowledge about the version control repository.

| Field | Type | Description |
|-------|------|-------------|
| `remotes` | `list[Remote]` | Name, URL, fetch/push status |
| `branches` | `BranchIndex` | Local and remote branches with last activity |
| `tags` | `list[Tag]` | Release tags with SemVer parsing |
| `commits` | `CommitLog` | Recent commit history (configurable depth) |
| `contributors` | `list[Contributor]` | Authors with contribution frequency |
| `pull_requests` | `list[PullRequest]` | Open PRs with review status |
| `ci_status` | `CIStatus` | Latest pipeline results per branch |

---

## Environment

The operating environment in which the system runs.

| Field | Type | Description |
|-------|------|-------------|
| `os` | `OSInfo` | Platform, version, architecture |
| `runtime` | `RuntimeInfo` | Language versions (Python, Node, etc.) |
| `package_manager` | `PackageManager` | pip, npm, cargo — detected manager and lockfile |
| `tools` | `list[Tool]` | Installed CLI tools with versions |
| `docker` | `DockerState | None` | Running containers, images, compose state |
| `resources` | `SystemResources` | CPU cores, RAM, disk, GPU availability |
| `network` | `NetworkState` | Connectivity, proxy config, allowed hosts |
| `environment_vars` | `dict[str, str]` | Relevant env vars (sanitized, no secrets) |

---

## Available Capabilities

Registry of capabilities currently loaded and accessible.

| Field | Type | Description |
|-------|------|-------------|
| `capabilities` | `list[Capability]` | All registered capabilities |
| `active` | `list[UUID]` | Currently active capability IDs |
| `suspended` | `list[UUID]` | Temporarily suspended capabilities |
| `health` | `dict[UUID, HealthStatus]` | Per-capability health status |
| `cost_map` | `dict[UUID, CostEstimate]` | Estimated cost per invocation |

### Capability Entry

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Unique identifier |
| `name` | `str` | Human-readable name |
| `version` | `SemVer` | Capability version |
| `type` | `CapabilityType` | tool, provider, integration, plugin |
| `permissions` | `list[Permission]` | Required permissions |
| `rate_limit` | `RateLimit | None` | Invocation constraints |

---

## Running Tasks

All currently executing tasks across the system.

| Field | Type | Description |
|-------|------|-------------|
| `tasks` | `list[RunningTask]` | Active task entries |
| `queue_depth` | `int` | Tasks waiting for execution |
| `concurrency` | `int` | Current parallel task count |
| `max_concurrency` | `int` | Configured limit |

### RunningTask Entry

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | `UUID` | Unique identifier |
| `goal_id` | `UUID` | Parent goal |
| `engine_id` | `str` | Assigned engine |
| `state` | `TaskState` | PENDING, RUNNING, BLOCKED, COMPLETING |
| `started_at` | `datetime` | Execution start time |
| `elapsed` | `Duration` | Time since start |
| `progress` | `float` | 0.0 – 1.0 |
| `resources_used` | `ResourceUsage` | Tokens, compute consumed so far |

---

## Resource Budget

Real-time budget tracking for the current session.

| Resource | Allocated | Consumed | Remaining | Unit |
|----------|-----------|----------|-----------|------|
| Tokens (input) | 100,000 | — | — | tokens |
| Tokens (output) | 50,000 | — | — | tokens |
| Compute time | 300 | — | — | seconds |
| API calls | 50 | — | — | invocations |
| Cost | $1.00 | — | — | USD |

| Field | Type | Description |
|-------|------|-------------|
| `budget` | `Budget` | Configured limits |
| `consumed` | `ResourceUsage` | Current consumption |
| `remaining` | `ResourceUsage` | Computed remaining |
| `projected` | `ResourceUsage` | Estimated total at completion |
| `alerts` | `list[BudgetAlert]` | Threshold warnings (50%, 80%, 95%) |

---

## Risk Register

Tracked risks that may affect the current goal or session.

| Field | Type | Description |
|-------|------|-------------|
| `risks` | `list[Risk]` | Active risk entries |
| `mitigations` | `dict[UUID, Mitigation]` | Applied or planned mitigations |
| `overall_risk_level` | `RiskLevel` | LOW, MEDIUM, HIGH, CRITICAL |

### Risk Entry

| Field | Type | Description |
|-------|------|-------------|
| `risk_id` | `UUID` | Unique identifier |
| `category` | `RiskCategory` | security, correctness, performance, cost, data_loss |
| `description` | `str` | Human-readable description |
| `probability` | `float` | 0.0 – 1.0 likelihood |
| `impact` | `ImpactLevel` | LOW, MEDIUM, HIGH, CRITICAL |
| `score` | `float` | probability × impact weight |
| `detected_at` | `datetime` | When the risk was identified |
| `source` | `str` | Which subsystem identified it |

---

## Active Sessions

All sessions connected to the current kernel instance.

| Field | Type | Description |
|-------|------|-------------|
| `sessions` | `list[Session]` | Active session entries |
| `current_session` | `UUID` | The session driving the current request |

### Session Entry

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `UUID` | Unique identifier |
| `user_id` | `str` | Authenticated user |
| `client` | `ClientType` | web, cli, desktop, mobile |
| `started_at` | `datetime` | Session creation time |
| `last_active` | `datetime` | Last interaction timestamp |
| `conversation_count` | `int` | Number of conversations in session |
| `goals_completed` | `int` | Goals finished this session |

---

## World Model Update Protocol

The World Model is updated through a publish-subscribe mechanism:

1. **Sensors** detect changes (filesystem watcher, git hooks, process monitor).
2. **Events** are published to the kernel event bus.
3. **World Model Updater** applies events to the model atomically.
4. **Subscribers** (engines, planners) receive invalidation notifications.

Updates are batched within a 100 ms window to avoid thrashing during rapid changes.

---

*Next: [06 — Goal Management](./06-goal-management.md)*
