"""Confidence scoring for intent classification.

Scores classification confidence based on keyword match strength,
ambiguity detection, and contextual signals.
"""

import structlog

logger = structlog.get_logger(__name__)


class ConfidenceScorer:
    """Scores classification confidence based on multiple signals.

    Combines keyword match density, pattern specificity, and ambiguity
    detection to produce a confidence score between 0.0 and 1.0.
    """

    def __init__(
        self,
        base_weight: float = 0.6,
        specificity_weight: float = 0.25,
        ambiguity_penalty: float = 0.3,
    ) -> None:
        """Initialize the confidence scorer.

        Args:
            base_weight: Weight for keyword match density signal.
            specificity_weight: Weight for pattern specificity signal.
            ambiguity_penalty: Penalty applied when multiple intents match.
        """
        self._base_weight = base_weight
        self._specificity_weight = specificity_weight
        self._ambiguity_penalty = ambiguity_penalty

    def score(
        self,
        match_count: int,
        total_keywords: int,
        competing_intents: int,
        content_length: int,
    ) -> float:
        """Compute confidence score from classification signals.

        Args:
            match_count: Number of keyword matches for the top intent.
            total_keywords: Total number of keywords checked.
            competing_intents: Number of other intents that also matched.
            content_length: Length of the input content in characters.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        if total_keywords == 0 or content_length == 0:
            return 0.0

        # Base signal: proportion of keywords matched
        match_density = min(match_count / max(total_keywords, 1), 1.0)
        base_score = match_density * self._base_weight

        # Specificity signal: more matches in shorter content = more specific
        specificity = min(match_count / max(content_length / 50, 1.0), 1.0)
        specificity_score = specificity * self._specificity_weight

        # Ambiguity penalty: reduce confidence when multiple intents match
        if competing_intents > 0:
            penalty = min(competing_intents * self._ambiguity_penalty, 0.5)
        else:
            penalty = 0.0

        # Combine signals
        raw_score = base_score + specificity_score - penalty

        # Boost for strong single-intent matches
        if match_count >= 3 and competing_intents == 0:
            raw_score += 0.15

        # Clamp to [0.0, 1.0]
        final_score = max(0.0, min(1.0, raw_score))

        logger.debug(
            "confidence_scored",
            match_count=match_count,
            competing_intents=competing_intents,
            raw_score=raw_score,
            final_score=final_score,
        )

        return final_score
