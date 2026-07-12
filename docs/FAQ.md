# Frequently Asked Questions

---

## What is Sona AI OS?

Sona AI OS is a next-generation Personal AI Operating System designed to combine the world's best AI models into one intelligent platform. Instead of depending on a single AI model, it uses an AI Orchestrator that automatically selects the best model for every task.

---

## Is Sona AI OS a chatbot?

No. Sona AI OS is an AI Operating System built around:

- AI Kernel (central intelligence)
- Orchestrator (task coordination)
- Multi-Agent System (specialized workers)
- LLM Pool (multi-model routing)
- Long-Term Memory (persistent knowledge)
- RAG (context-aware generation)
- Automation Engine (workflow automation)

---

## What is an AI Orchestrator?

The Orchestrator analyzes every request and decides:

- Which AI model should answer
- Which tools should be invoked
- Which agents should collaborate
- Whether memory context is needed
- Whether web search is required

---

## What is an LLM Pool?

The LLM Pool is a collection of multiple AI models working together. Supported providers include:

- OpenAI (GPT-4, GPT-4o)
- Anthropic (Claude)
- Google (Gemini)
- Open-source local models (via Ollama)

The Orchestrator automatically selects the best model based on task type, cost, and performance.

---

## What architecture does the backend use?

The backend follows Clean Architecture with four layers:

1. **Domain** (core/) — Business entities and rules, no external dependencies
2. **Services** — Application use cases
3. **API** — HTTP interface adapters
4. **Infrastructure** (providers/, database/) — External service implementations

---

## What platforms are supported?

- **Web** — Browser-based interface (React + TypeScript)
- **Desktop** — Native application (Tauri)
- **Android** — Companion app (Kotlin + Jetpack Compose)

---

## What is the current project status?

The project is in the **Architecture Phase** (v0.2-alpha). All system architecture is documented and the repository structure is defined. Implementation has not yet begun.

---

## How can I contribute?

Contribution guidelines will be published when the project enters the implementation phase. For now, architecture feedback and documentation improvements are welcome.

---

## Version

FAQ v0.2 — Architecture Phase

---

© Sona AI OS
