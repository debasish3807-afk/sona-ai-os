"""Project memory for tracking project-level knowledge.

Tracks architecture decisions (ADRs), features, bugs, TODOs,
and milestones. Integrates with the knowledge graph.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

import structlog

from sona_research.domain.personal_models import KnowledgeEdge, KnowledgeNode
from sona_research.infrastructure.knowledge_graph.runtime import KnowledgeGraphRuntime

logger = structlog.get_logger()


class FeatureStatus(StrEnum):
    """Status of a project feature."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    DEFERRED = "deferred"


class BugSeverity(StrEnum):
    """Severity of a bug."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class ArchitectureDecision:
    """An architecture decision record (ADR)."""

    adr_id: str
    title: str
    context: str
    decision: str
    consequences: str = ""
    status: str = "accepted"
    created_at: str = ""


@dataclass(frozen=True)
class Feature:
    """A project feature."""

    feature_id: str
    title: str
    description: str = ""
    status: FeatureStatus = FeatureStatus.PLANNED
    assignee: str = ""
    created_at: str = ""


@dataclass(frozen=True)
class Bug:
    """A tracked bug."""

    bug_id: str
    title: str
    description: str = ""
    severity: BugSeverity = BugSeverity.MEDIUM
    status: str = "open"
    assignee: str = ""
    created_at: str = ""


@dataclass(frozen=True)
class Milestone:
    """A project milestone."""

    milestone_id: str
    title: str
    description: str = ""
    due_date: str = ""
    completed: bool = False
    features: list[str] = field(default_factory=list)


class ProjectMemory:
    """Track project-level knowledge and integrate with knowledge graph.

    Manages architecture decisions, features, bugs, TODOs, and milestones,
    connecting them in the knowledge graph for relationship tracking.
    """

    def __init__(self, knowledge_graph: KnowledgeGraphRuntime) -> None:
        """Initialize project memory with a knowledge graph.

        Args:
            knowledge_graph: The knowledge graph runtime for relationship tracking.
        """
        self._kg = knowledge_graph
        self._adrs: dict[str, ArchitectureDecision] = {}
        self._features: dict[str, Feature] = {}
        self._bugs: dict[str, Bug] = {}
        self._todos: list[str] = []
        self._milestones: dict[str, Milestone] = {}
        self._next_adr_id: int = 1
        self._next_feature_id: int = 1
        self._next_bug_id: int = 1
        self._next_milestone_id: int = 1

    async def add_adr(
        self,
        title: str,
        context: str,
        decision: str,
        consequences: str = "",
    ) -> ArchitectureDecision:
        """Add an architecture decision record.

        Args:
            title: Decision title.
            context: Context/problem being addressed.
            decision: The decision made.
            consequences: Consequences of the decision.

        Returns:
            The created ADR.
        """
        adr_id = f"adr-{self._next_adr_id:04d}"
        self._next_adr_id += 1

        adr = ArchitectureDecision(
            adr_id=adr_id,
            title=title,
            context=context,
            decision=decision,
            consequences=consequences,
            status="accepted",
            created_at=datetime.now(UTC).isoformat(),
        )
        self._adrs[adr_id] = adr

        # Add to knowledge graph
        node = KnowledgeNode(
            node_id=f"adr:{adr_id}",
            label=title,
            node_type="decision",
            properties={
                "context": context,
                "decision": decision,
                "consequences": consequences,
            },
        )
        await self._kg.add_node(node)

        logger.info("project_memory.adr_added", adr_id=adr_id, title=title)
        return adr

    async def get_adr(self, adr_id: str) -> ArchitectureDecision | None:
        """Get an ADR by ID."""
        return self._adrs.get(adr_id)

    async def list_adrs(self) -> list[ArchitectureDecision]:
        """List all architecture decisions."""
        return list(self._adrs.values())

    async def add_feature(
        self,
        title: str,
        description: str = "",
        assignee: str = "",
    ) -> Feature:
        """Add a project feature.

        Args:
            title: Feature title.
            description: Feature description.
            assignee: Person assigned to the feature.

        Returns:
            The created Feature.
        """
        feature_id = f"feat-{self._next_feature_id:04d}"
        self._next_feature_id += 1

        feature = Feature(
            feature_id=feature_id,
            title=title,
            description=description,
            status=FeatureStatus.PLANNED,
            assignee=assignee,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._features[feature_id] = feature

        # Add to knowledge graph
        node = KnowledgeNode(
            node_id=f"feature:{feature_id}",
            label=title,
            node_type="feature",
            properties={"description": description, "assignee": assignee},
        )
        await self._kg.add_node(node)

        logger.info("project_memory.feature_added", feature_id=feature_id)
        return feature

    async def update_feature_status(self, feature_id: str, status: FeatureStatus) -> Feature | None:
        """Update a feature's status.

        Args:
            feature_id: The feature identifier.
            status: New status.

        Returns:
            Updated feature or None if not found.
        """
        existing = self._features.get(feature_id)
        if existing is None:
            return None

        updated = Feature(
            feature_id=existing.feature_id,
            title=existing.title,
            description=existing.description,
            status=status,
            assignee=existing.assignee,
            created_at=existing.created_at,
        )
        self._features[feature_id] = updated
        return updated

    async def list_features(self, status: FeatureStatus | None = None) -> list[Feature]:
        """List features, optionally filtered by status."""
        features = list(self._features.values())
        if status is not None:
            features = [f for f in features if f.status == status]
        return features

    async def add_bug(
        self,
        title: str,
        description: str = "",
        severity: BugSeverity = BugSeverity.MEDIUM,
        assignee: str = "",
    ) -> Bug:
        """Add a tracked bug.

        Args:
            title: Bug title.
            description: Bug description.
            severity: Bug severity.
            assignee: Person assigned to fix.

        Returns:
            The created Bug.
        """
        bug_id = f"bug-{self._next_bug_id:04d}"
        self._next_bug_id += 1

        bug = Bug(
            bug_id=bug_id,
            title=title,
            description=description,
            severity=severity,
            status="open",
            assignee=assignee,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._bugs[bug_id] = bug

        # Add to knowledge graph
        node = KnowledgeNode(
            node_id=f"bug:{bug_id}",
            label=title,
            node_type="bug",
            properties={"severity": severity.value, "assignee": assignee},
        )
        await self._kg.add_node(node)

        logger.info("project_memory.bug_added", bug_id=bug_id, severity=severity.value)
        return bug

    async def fix_bug(self, bug_id: str) -> Bug | None:
        """Mark a bug as fixed.

        Args:
            bug_id: The bug identifier.

        Returns:
            Updated bug or None if not found.
        """
        existing = self._bugs.get(bug_id)
        if existing is None:
            return None

        fixed = Bug(
            bug_id=existing.bug_id,
            title=existing.title,
            description=existing.description,
            severity=existing.severity,
            status="fixed",
            assignee=existing.assignee,
            created_at=existing.created_at,
        )
        self._bugs[bug_id] = fixed
        return fixed

    async def list_bugs(self, status: str | None = None) -> list[Bug]:
        """List bugs, optionally filtered by status."""
        bugs = list(self._bugs.values())
        if status is not None:
            bugs = [b for b in bugs if b.status == status]
        return bugs

    async def add_todo(self, text: str) -> str:
        """Add a TODO item.

        Args:
            text: TODO text.

        Returns:
            The TODO text.
        """
        self._todos.append(text)
        return text

    async def list_todos(self) -> list[str]:
        """List all TODOs."""
        return list(self._todos)

    async def remove_todo(self, text: str) -> bool:
        """Remove a TODO by text.

        Args:
            text: The TODO text to remove.

        Returns:
            True if the TODO was found and removed.
        """
        if text in self._todos:
            self._todos.remove(text)
            return True
        return False

    async def add_milestone(
        self,
        title: str,
        description: str = "",
        due_date: str = "",
        features: list[str] | None = None,
    ) -> Milestone:
        """Add a project milestone.

        Args:
            title: Milestone title.
            description: Milestone description.
            due_date: Due date string.
            features: List of feature IDs linked to this milestone.

        Returns:
            The created Milestone.
        """
        milestone_id = f"ms-{self._next_milestone_id:04d}"
        self._next_milestone_id += 1

        milestone = Milestone(
            milestone_id=milestone_id,
            title=title,
            description=description,
            due_date=due_date,
            features=features or [],
        )
        self._milestones[milestone_id] = milestone

        # Add to knowledge graph
        node = KnowledgeNode(
            node_id=f"milestone:{milestone_id}",
            label=title,
            node_type="milestone",
            properties={"due_date": due_date},
        )
        await self._kg.add_node(node)

        # Link milestone to features
        for feat_id in features or []:
            feat_node_id = f"feature:{feat_id}"
            if await self._kg.get_node(feat_node_id):
                edge = KnowledgeEdge(
                    source_id=f"milestone:{milestone_id}",
                    target_id=feat_node_id,
                    relationship="includes",
                )
                await self._kg.add_edge(edge)

        logger.info("project_memory.milestone_added", milestone_id=milestone_id)
        return milestone

    async def complete_milestone(self, milestone_id: str) -> Milestone | None:
        """Mark a milestone as completed.

        Args:
            milestone_id: The milestone identifier.

        Returns:
            Updated milestone or None if not found.
        """
        existing = self._milestones.get(milestone_id)
        if existing is None:
            return None

        completed = Milestone(
            milestone_id=existing.milestone_id,
            title=existing.title,
            description=existing.description,
            due_date=existing.due_date,
            completed=True,
            features=existing.features,
        )
        self._milestones[milestone_id] = completed
        return completed

    async def list_milestones(self, completed: bool | None = None) -> list[Milestone]:
        """List milestones, optionally filtered by completion status."""
        milestones = list(self._milestones.values())
        if completed is not None:
            milestones = [m for m in milestones if m.completed == completed]
        return milestones

    async def get_summary(self) -> dict[str, int]:
        """Get project memory summary statistics.

        Returns:
            Dictionary with counts of ADRs, features, bugs, todos, milestones.
        """
        return {
            "adrs": len(self._adrs),
            "features": len(self._features),
            "bugs": len(self._bugs),
            "todos": len(self._todos),
            "milestones": len(self._milestones),
            "open_bugs": sum(1 for b in self._bugs.values() if b.status == "open"),
            "planned_features": sum(
                1 for f in self._features.values() if f.status == FeatureStatus.PLANNED
            ),
        }
