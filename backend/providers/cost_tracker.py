"""Cost tracking for AI provider usage.

Tracks estimated costs based on token usage and provider pricing.
Pricing data is approximate and should be updated as providers change rates.
"""

from __future__ import annotations

from dataclasses import dataclass

from providers.types import TokenUsage


@dataclass
class CostEstimate:
    """Estimated cost for a single request."""

    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    model: str = ""
    provider: str = ""


# Pricing per 1M tokens (USD) — approximate, updated 2025
MODEL_PRICING: dict[str, dict[str, float]] = {
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "o1": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    # Anthropic Claude
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    # Google Gemini
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    # DeepSeek
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
    # Mistral
    "mistral-large-latest": {"input": 2.00, "output": 6.00},
    "mistral-small-latest": {"input": 0.20, "output": 0.60},
    "codestral-latest": {"input": 0.30, "output": 0.90},
    # Qwen (DashScope)
    "qwen-plus": {"input": 0.80, "output": 2.00},
    "qwen-turbo": {"input": 0.30, "output": 0.60},
    "qwen-max": {"input": 2.40, "output": 9.60},
}


def estimate_cost(model: str, usage: TokenUsage) -> CostEstimate:
    """Estimate the cost of a request based on model pricing.

    Args:
        model: Model identifier.
        usage: Token usage statistics.

    Returns:
        CostEstimate with calculated costs.
    """
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        # Try partial match (model names may have version suffixes)
        for key, val in MODEL_PRICING.items():
            if key in model or model in key:
                pricing = val
                break

    if not pricing:
        return CostEstimate(model=model)

    input_cost = (usage.prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (usage.completion_tokens / 1_000_000) * pricing["output"]

    return CostEstimate(
        input_cost_usd=round(input_cost, 8),
        output_cost_usd=round(output_cost, 8),
        total_cost_usd=round(input_cost + output_cost, 8),
        model=model,
    )
