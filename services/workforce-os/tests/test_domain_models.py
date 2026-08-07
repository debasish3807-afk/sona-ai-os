"""Unit tests for Workforce OS domain models.

Tests verify that all domain models, enums, and dataclasses are correctly
defined, instantiate properly, and enforce immutability.
"""

from dataclasses import FrozenInstanceError

import pytest

from sona_workforce.domain.models import (
    AgentResult,
    AgentStatus,
    AgentTask,
    AgentType,
)


class TestAgentType:
    """Tests for the AgentType enum."""

    def test_all_values_defined(self) -> None:
        """Verify all required agent types exist."""
        expected = {
            "CODING",
            "RESEARCH",
            "PLANNER",
            "AUTOMATION",
            "COMMUNICATION",
            "SYSTEM",
            "VOICE",
            "VISION",
            "WEB",
            "ANDROID",
            "CUSTOM",
        }
        actual = {member.name for member in AgentType}
        assert actual == expected

    def test_string_values(self) -> None:
        """Verify enum values are lowercase strings."""
        assert AgentType.CODING == "coding"
        assert AgentType.RESEARCH == "research"
        assert AgentType.PLANNER == "planner"
        assert AgentType.AUTOMATION == "automation"
        assert AgentType.COMMUNICATION == "communication"
        assert AgentType.SYSTEM == "system"
        assert AgentType.VOICE == "voice"
        assert AgentType.VISION == "vision"
        assert AgentType.WEB == "web"
        assert AgentType.ANDROID == "android"
        assert AgentType.CUSTOM == "custom"

    def test_is_str_enum(self) -> None:
        """Verify AgentType is a StrEnum and can be used as string."""
        assert isinstance(AgentType.CODING, str)
        assert f"Agent: {AgentType.CODING}" == "Agent: coding"

    def test_total_count(self) -> None:
        """Verify the correct number of agent types."""
        assert len(AgentType) == 11


class TestAgentStatus:
    """Tests for the AgentStatus enum."""

    def test_all_values_defined(self) -> None:
        """Verify all required agent statuses exist."""
        expected = {"IDLE", "BUSY", "ERROR", "STOPPED"}
        actual = {member.name for member in AgentStatus}
        assert actual == expected

    def test_string_values(self) -> None:
        """Verify enum values are lowercase strings."""
        assert AgentStatus.IDLE == "idle"
        assert AgentStatus.BUSY == "busy"
        assert AgentStatus.ERROR == "error"
        assert AgentStatus.STOPPED == "stopped"

    def test_is_str_enum(self) -> None:
        """Verify AgentStatus is a StrEnum and can be used as string."""
        assert isinstance(AgentStatus.IDLE, str)
        assert f"Status: {AgentStatus.BUSY}" == "Status: busy"

    def test_total_count(self) -> None:
        """Verify the correct number of agent statuses."""
        assert len(AgentStatus) == 4


class TestAgentTask:
    """Tests for the AgentTask frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        task = AgentTask(
            task_id="task-001",
            agent_type=AgentType.CODING,
            instruction="Write a Python function",
        )
        assert task.task_id == "task-001"
        assert task.agent_type == AgentType.CODING
        assert task.instruction == "Write a Python function"

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.RESEARCH,
            instruction="Search for info",
        )
        assert task.context is None
        assert task.timeout_seconds == 120
        assert task.priority == 5

    def test_with_all_fields(self) -> None:
        """Create with all optional fields."""
        context = {"project": "sona", "language": "python"}
        task = AgentTask(
            task_id="task-abc",
            agent_type=AgentType.PLANNER,
            instruction="Plan the project structure",
            context=context,
            timeout_seconds=300,
            priority=1,
        )
        assert task.context == context
        assert task.timeout_seconds == 300
        assert task.priority == 1

    def test_is_frozen(self) -> None:
        """Verify AgentTask is immutable."""
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.SYSTEM,
            instruction="Check health",
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            task.task_id = "changed"  # type: ignore[misc]

    def test_agent_type_is_enum_value(self) -> None:
        """Verify agent_type stores proper enum value."""
        task = AgentTask(
            task_id="t1",
            agent_type=AgentType.VOICE,
            instruction="Process speech",
        )
        assert task.agent_type is AgentType.VOICE
        assert task.agent_type == "voice"


class TestAgentResult:
    """Tests for the AgentResult frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create result with required fields only."""
        result = AgentResult(
            task_id="task-001",
            agent_type=AgentType.CODING,
            output="def hello(): pass",
            status="success",
        )
        assert result.task_id == "task-001"
        assert result.agent_type == AgentType.CODING
        assert result.output == "def hello(): pass"
        assert result.status == "success"

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        result = AgentResult(
            task_id="t1",
            agent_type=AgentType.RESEARCH,
            output="Found 5 results",
            status="success",
        )
        assert result.tokens_used == 0
        assert result.duration_ms == 0.0
        assert result.artifacts is None

    def test_with_all_fields(self) -> None:
        """Create result with all optional fields."""
        artifacts = [{"type": "file", "path": "/tmp/output.py"}]
        result = AgentResult(
            task_id="task-xyz",
            agent_type=AgentType.AUTOMATION,
            output="Workflow executed successfully",
            status="success",
            tokens_used=1500,
            duration_ms=2500.5,
            artifacts=artifacts,
        )
        assert result.tokens_used == 1500
        assert result.duration_ms == 2500.5
        assert result.artifacts == artifacts

    def test_is_frozen(self) -> None:
        """Verify AgentResult is immutable."""
        result = AgentResult(
            task_id="t1",
            agent_type=AgentType.WEB,
            output="Page scraped",
            status="success",
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            result.output = "changed"  # type: ignore[misc]

    def test_error_status(self) -> None:
        """Verify result can represent an error state."""
        result = AgentResult(
            task_id="t-err",
            agent_type=AgentType.VISION,
            output="",
            status="error",
            tokens_used=50,
            duration_ms=100.0,
        )
        assert result.status == "error"
        assert result.output == ""
        assert result.tokens_used == 50
