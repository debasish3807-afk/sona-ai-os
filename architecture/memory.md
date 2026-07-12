# Memory System

## Overview

The Memory subsystem provides persistent and ephemeral storage for context, conversations, knowledge, and user preferences.

## Memory Types

| Type | Duration | Purpose |
|------|----------|---------|
| Working Memory | Session | Current conversation context |
| Short-term Memory | Hours/Days | Recent interactions and tasks |
| Long-term Memory | Permanent | User preferences, learned patterns |
| Episodic Memory | Permanent | Specific event records |
| Semantic Memory | Permanent | Factual knowledge and relationships |

## Architecture

```
┌─────────────────────────────────┐
│         Memory Manager           │
├─────────────────────────────────┤
│  Working Memory (In-Process)     │
│  Short-term Store (Redis/Cache)  │
│  Long-term Store (Vector DB)     │
│  Episodic Store (Document DB)    │
│  Semantic Store (Graph DB)       │
└─────────────────────────────────┘
```

## Operations

- **Store**: Save new memories with metadata
- **Retrieve**: Query memories by relevance
- **Consolidate**: Merge and summarize memories
- **Forget**: Remove outdated or irrelevant data
- **Index**: Maintain searchable indices

## Privacy

- All memory operations respect user privacy settings
- Local-first storage with optional cloud sync
- User can inspect, export, and delete memories
