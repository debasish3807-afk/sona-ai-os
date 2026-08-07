"""Rule-based intent classification using keyword matching.

Classifies user input into IntentCategory values using pattern matching
with confidence scoring. This is a CPU-bound, synchronous classifier
suitable for low-latency routing decisions.
"""

import re

import structlog

from sona_thalamus.domain.models import IntentCategory
from sona_thalamus.infrastructure.confidence_scorer import ConfidenceScorer

logger = structlog.get_logger(__name__)

# Keyword patterns for each intent category
_INTENT_PATTERNS: dict[IntentCategory, list[str]] = {
    IntentCategory.CODE: [
        r"\bwrite\s+code\b",
        r"\bimplement\b",
        r"\bdebug\b",
        r"\brefactor\b",
        r"\bfunction\b",
        r"\bclass\b",
        r"\balgorithm\b",
        r"\bcompile\b",
        r"\bsyntax\b",
        r"\bprogram\b",
        r"\bcode\b",
        r"\bbug\s*fix\b",
        r"\btest\s+case\b",
        r"\bunit\s+test\b",
        r"\bapi\s+endpoint\b",
    ],
    IntentCategory.RESEARCH: [
        r"\bsearch\b",
        r"\bfind\b",
        r"\blook\s+up\b",
        r"\bwhat\s+is\b",
        r"\bexplain\b",
        r"\bsummarize\b",
        r"\bresearch\b",
        r"\bcompare\b",
        r"\banalyze\b",
        r"\binvestigate\b",
        r"\bhow\s+does\b",
        r"\bwhy\s+does\b",
        r"\btell\s+me\s+about\b",
    ],
    IntentCategory.AUTOMATION: [
        r"\bschedule\b",
        r"\bautomate\b",
        r"\bworkflow\b",
        r"\btrigger\b",
        r"\bcron\b",
        r"\bevery\s+day\b",
        r"\bevery\s+hour\b",
        r"\brepeat\b",
        r"\bpipeline\b",
        r"\bbatch\b",
        r"\brun\s+automatically\b",
    ],
    IntentCategory.MEMORY: [
        r"\bremember\b",
        r"\brecall\b",
        r"\bforget\b",
        r"\bhistory\b",
        r"\blast\s+time\b",
        r"\bpreviously\b",
        r"\bearlier\b",
        r"\bsave\s+this\b",
        r"\bnote\s+that\b",
        r"\bdon'?t\s+forget\b",
    ],
    IntentCategory.SYSTEM: [
        r"\bsettings\b",
        r"\bconfigure\b",
        r"\bstatus\b",
        r"\bhealth\b",
        r"\bversion\b",
        r"\bupdate\b",
        r"\bpreference\b",
        r"\breset\b",
        r"\bdiagnostic\b",
        r"\bsystem\s+info\b",
    ],
}


class IntentClassifier:
    """Rule-based intent classifier using keyword pattern matching.

    Classifies user input text into an IntentCategory by matching against
    predefined keyword patterns. Falls back to CHAT when no patterns match
    or confidence is too low.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.15,
        scorer: ConfidenceScorer | None = None,
    ) -> None:
        """Initialize the intent classifier.

        Args:
            confidence_threshold: Minimum confidence to accept a classification.
            scorer: Optional ConfidenceScorer instance (creates default if None).
        """
        self._confidence_threshold = confidence_threshold
        self._scorer = scorer or ConfidenceScorer()
        # Pre-compile all patterns
        self._compiled_patterns: dict[IntentCategory, list[re.Pattern[str]]] = {
            intent: [re.compile(p, re.IGNORECASE) for p in patterns]
            for intent, patterns in _INTENT_PATTERNS.items()
        }

    def classify(self, content: str) -> tuple[IntentCategory, float]:
        """Classify the intent of the given content.

        Args:
            content: The user input text to classify.

        Returns:
            Tuple of (classified IntentCategory, confidence score).
        """
        if not content or not content.strip():
            return IntentCategory.CHAT, 0.0

        # Count matches for each intent
        match_counts: dict[IntentCategory, int] = {}
        for intent, patterns in self._compiled_patterns.items():
            count = sum(1 for p in patterns if p.search(content))
            if count > 0:
                match_counts[intent] = count

        # No matches → default to CHAT
        if not match_counts:
            logger.debug("intent_classified", intent="chat", confidence=0.0, reason="no_matches")
            return IntentCategory.CHAT, 0.0

        # Find top intent
        top_intent = max(match_counts, key=lambda k: match_counts[k])
        top_count = match_counts[top_intent]
        competing = len(match_counts) - 1

        # Calculate total keywords for the top intent
        total_keywords = len(self._compiled_patterns[top_intent])

        # Score confidence
        confidence = self._scorer.score(
            match_count=top_count,
            total_keywords=total_keywords,
            competing_intents=competing,
            content_length=len(content),
        )

        # Apply threshold
        if confidence < self._confidence_threshold:
            logger.debug(
                "intent_classified",
                intent="chat",
                confidence=confidence,
                reason="below_threshold",
            )
            return IntentCategory.CHAT, confidence

        logger.debug(
            "intent_classified",
            intent=str(top_intent),
            confidence=confidence,
            match_count=top_count,
            competing=competing,
        )

        return top_intent, confidence
