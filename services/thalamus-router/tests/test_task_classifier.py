"""Unit tests for the TaskClassifier."""

import pytest
from sona_thalamus.domain.models import IntentCategory
from sona_thalamus.infrastructure.task_classifier import (
    TaskClassifier,
    TaskType,
)


class TestTaskClassifier:
    """Tests for task complexity and type classification."""

    def setup_method(self) -> None:
        """Create a fresh classifier for each test."""
        self.classifier = TaskClassifier()

    def test_simple_chat_task(self) -> None:
        """Test simple chat messages classified as SIMPLE."""
        result = self.classifier.classify("Hello there", IntentCategory.CHAT)
        assert result.task_type == TaskType.SIMPLE
        assert result.complexity_score < 0.5

    def test_technical_code_task(self) -> None:
        """Test code intent classified as TECHNICAL."""
        result = self.classifier.classify("Implement a binary search", IntentCategory.CODE)
        assert result.task_type == TaskType.TECHNICAL

    def test_research_task(self) -> None:
        """Test research intent classified as RESEARCH."""
        result = self.classifier.classify("Find information about AI", IntentCategory.RESEARCH)
        assert result.task_type == TaskType.RESEARCH

    def test_composite_task_detection(self) -> None:
        """Test composite task detection from patterns."""
        content = "First do step 1, and then do step 2, break down the problem"
        result = self.classifier.classify(content, IntentCategory.CHAT)
        assert result.task_type == TaskType.COMPOSITE

    def test_creative_task_detection(self) -> None:
        """Test creative task detection from patterns."""
        content = "Write a story and brainstorm some creative ideas for fiction"
        result = self.classifier.classify(content, IntentCategory.CHAT)
        assert result.task_type == TaskType.CREATIVE

    def test_analytical_task_detection(self) -> None:
        """Test analytical task detection from patterns."""
        content = "Analyze and evaluate the trade-offs between these approaches"
        result = self.classifier.classify(content, IntentCategory.CHAT)
        assert result.task_type == TaskType.ANALYTICAL

    def test_requires_tools_for_code(self) -> None:
        """Test that code tasks require tools."""
        result = self.classifier.classify("Write a function", IntentCategory.CODE)
        assert result.requires_tools is True

    def test_requires_tools_for_automation(self) -> None:
        """Test that automation tasks require tools."""
        result = self.classifier.classify("Automate this", IntentCategory.AUTOMATION)
        assert result.requires_tools is True

    def test_no_tools_for_chat(self) -> None:
        """Test that chat tasks don't require tools."""
        result = self.classifier.classify("Hello", IntentCategory.CHAT)
        assert result.requires_tools is False

    def test_requires_memory(self) -> None:
        """Test memory requirement detection."""
        result = self.classifier.classify("What did I say?", IntentCategory.MEMORY)
        assert result.requires_memory is True

    def test_complexity_increases_with_length(self) -> None:
        """Test that longer content has higher complexity."""
        short = self.classifier.classify("Do it", IntentCategory.CODE)
        long_content = "Please implement " + " ".join(["a complex"] * 30) + " system"
        long_result = self.classifier.classify(long_content, IntentCategory.CODE)
        assert long_result.complexity_score >= short.complexity_score

    def test_empty_content(self) -> None:
        """Test empty content classification."""
        result = self.classifier.classify("", IntentCategory.CHAT)
        assert result.task_type == TaskType.SIMPLE
        assert result.complexity_score == 0.0

    def test_streaming_for_simple_tasks(self) -> None:
        """Test streaming is enabled for simple tasks."""
        result = self.classifier.classify("Hello", IntentCategory.CHAT)
        assert result.requires_streaming is True

    def test_classification_result_is_frozen(self) -> None:
        """Test that TaskClassification is immutable."""
        result = self.classifier.classify("Hello", IntentCategory.CHAT)
        with pytest.raises((TypeError, AttributeError)):
            result.task_type = TaskType.COMPOSITE  # type: ignore[misc]
