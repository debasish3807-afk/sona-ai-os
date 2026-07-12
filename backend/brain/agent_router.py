"""Agent router — automatically selects the best agent for a request.

Analyzes the user's message intent to route to the appropriate
specialized agent (coding, research, planning, etc.).
"""

from __future__ import annotations

import re

from brain.schemas import ChatMessageSchema
from config.logging import get_logger

logger = get_logger(__name__)


class AgentCategory:
    """Agent categories for routing."""

    GENERAL = "general"
    CODING = "coding"
    RESEARCH = "research"
    PLANNER = "planner"
    ANDROID = "android"
    WEB = "web"


# Intent detection patterns (keyword-based + semantic heuristics)
_CODING_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(code|coding|program|script|function|class|debug|fix\s+bug)\b", re.I),
    re.compile(r"\b(python|javascript|typescript|rust|java|kotlin|go|c\+\+|swift)\b", re.I),
    re.compile(r"\b(implement|refactor|optimize|algorithm|api|endpoint|database)\b", re.I),
    re.compile(r"\b(git|commit|pull\s+request|merge|branch|deploy)\b", re.I),
    re.compile(r"```", re.I),
]

_RESEARCH_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(research|investigate|find\s+out|look\s+up|search)\b", re.I),
    re.compile(r"\b(compare|analyze|summarize|explain|what\s+is|how\s+does)\b", re.I),
    re.compile(r"\b(paper|article|study|documentation|reference)\b", re.I),
    re.compile(r"\b(pros\s+and\s+cons|advantages|disadvantages|benchmark)\b", re.I),
]

_PLANNER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(plan|schedule|organize|timeline|roadmap|milestone)\b", re.I),
    re.compile(r"\b(step\s+by\s+step|breakdown|task\s+list|todo|prioritize)\b", re.I),
    re.compile(r"\b(project\s+plan|sprint|epic|strategy|architecture\s+plan)\b", re.I),
]

_ANDROID_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(android|kotlin|jetpack\s+compose|gradle|apk|adb)\b", re.I),
    re.compile(r"\b(activity|fragment|viewmodel|room|hilt|retrofit)\b", re.I),
    re.compile(r"\b(material\s+design|play\s+store|android\s+studio)\b", re.I),
]

_WEB_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(web|website|frontend|html|css|react|vue|angular|next\.?js)\b", re.I),
    re.compile(r"\b(browser|dom|responsive|tailwind|webpack|vite)\b", re.I),
    re.compile(r"\b(http|rest\s+api|graphql|websocket|cors|cookie)\b", re.I),
]


def _score_patterns(text: str, patterns: list[re.Pattern[str]]) -> int:
    """Count how many patterns match the text."""
    return sum(1 for p in patterns if p.search(text))


def detect_agent(messages: list[ChatMessageSchema]) -> str:
    """Detect the best agent for the given messages.

    Analyzes the most recent user message(s) to determine intent
    and routes to the appropriate specialized agent.

    Args:
        messages: The conversation messages.

    Returns:
        Agent category string.
    """
    # Combine recent user messages for analysis
    user_texts: list[str] = []
    for msg in reversed(messages):
        if msg.role == "user":
            user_texts.append(msg.content)
            if len(user_texts) >= 3:
                break

    if not user_texts:
        return AgentCategory.GENERAL

    combined_text = " ".join(user_texts)

    # Score each category
    scores: dict[str, int] = {
        AgentCategory.CODING: _score_patterns(combined_text, _CODING_PATTERNS),
        AgentCategory.RESEARCH: _score_patterns(combined_text, _RESEARCH_PATTERNS),
        AgentCategory.PLANNER: _score_patterns(combined_text, _PLANNER_PATTERNS),
        AgentCategory.ANDROID: _score_patterns(combined_text, _ANDROID_PATTERNS),
        AgentCategory.WEB: _score_patterns(combined_text, _WEB_PATTERNS),
    }

    # Find highest scoring category
    best_category = max(scores, key=lambda k: scores[k])
    best_score = scores[best_category]

    # Require minimum confidence (at least 2 pattern matches)
    selected = AgentCategory.GENERAL if best_score < 2 else best_category

    logger.debug(
        "Agent routing decision",
        selected_agent=selected,
        scores=scores,
        text_preview=combined_text[:100],
    )
    return selected


def get_agent_system_prompt(agent: str) -> str | None:
    """Get a specialized system prompt for the selected agent.

    Args:
        agent: The agent category.

    Returns:
        System prompt string or None for default.
    """
    prompts: dict[str, str] = {
        AgentCategory.CODING: (
            "You are Sona's Coding Agent — an expert software engineer. "
            "Write clean, well-structured, production-quality code. "
            "Include type hints, docstrings, and handle edge cases. "
            "Explain your approach concisely."
        ),
        AgentCategory.RESEARCH: (
            "You are Sona's Research Agent — an expert analyst. "
            "Provide thorough, accurate, and well-structured analysis. "
            "Cite sources when relevant and present balanced perspectives."
        ),
        AgentCategory.PLANNER: (
            "You are Sona's Planner Agent — an expert project planner. "
            "Create clear, actionable plans with concrete steps, timelines, "
            "and priorities. Structure output for easy execution."
        ),
        AgentCategory.ANDROID: (
            "You are Sona's Android Agent — an expert Android developer. "
            "Write modern Kotlin with Jetpack Compose, follow Material Design "
            "guidelines, and use best practices for Android architecture."
        ),
        AgentCategory.WEB: (
            "You are Sona's Web Agent — an expert web developer. "
            "Build responsive, accessible, and performant web applications. "
            "Follow modern best practices for frontend and backend web development."
        ),
    }
    return prompts.get(agent)
