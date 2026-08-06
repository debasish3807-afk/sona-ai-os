# Coding Standards

This document defines the coding standards for Sona AI OS across all three primary languages: Python, TypeScript, and Kotlin.

---

## Python Standards

### Version & Tooling

- Python 3.12+ required
- **Formatter**: `ruff format` (line length: 100)
- **Linter**: `ruff check`
- **Type checker**: `mypy` (strict mode)
- **Test runner**: `pytest` with `pytest-asyncio`

### Style Rules

```python
# Use StrEnum (not plain Enum) for string enumerations
from enum import StrEnum

class MemoryType(StrEnum):
    WORKING = "working"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"


# Use frozen dataclasses for value objects and domain models
from dataclasses import dataclass

@dataclass(frozen=True)
class MemoryEntry:
    id: str
    content: str
    importance: float = 0.5


# Use Result[T, E] pattern for error handling (not exceptions)
from sona_shared.domain.result import Result

async def fetch_memory(id: str) -> Result[MemoryEntry, str]:
    if not id:
        return Result.fail("ID cannot be empty")
    # ...
    return Result.ok(entry)


# Use ABCs for port interfaces
from abc import ABC, abstractmethod

class MemoryStorePort(ABC):
    @abstractmethod
    async def store(self, entry: MemoryEntry) -> str: ...

    @abstractmethod
    async def retrieve(self, query: str) -> list[MemoryEntry]: ...
```

### Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Modules | `snake_case` | `memory_store.py` |
| Classes | `PascalCase` | `MemoryStorePort` |
| Functions | `snake_case` | `retrieve_memories()` |
| Constants | `UPPER_SNAKE` | `MAX_RETRIES = 3` |
| Type aliases | `PascalCase` | `MemoryId = str` |
| Private | Leading underscore | `_internal_method()` |

### Import Order

```python
# 1. Standard library
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

# 2. Third-party
from fastapi import APIRouter
from pydantic import BaseModel

# 3. Local / shared kernel
from sona_shared.domain.entities import Entity, EntityId
from sona_shared.domain.result import Result

# 4. Same-service imports
from .ports import MemoryStorePort
```

### Type Hints

All functions must have complete type annotations:

```python
# Good
async def process(self, request: KernelRequest) -> KernelResponse: ...

# Bad — missing return type
async def process(self, request): ...
```

---

## TypeScript Standards

### Version & Tooling

- TypeScript 5.5+
- **Formatter**: Prettier (via ESLint)
- **Linter**: ESLint with TypeScript plugin
- **Build**: Vite 6
- **Testing**: Vitest + React Testing Library

### Style Rules

```typescript
// Use interfaces for object shapes
interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: Date;
}

// Use type for unions and computed types
type ApiResult<T> = { data: T; error: null } | { data: null; error: string };

// Use explicit return types on exported functions
export function formatTimestamp(date: Date): string {
  return date.toISOString();
}

// Use const assertions for literal types
const ROUTES = {
  home: "/",
  chat: "/chat",
  settings: "/settings",
} as const;
```

### Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Files (components) | `PascalCase.tsx` | `ChatWindow.tsx` |
| Files (utilities) | `camelCase.ts` | `apiClient.ts` |
| Components | `PascalCase` | `<ChatWindow />` |
| Hooks | `useCamelCase` | `useChatMessages()` |
| Constants | `UPPER_SNAKE` | `API_BASE_URL` |
| Types/Interfaces | `PascalCase` | `ChatMessage` |

### Project Organization

```
src/
├── app/            App shell, routing, global providers
├── features/       Feature modules (co-located components, hooks, api)
├── shared/         Reusable UI components, hooks, utilities
└── infrastructure/ API clients, state management, config
```

---

## Kotlin Standards

### Version & Tooling

- Kotlin 2.0+
- **Build**: Gradle 8.5+ with KTS
- **UI**: Jetpack Compose (BOM 2024)
- **DI**: Hilt 2.51+
- **Testing**: JUnit 5 + MockK

### Style Rules

```kotlin
// Use data class for domain models
data class ChatMessage(
    val id: String,
    val role: MessageRole,
    val content: String,
    val timestamp: Instant = Instant.now()
)

// Use sealed class for state management
sealed class UiState<out T> {
    data object Loading : UiState<Nothing>()
    data class Success<T>(val data: T) : UiState<T>()
    data class Error(val message: String) : UiState<Nothing>()
}

// Use suspend functions for async operations
interface ChatRepository {
    suspend fun sendMessage(message: ChatMessage): Result<ChatMessage>
    fun observeMessages(sessionId: String): Flow<List<ChatMessage>>
}
```

### Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Packages | `lowercase` | `com.sona.ai.features.chat` |
| Classes | `PascalCase` | `ChatViewModel` |
| Functions | `camelCase` | `sendMessage()` |
| Properties | `camelCase` | `isLoading` |
| Constants | `UPPER_SNAKE` | `MAX_MESSAGE_LENGTH` |

---

## General Practices (All Languages)

1. **No magic numbers** — Use named constants
2. **Single Responsibility** — One class/function does one thing
3. **Fail fast** — Validate inputs at boundaries
4. **Document why, not what** — Code explains what; comments explain why
5. **Tests are documentation** — Test names should read like specs
6. **No dead code** — Remove unused imports, functions, and files
