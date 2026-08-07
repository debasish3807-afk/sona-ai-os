"""Unit tests for the IntentClassifier."""

from sona_thalamus.domain.models import IntentCategory
from sona_thalamus.infrastructure.intent_classifier import IntentClassifier


class TestIntentClassifier:
    """Tests for rule-based intent classification."""

    def setup_method(self) -> None:
        """Create a fresh classifier for each test."""
        self.classifier = IntentClassifier()

    def test_code_intent_keywords(self) -> None:
        """Test code intent detection with various keywords."""
        intent, confidence = self.classifier.classify("Please write code for a sorting algorithm")
        assert intent == IntentCategory.CODE
        assert confidence > 0.0

    def test_code_intent_debug(self) -> None:
        """Test code intent with debug keyword."""
        intent, _ = self.classifier.classify("Debug this function please")
        assert intent == IntentCategory.CODE

    def test_code_intent_refactor(self) -> None:
        """Test code intent with refactor keyword."""
        intent, _ = self.classifier.classify("Refactor the class to use dependency injection")
        assert intent == IntentCategory.CODE

    def test_research_intent_keywords(self) -> None:
        """Test research intent detection."""
        intent, confidence = self.classifier.classify(
            "What is quantum computing? Explain it to me."
        )
        assert intent == IntentCategory.RESEARCH
        assert confidence > 0.0

    def test_research_intent_search(self) -> None:
        """Test research intent with search keyword."""
        intent, _ = self.classifier.classify("Search for the latest AI research papers")
        assert intent == IntentCategory.RESEARCH

    def test_automation_intent_keywords(self) -> None:
        """Test automation intent detection."""
        intent, confidence = self.classifier.classify("Schedule a workflow to run every day")
        assert intent == IntentCategory.AUTOMATION
        assert confidence > 0.0

    def test_memory_intent_keywords(self) -> None:
        """Test memory intent detection."""
        intent, confidence = self.classifier.classify("Remember that I prefer dark mode")
        assert intent == IntentCategory.MEMORY
        assert confidence > 0.0

    def test_memory_intent_recall(self) -> None:
        """Test memory intent with recall keyword."""
        intent, _ = self.classifier.classify("Recall what we discussed last time")
        assert intent == IntentCategory.MEMORY

    def test_system_intent_keywords(self) -> None:
        """Test system intent detection."""
        intent, confidence = self.classifier.classify("Check the system status and health")
        assert intent == IntentCategory.SYSTEM
        assert confidence > 0.0

    def test_chat_fallback(self) -> None:
        """Test that unrecognized content falls back to CHAT."""
        intent, confidence = self.classifier.classify("Hello, how are you today?")
        assert intent == IntentCategory.CHAT
        assert confidence == 0.0

    def test_empty_content(self) -> None:
        """Test classification of empty content."""
        intent, confidence = self.classifier.classify("")
        assert intent == IntentCategory.CHAT
        assert confidence == 0.0

    def test_whitespace_only(self) -> None:
        """Test classification of whitespace-only content."""
        intent, confidence = self.classifier.classify("   \n\t  ")
        assert intent == IntentCategory.CHAT
        assert confidence == 0.0

    def test_multiple_keyword_confidence(self) -> None:
        """Test that multiple matches increase confidence."""
        _, confidence_single = self.classifier.classify("implement it")
        _, confidence_multi = self.classifier.classify(
            "implement a function class with the algorithm"
        )
        assert confidence_multi >= confidence_single

    def test_case_insensitive(self) -> None:
        """Test that classification is case-insensitive."""
        intent, _ = self.classifier.classify("IMPLEMENT a new FUNCTION")
        assert intent == IntentCategory.CODE
