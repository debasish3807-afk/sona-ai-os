"""Unit tests for AgentProfile, AgentState, AgentRole, and AgentCapability."""

from sona_workforce.domain.agent import (
    AgentCapability,
    AgentProfile,
    AgentRole,
    AgentState,
)


class TestAgentRole:
    """Tests for the AgentRole enum."""

    def test_all_values(self) -> None:
        expected = {"MANAGER", "WORKER", "SPECIALIST", "REVIEWER"}
        actual = {m.name for m in AgentRole}
        assert actual == expected

    def test_string_values(self) -> None:
        assert AgentRole.MANAGER == "manager"
        assert AgentRole.WORKER == "worker"
        assert AgentRole.SPECIALIST == "specialist"
        assert AgentRole.REVIEWER == "reviewer"

    def test_is_str_enum(self) -> None:
        assert isinstance(AgentRole.MANAGER, str)

    def test_count(self) -> None:
        assert len(AgentRole) == 4


class TestAgentCapability:
    """Tests for the AgentCapability enum."""

    def test_all_values(self) -> None:
        expected = {
            "CODE_GENERATION",
            "CODE_REVIEW",
            "RESEARCH",
            "PLANNING",
            "WRITING",
            "SUMMARIZATION",
            "DATA_ANALYSIS",
            "MEMORY_MANAGEMENT",
            "KNOWLEDGE_RETRIEVAL",
            "TASK_EXECUTION",
            "DELEGATION",
            "QUALITY_REVIEW",
        }
        actual = {m.name for m in AgentCapability}
        assert actual == expected

    def test_count(self) -> None:
        assert len(AgentCapability) == 12

    def test_string_values(self) -> None:
        assert AgentCapability.CODE_GENERATION == "code_generation"
        assert AgentCapability.DELEGATION == "delegation"

    def test_is_str_enum(self) -> None:
        assert isinstance(AgentCapability.RESEARCH, str)


class TestAgentState:
    """Tests for the AgentState enum."""

    def test_all_values(self) -> None:
        expected = {
            "INITIALIZING",
            "IDLE",
            "PROCESSING",
            "DELEGATING",
            "WAITING",
            "ERROR",
            "SHUTDOWN",
        }
        actual = {m.name for m in AgentState}
        assert actual == expected

    def test_string_values(self) -> None:
        assert AgentState.INITIALIZING == "initializing"
        assert AgentState.IDLE == "idle"
        assert AgentState.PROCESSING == "processing"
        assert AgentState.ERROR == "error"
        assert AgentState.SHUTDOWN == "shutdown"

    def test_count(self) -> None:
        assert len(AgentState) == 7


class TestAgentProfile:
    """Tests for the AgentProfile dataclass."""

    def test_minimal_creation(self) -> None:
        profile = AgentProfile(
            agent_id="agent-1",
            name="Test Agent",
            agent_type="coding",
            role=AgentRole.WORKER,
            capabilities=[AgentCapability.CODE_GENERATION],
        )
        assert profile.agent_id == "agent-1"
        assert profile.name == "Test Agent"
        assert profile.agent_type == "coding"
        assert profile.role == AgentRole.WORKER

    def test_default_values(self) -> None:
        profile = AgentProfile(
            agent_id="a1",
            name="A1",
            agent_type="research",
            role=AgentRole.SPECIALIST,
            capabilities=[],
        )
        assert profile.state == AgentState.IDLE
        assert profile.max_concurrent_tasks == 3
        assert profile.priority == 5
        assert profile.active_tasks == 0
        assert profile.total_completed == 0
        assert profile.total_failed == 0
        assert profile.metadata == {}

    def test_with_all_fields(self) -> None:
        profile = AgentProfile(
            agent_id="mgr-1",
            name="Manager",
            agent_type="planner",
            role=AgentRole.MANAGER,
            capabilities=[AgentCapability.DELEGATION, AgentCapability.PLANNING],
            state=AgentState.PROCESSING,
            max_concurrent_tasks=2,
            priority=1,
            active_tasks=1,
            total_completed=10,
            total_failed=2,
            metadata={"team": "alpha"},
        )
        assert profile.state == AgentState.PROCESSING
        assert profile.max_concurrent_tasks == 2
        assert profile.priority == 1
        assert profile.active_tasks == 1
        assert profile.total_completed == 10
        assert profile.total_failed == 2
        assert profile.metadata == {"team": "alpha"}

    def test_mutable_state(self) -> None:
        profile = AgentProfile(
            agent_id="a1",
            name="A1",
            agent_type="coding",
            role=AgentRole.WORKER,
            capabilities=[],
        )
        profile.state = AgentState.PROCESSING
        assert profile.state == AgentState.PROCESSING
        profile.active_tasks += 1
        assert profile.active_tasks == 1

    def test_multiple_capabilities(self) -> None:
        caps = [
            AgentCapability.CODE_GENERATION,
            AgentCapability.CODE_REVIEW,
            AgentCapability.RESEARCH,
        ]
        profile = AgentProfile(
            agent_id="multi-1",
            name="Multi Agent",
            agent_type="coding",
            role=AgentRole.SPECIALIST,
            capabilities=caps,
        )
        assert len(profile.capabilities) == 3
        assert AgentCapability.CODE_REVIEW in profile.capabilities

    def test_metadata_is_independent(self) -> None:
        p1 = AgentProfile(
            agent_id="a1",
            name="A1",
            agent_type="coding",
            role=AgentRole.WORKER,
            capabilities=[],
        )
        p2 = AgentProfile(
            agent_id="a2",
            name="A2",
            agent_type="coding",
            role=AgentRole.WORKER,
            capabilities=[],
        )
        p1.metadata["key"] = "value"
        assert "key" not in p2.metadata
