"""Task complexity and requirements classification.

Classifies user requests by complexity and type to inform model selection
and execution planning.
"""

import re
from dataclasses import dataclass
from enum import StrEnum

import structlog

from sona_thalamus.domain.models import IntentCategory

logger = structlog.get_logger(__name__)


class TaskType(StrEnum):
    """Classification of task complexity and requirements."""

    SIMPLE = "simple"
    COMPOSITE = "composite"
    RESEARCH = "research"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    ANALYTICAL = "analytical"


@dataclass(frozen=True)
class TaskClassification:
    """Result of task classification.

    Attributes:
        task_type: The primary task type classification.
        complexity_score: Complexity score from 0.0 (trivial) to 1.0 (very complex).
        requires_tools: Whether the task likely requires tool access.
        requires_memory: Whether the task requires memory/context retrieval.
        requires_streaming: Whether the response should be streamed.
    """

    task_type: TaskType
    complexity_score: float
    requires_tools: bool
    requires_memory: bool
    requires_streaming: bool


# Patterns indicating multi-step / composite tasks
_COMPOSITE_PATTERNS: list[str] = [
    r"\band\s+then\b",
    r"\bfirst\b.*\bthen\b",
    r"\bstep\s+\d+\b",
    r"\bmulti.?step\b",
    r"\bcomplex\b",
    r"\bplan\b",
    r"\bbreak\s+down\b",
]

# Patterns indicating creative tasks
_CREATIVE_PATTERNS: list[str] = [
    r"\bwrite\s+a\s+story\b",
    r"\bcreative\b",
    r"\bimagine\b",
    r"\bbrainstorm\b",
    r"\bgenerate\s+ideas\b",
    r"\bpoem\b",
    r"\bfiction\b",
    r"\bdesign\b",
]

# Patterns indicating analytical tasks
_ANALYTICAL_PATTERNS: list[str] = [
    r"\banalyze\b",
    r"\bcompare\s+and\s+contrast\b",
    r"\bevaluate\b",
    r"\bassess\b",
    r"\bcritique\b",
    r"\bpros?\s+and\s+cons?\b",
    r"\btrade.?off\b",
    r"\breason\b",
    r"\blogic\b",
]


class TaskClassifier:
    """Classifies task complexity and type from content and intent.

    Uses pattern matching and intent-based heuristics to determine
    the nature of a task for downstream model selection and planning.
    """

    def __init__(self) -> None:
        """Initialize the task classifier with pre-compiled patterns."""
        self._composite_patterns = [re.compile(p, re.IGNORECASE) for p in _COMPOSITE_PATTERNS]
        self._creative_patterns = [re.compile(p, re.IGNORECASE) for p in _CREATIVE_PATTERNS]
        self._analytical_patterns = [re.compile(p, re.IGNORECASE) for p in _ANALYTICAL_PATTERNS]

    def classify(self, content: str, intent: IntentCategory) -> TaskClassification:
        """Classify the task type and complexity.

        Args:
            content: The user input text.
            intent: The classified intent category.

        Returns:
            TaskClassification with type, complexity, and requirements.
        """
        if not content.strip():
            return TaskClassification(
                task_type=TaskType.SIMPLE,
                complexity_score=0.0,
                requires_tools=False,
                requires_memory=False,
                requires_streaming=True,
            )

        # Check composite patterns
        composite_matches = sum(1 for p in self._composite_patterns if p.search(content))
        creative_matches = sum(1 for p in self._creative_patterns if p.search(content))
        analytical_matches = sum(1 for p in self._analytical_patterns if p.search(content))

        # Intent-based primary classification
        task_type = self._intent_to_task_type(intent)

        # Override with pattern-based classification if stronger signals
        if composite_matches >= 2:
            task_type = TaskType.COMPOSITE
        elif creative_matches >= 2:
            task_type = TaskType.CREATIVE
        elif analytical_matches >= 2:
            task_type = TaskType.ANALYTICAL

        # Calculate complexity
        complexity = self._compute_complexity(
            content=content,
            composite_matches=composite_matches,
            intent=intent,
        )

        # Determine requirements
        requires_tools = intent in (IntentCategory.CODE, IntentCategory.AUTOMATION)
        requires_memory = intent == IntentCategory.MEMORY or "remember" in content.lower()
        requires_streaming = task_type in (TaskType.SIMPLE, TaskType.CREATIVE)

        classification = TaskClassification(
            task_type=task_type,
            complexity_score=complexity,
            requires_tools=requires_tools,
            requires_memory=requires_memory,
            requires_streaming=requires_streaming,
        )

        logger.debug(
            "task_classified",
            task_type=str(task_type),
            complexity=complexity,
            requires_tools=requires_tools,
        )

        return classification

    def _intent_to_task_type(self, intent: IntentCategory) -> TaskType:
        """Map intent category to default task type."""
        mapping: dict[IntentCategory, TaskType] = {
            IntentCategory.CHAT: TaskType.SIMPLE,
            IntentCategory.CODE: TaskType.TECHNICAL,
            IntentCategory.RESEARCH: TaskType.RESEARCH,
            IntentCategory.AUTOMATION: TaskType.COMPOSITE,
            IntentCategory.MEMORY: TaskType.SIMPLE,
            IntentCategory.SYSTEM: TaskType.SIMPLE,
        }
        return mapping.get(intent, TaskType.SIMPLE)

    def _compute_complexity(
        self,
        content: str,
        composite_matches: int,
        intent: IntentCategory,
    ) -> float:
        """Compute a complexity score from 0.0 to 1.0."""
        score = 0.0

        # Length contributes to complexity
        word_count = len(content.split())
        if word_count > 50:
            score += 0.3
        elif word_count > 20:
            score += 0.15

        # Composite signals
        score += min(composite_matches * 0.15, 0.4)

        # Intent-based complexity
        if intent in (IntentCategory.CODE, IntentCategory.AUTOMATION):
            score += 0.2
        elif intent == IntentCategory.RESEARCH:
            score += 0.15

        return min(score, 1.0)
