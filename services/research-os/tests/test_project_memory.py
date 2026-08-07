"""Tests for project memory."""

import pytest

from sona_research.infrastructure.knowledge_graph.runtime import KnowledgeGraphRuntime
from sona_research.infrastructure.project_memory import (
    BugSeverity,
    FeatureStatus,
    ProjectMemory,
)


@pytest.fixture
def kg() -> KnowledgeGraphRuntime:
    return KnowledgeGraphRuntime()


@pytest.fixture
def pm(kg: KnowledgeGraphRuntime) -> ProjectMemory:
    return ProjectMemory(kg)


class TestProjectMemoryADRs:
    @pytest.mark.asyncio
    async def test_add_adr(self, pm: ProjectMemory) -> None:
        adr = await pm.add_adr("Use PostgreSQL", "Need ACID", "Use Postgres")
        assert adr.title == "Use PostgreSQL"
        assert adr.context == "Need ACID"
        assert adr.decision == "Use Postgres"
        assert adr.adr_id.startswith("adr-")

    @pytest.mark.asyncio
    async def test_get_adr(self, pm: ProjectMemory) -> None:
        adr = await pm.add_adr("Test", "Ctx", "Dec")
        retrieved = await pm.get_adr(adr.adr_id)
        assert retrieved is not None
        assert retrieved.title == "Test"

    @pytest.mark.asyncio
    async def test_list_adrs(self, pm: ProjectMemory) -> None:
        await pm.add_adr("A", "c", "d")
        await pm.add_adr("B", "c", "d")
        adrs = await pm.list_adrs()
        assert len(adrs) == 2

    @pytest.mark.asyncio
    async def test_adr_added_to_graph(self, pm: ProjectMemory, kg: KnowledgeGraphRuntime) -> None:
        adr = await pm.add_adr("Graph Test", "C", "D")
        node = await kg.get_node(f"adr:{adr.adr_id}")
        assert node is not None
        assert node.node_type == "decision"


class TestProjectMemoryFeatures:
    @pytest.mark.asyncio
    async def test_add_feature(self, pm: ProjectMemory) -> None:
        feat = await pm.add_feature("Auth System", "OAuth2 implementation")
        assert feat.title == "Auth System"
        assert feat.status == FeatureStatus.PLANNED

    @pytest.mark.asyncio
    async def test_update_feature_status(self, pm: ProjectMemory) -> None:
        feat = await pm.add_feature("F")
        updated = await pm.update_feature_status(feat.feature_id, FeatureStatus.IN_PROGRESS)
        assert updated is not None
        assert updated.status == FeatureStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_list_features_by_status(self, pm: ProjectMemory) -> None:
        await pm.add_feature("A")
        f2 = await pm.add_feature("B")
        await pm.update_feature_status(f2.feature_id, FeatureStatus.DONE)
        planned = await pm.list_features(FeatureStatus.PLANNED)
        assert len(planned) == 1

    @pytest.mark.asyncio
    async def test_feature_added_to_graph(
        self, pm: ProjectMemory, kg: KnowledgeGraphRuntime
    ) -> None:
        feat = await pm.add_feature("Graph Feat")
        node = await kg.get_node(f"feature:{feat.feature_id}")
        assert node is not None


class TestProjectMemoryBugs:
    @pytest.mark.asyncio
    async def test_add_bug(self, pm: ProjectMemory) -> None:
        bug = await pm.add_bug("Login crash", severity=BugSeverity.CRITICAL)
        assert bug.title == "Login crash"
        assert bug.severity == BugSeverity.CRITICAL
        assert bug.status == "open"

    @pytest.mark.asyncio
    async def test_fix_bug(self, pm: ProjectMemory) -> None:
        bug = await pm.add_bug("B")
        fixed = await pm.fix_bug(bug.bug_id)
        assert fixed is not None
        assert fixed.status == "fixed"

    @pytest.mark.asyncio
    async def test_list_bugs_by_status(self, pm: ProjectMemory) -> None:
        await pm.add_bug("Open")
        b2 = await pm.add_bug("Fixed")
        await pm.fix_bug(b2.bug_id)
        open_bugs = await pm.list_bugs("open")
        assert len(open_bugs) == 1

    @pytest.mark.asyncio
    async def test_bug_added_to_graph(self, pm: ProjectMemory, kg: KnowledgeGraphRuntime) -> None:
        bug = await pm.add_bug("Graph Bug")
        node = await kg.get_node(f"bug:{bug.bug_id}")
        assert node is not None


class TestProjectMemoryTodos:
    @pytest.mark.asyncio
    async def test_add_todo(self, pm: ProjectMemory) -> None:
        text = await pm.add_todo("Refactor auth module")
        assert text == "Refactor auth module"

    @pytest.mark.asyncio
    async def test_list_todos(self, pm: ProjectMemory) -> None:
        await pm.add_todo("A")
        await pm.add_todo("B")
        todos = await pm.list_todos()
        assert len(todos) == 2

    @pytest.mark.asyncio
    async def test_remove_todo(self, pm: ProjectMemory) -> None:
        await pm.add_todo("Remove me")
        removed = await pm.remove_todo("Remove me")
        assert removed is True
        assert len(await pm.list_todos()) == 0

    @pytest.mark.asyncio
    async def test_remove_nonexistent(self, pm: ProjectMemory) -> None:
        assert await pm.remove_todo("nope") is False


class TestProjectMemoryMilestones:
    @pytest.mark.asyncio
    async def test_add_milestone(self, pm: ProjectMemory) -> None:
        ms = await pm.add_milestone("v1.0 Release", due_date="2024-12-01")
        assert ms.title == "v1.0 Release"
        assert ms.completed is False

    @pytest.mark.asyncio
    async def test_complete_milestone(self, pm: ProjectMemory) -> None:
        ms = await pm.add_milestone("MS")
        completed = await pm.complete_milestone(ms.milestone_id)
        assert completed is not None
        assert completed.completed is True

    @pytest.mark.asyncio
    async def test_list_milestones(self, pm: ProjectMemory) -> None:
        await pm.add_milestone("A")
        ms2 = await pm.add_milestone("B")
        await pm.complete_milestone(ms2.milestone_id)
        incomplete = await pm.list_milestones(completed=False)
        assert len(incomplete) == 1

    @pytest.mark.asyncio
    async def test_milestone_with_features(self, pm: ProjectMemory) -> None:
        f = await pm.add_feature("F1")
        ms = await pm.add_milestone("MS", features=[f.feature_id])
        assert f.feature_id in ms.features


class TestProjectMemorySummary:
    @pytest.mark.asyncio
    async def test_get_summary(self, pm: ProjectMemory) -> None:
        await pm.add_adr("A", "c", "d")
        await pm.add_feature("F")
        await pm.add_bug("B")
        await pm.add_todo("T")
        await pm.add_milestone("M")
        summary = await pm.get_summary()
        assert summary["adrs"] == 1
        assert summary["features"] == 1
        assert summary["bugs"] == 1
        assert summary["todos"] == 1
        assert summary["milestones"] == 1
        assert summary["open_bugs"] == 1
        assert summary["planned_features"] == 1
