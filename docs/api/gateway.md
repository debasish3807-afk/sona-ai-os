# API Gateway Documentation

The API Gateway is the unified entry point for all client requests to Sona AI OS. It handles authentication, rate limiting, request validation, and routing to downstream services.

## Base URL

| Environment | URL |
|---|---|
| Local | `http://localhost:8000` |
| Staging | `https://api-staging.sona.ai` |
| Production | `https://api.sona.ai` |

## Authentication

All endpoints (except `/health` and `/api/v1/auth/*`) require a valid JWT Bearer token:

```
Authorization: Bearer <access_token>
```

Tokens are obtained via the `/api/v1/auth/login` endpoint and have a 15-minute expiry. Use the refresh token endpoint to obtain a new access token.

---

## Endpoints

### Health Check

```
GET /health
```

Returns service health status. No authentication required.

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Chat Completion

```
POST /api/v1/chat
```

Send a chat message and receive an AI response.

**Request Body:**
```json
{
  "messages": [
    { "role": "user", "content": "Explain quantum computing" }
  ],
  "model": null,
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 4096,
  "session_id": "optional-session-uuid",
  "metadata": {}
}
```

**Parameters:**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `messages` | array | Yes | Min 1 message |
| `messages[].role` | string | Yes | `user`, `assistant`, or `system` |
| `messages[].content` | string | Yes | 1 to 100,000 characters |
| `model` | string | No | Specific model override |
| `stream` | boolean | No | Default: `false` |
| `temperature` | float | No | 0.0 to 2.0, default: 0.7 |
| `max_tokens` | int | No | 1 to 128,000, default: 4096 |
| `session_id` | string | No | UUID for conversation continuity |
| `metadata` | object | No | Custom metadata |

**Response** `200 OK`:
```json
{
  "content": "Quantum computing uses quantum bits (qubits)...",
  "model_used": "ollama/llama3.1",
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 256,
    "total_tokens": 268
  },
  "session_id": "abc-123-def-456",
  "latency_ms": 1542.3,
  "created_at": "2024-01-15T10:30:05Z"
}
```

**Error Responses:**

| Code | Condition |
|---|---|
| `401` | Missing or invalid auth token |
| `422` | Validation error (invalid role, empty content, out-of-range values) |
| `429` | Rate limit exceeded |
| `503` | Service unavailable (downstream failure) |

---

### Chat Completion (Streaming)

```
POST /api/v1/chat
Content-Type: application/json

{ "messages": [...], "stream": true }
```

When `stream: true`, the response uses **Server-Sent Events (SSE)**:

```
data: {"content": "Quantum", "done": false}
data: {"content": " computing", "done": false}
data: {"content": " uses", "done": false}
...
data: {"content": "", "done": true, "usage": {...}}
```

---

### Models

```
GET /api/v1/models
```

List available AI models.

**Response** `200 OK`:
```json
{
  "models": [
    {
      "id": "ollama/llama3.1",
      "provider": "ollama",
      "capabilities": ["chat", "code"],
      "max_tokens": 128000
    }
  ]
}
```

---

### Providers

```
GET /api/v1/providers
```

List configured LLM providers and their status.

---

## Rate Limiting

| Tier | Requests/min | Tokens/hour |
|---|---|---|
| Free | 10 | 50,000 |
| Standard | 60 | 500,000 |
| Premium | 300 | 2,000,000 |
| Service | 1000 | Unlimited |

Rate limit headers are included in every response:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1705312260
```

---

## Error Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "validation_error",
    "message": "temperature must be between 0.0 and 2.0",
    "details": [
      {
        "field": "temperature",
        "message": "ensure this value is less than or equal to 2.0"
      }
    ]
  }
}
```

---

## CORS

The gateway allows cross-origin requests from configured origins:
- Local: `http://localhost:3000`
- Staging/Production: Configured per environment
