"""Unit tests for the ConfidenceScorer."""

from sona_thalamus.infrastructure.confidence_scorer import ConfidenceScorer


class TestConfidenceScorer:
    """Tests for confidence scoring logic."""

    def setup_method(self) -> None:
        """Create a fresh scorer for each test."""
        self.scorer = ConfidenceScorer()

    def test_zero_matches_zero_confidence(self) -> None:
        """Test that zero matches produce zero confidence."""
        score = self.scorer.score(
            match_count=0,
            total_keywords=10,
            competing_intents=0,
            content_length=50,
        )
        assert score == 0.0

    def test_high_matches_high_confidence(self) -> None:
        """Test that many matches produce high confidence."""
        score = self.scorer.score(
            match_count=5,
            total_keywords=10,
            competing_intents=0,
            content_length=50,
        )
        assert score > 0.5

    def test_competing_intents_reduce_confidence(self) -> None:
        """Test that competing intents reduce confidence."""
        score_no_compete = self.scorer.score(
            match_count=3,
            total_keywords=10,
            competing_intents=0,
            content_length=100,
        )
        score_with_compete = self.scorer.score(
            match_count=3,
            total_keywords=10,
            competing_intents=2,
            content_length=100,
        )
        assert score_with_compete < score_no_compete

    def test_confidence_clamped_to_one(self) -> None:
        """Test that confidence never exceeds 1.0."""
        score = self.scorer.score(
            match_count=100,
            total_keywords=10,
            competing_intents=0,
            content_length=10,
        )
        assert score <= 1.0

    def test_confidence_never_negative(self) -> None:
        """Test that confidence never goes below 0.0."""
        score = self.scorer.score(
            match_count=1,
            total_keywords=100,
            competing_intents=5,
            content_length=1000,
        )
        assert score >= 0.0

    def test_zero_total_keywords(self) -> None:
        """Test edge case with zero total keywords."""
        score = self.scorer.score(
            match_count=1,
            total_keywords=0,
            competing_intents=0,
            content_length=50,
        )
        assert score == 0.0

    def test_zero_content_length(self) -> None:
        """Test edge case with zero content length."""
        score = self.scorer.score(
            match_count=1,
            total_keywords=10,
            competing_intents=0,
            content_length=0,
        )
        assert score == 0.0

    def test_strong_single_intent_boost(self) -> None:
        """Test boost for strong single-intent matches (3+ matches, no competition)."""
        score_weak = self.scorer.score(
            match_count=2,
            total_keywords=10,
            competing_intents=0,
            content_length=100,
        )
        score_strong = self.scorer.score(
            match_count=3,
            total_keywords=10,
            competing_intents=0,
            content_length=100,
        )
        # Strong match gets a boost
        assert score_strong > score_weak

    def test_custom_weights(self) -> None:
        """Test scorer with custom weights."""
        scorer = ConfidenceScorer(
            base_weight=0.8,
            specificity_weight=0.1,
            ambiguity_penalty=0.5,
        )
        score = scorer.score(
            match_count=3,
            total_keywords=10,
            competing_intents=0,
            content_length=100,
        )
        assert 0.0 <= score <= 1.0

    def test_specificity_signal(self) -> None:
        """Test that shorter content with matches has higher specificity."""
        score_short = self.scorer.score(
            match_count=2,
            total_keywords=10,
            competing_intents=0,
            content_length=30,
        )
        score_long = self.scorer.score(
            match_count=2,
            total_keywords=10,
            competing_intents=0,
            content_length=500,
        )
        assert score_short >= score_long
