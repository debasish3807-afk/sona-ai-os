# Dependency Graph — Sona AI OS Backend

**Date:** 2026-07-12  
**Status:** No circular dependencies, no violations

---

## Module Dependency Direction

```
                    ┌────────────┐
                    │    app/    │  (Composition Root)
                    └──────┬─────┘
                           │ depends on
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │  api/   │  │ config/ │  │  core/  │
        └────┬────┘  └─────────┘  └────┬────┘
             │                          │
             ▼                          ▼
        ┌─────────┐              ┌─────────┐
        │ config/ │              │ config/ │
        └─────────┘              └─────────┘
        ┌─────────┐
        │  core/  │
        └─────────┘


    ┌──────────┐   ┌────────────┐   ┌──────────┐   ┌──────────┐
    │ kernel/  │   │ providers/ │   │ agents/  │   │ memory/  │
    │          │   │            │   │          │   │          │
    │  (self-  │   │   (self-   │   │  (self-  │   │  (self-  │
    │contained)│   │ contained) │   │contained)│   │contained)│
    └──────────┘   └────────────┘   └──────────┘   └──────────┘
```

---

## Explicit Dependencies

| Source Module | Dependencies | Forbidden Imports |
|--------------|-------------|-------------------|
| `config/` | (none — foundation) | core, api, app, kernel, providers, agents, memory |
| `core/` | config | api, app, kernel, providers, agents, memory |
| `api/` | config, core | app, kernel, providers, agents, memory |
| `app/` | api, config, core | kernel, providers, agents, memory (direct) |
| `kernel/` | (self-contained) | providers, agents, memory, api, app |
| `providers/` | (self-contained) | kernel, agents, memory, api, app |
| `agents/` | (self-contained) | kernel, providers, memory, api, app |
| `memory/` | (self-contained) | kernel, providers, agents, api, app |

---

## Clean Architecture Layers

```
Layer 4 (Framework):    app/, api/
Layer 3 (Interface):    api/ routes, middleware
Layer 2 (Application):  kernel/, agents/ (orchestration)
Layer 1 (Domain):       providers/, memory/ (business abstractions)
Layer 0 (Foundation):   config/, core/ (shared primitives)
```

**Rule:** Dependencies point inward only. Inner layers never import from outer layers.

---

## Integration Strategy (Future)

When the composition root (`app/`) connects these modules at runtime:

```python
# app/ will use dependency injection to wire:
# kernel.ProviderRegistry ← adapts → providers.ProviderRegistry
# kernel.ContextManager   ← adapts → memory.MemoryContextAssembler
# kernel.TaskRouter       ← routes → agents.AgentRouter
```

This preserves compile-time independence while enabling runtime collaboration.

---

## Verification Command

```bash
cd backend && python3 -c "
import ast, os
modules = {'app','config','core','api','kernel','providers','agents','memory'}
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if not f.endswith('.py'): continue
        path = os.path.join(root, f)
        source = path.split('/')[1] if len(path.split('/')) >= 2 else None
        if source not in modules: continue
        tree = ast.parse(open(path).read())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                target = node.module.split('.')[0]
                if target in modules and target != source:
                    print(f'{source} -> {target} ({path})')
"
```
