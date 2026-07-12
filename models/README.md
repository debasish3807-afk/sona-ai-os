# Models

Configuration, prompts, and resources for AI/ML models used by Sona AI OS.

## Structure

```
models/
├── prompts/      — Model-specific prompt templates
├── system/       — System prompt definitions and personas
├── embeddings/   — Embedding model configurations and schemas
└── configs/      — Model configuration files and parameters
```

## Purpose

This directory manages all model-related resources:

- **prompts/**: Prompt templates optimized for specific models (GPT-4, Claude, Gemini, etc.)
- **system/**: System prompts that define the AI assistant's personality and behavior
- **embeddings/**: Configuration for embedding models used in RAG and memory
- **configs/**: Model parameters, routing rules, and provider settings

## Conventions

- Use YAML or JSON for configuration files
- Version prompt templates with clear naming
- Document model compatibility for each prompt
- Keep sensitive API keys in environment variables, not here
