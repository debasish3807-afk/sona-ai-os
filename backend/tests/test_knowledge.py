"""Tests for Phase 31.1: Knowledge Graph Foundation."""

import pytest

from knowledge.entity_manager import EntityManager
from knowledge.exceptions import EntityNotFoundError
from knowledge.models import EntityType, KnowledgeEntity, KnowledgeRelationship, RelationType
from knowledge.relationship_manager import RelationshipManager
from knowledge.services import KnowledgeGraphService


@pytest.fixture
def service():
    return KnowledgeGraphService()


@pytest.fixture
def populated_graph(service):
    e1 = KnowledgeEntity(
        entity_type=EntityType.PROJECT, name="Alpha", description="First project", tags=["project"]
    )
    e2 = KnowledgeEntity(
        entity_type=EntityType.PROJECT, name="Beta", description="Second project", tags=["project"]
    )
    e3 = KnowledgeEntity(
        entity_type=EntityType.FILE, name="main.py", description="Main file", tags=["code"]
    )
    e4 = KnowledgeEntity(
        entity_type=EntityType.PEOPLE, name="Alice", description="Developer", tags=["dev"]
    )
    e1_id = service.entities.create(e1)
    e2_id = service.entities.create(e2)
    e3_id = service.entities.create(e3)
    e4_id = service.entities.create(e4)
    service.relationships.create(
        KnowledgeRelationship(
            source_id=e1_id, target_id=e2_id, relation_type=RelationType.DEPENDS_ON
        )
    )
    service.relationships.create(
        KnowledgeRelationship(
            source_id=e3_id, target_id=e1_id, relation_type=RelationType.BELONGS_TO
        )
    )
    service.relationships.create(
        KnowledgeRelationship(
            source_id=e4_id, target_id=e1_id, relation_type=RelationType.CREATED_BY
        )
    )
    return service, {"alpha": e1_id, "beta": e2_id, "main": e3_id, "alice": e4_id}


class TestEntityManager:
    def test_create_and_get(self):
        mgr = EntityManager()
        eid = mgr.create(KnowledgeEntity(name="Test", entity_type=EntityType.PROJECT))
        assert mgr.get(eid).name == "Test"

    def test_get_not_found(self):
        mgr = EntityManager()
        with pytest.raises(EntityNotFoundError):
            mgr.get("nonexistent")

    def test_update(self):
        mgr = EntityManager()
        eid = mgr.create(KnowledgeEntity(name="Old"))
        mgr.update(eid, name="New")
        assert mgr.get(eid).name == "New"

    def test_delete(self):
        mgr = EntityManager()
        eid = mgr.create(KnowledgeEntity(name="Test"))
        assert mgr.delete(eid)
        assert not mgr.delete("nonexistent")

    def test_list(self):
        mgr = EntityManager()
        mgr.create(KnowledgeEntity(name="A", entity_type=EntityType.PROJECT))
        mgr.create(KnowledgeEntity(name="B", entity_type=EntityType.TASK))
        assert len(mgr.list(entity_type="project")) == 1
        assert len(mgr.list()) == 2

    def test_search(self):
        mgr = EntityManager()
        mgr.create(KnowledgeEntity(name="SearchTarget", description="find me"))
        assert len(mgr.search("Search")) == 1
        assert len(mgr.search("xyz")) == 0


class TestRelationshipManager:
    def test_create_and_get(self):
        emgr = EntityManager()
        e1 = emgr.create(KnowledgeEntity(name="A"))
        e2 = emgr.create(KnowledgeEntity(name="B"))
        rmgr = RelationshipManager(entity_exists_fn=emgr.exists)
        rid = rmgr.create(KnowledgeRelationship(source_id=e1, target_id=e2))
        assert rmgr.get(rid).relation_type == RelationType.RELATED_TO

    def test_invalid_entity(self):
        rmgr = RelationshipManager(entity_exists_fn=lambda _: False)
        with pytest.raises(EntityNotFoundError):
            rmgr.create(KnowledgeRelationship(source_id="bad", target_id="bad2"))

    def test_outgoing_incoming(self):
        emgr = EntityManager()
        e1 = emgr.create(KnowledgeEntity(name="A"))
        e2 = emgr.create(KnowledgeEntity(name="B"))
        rmgr = RelationshipManager(entity_exists_fn=emgr.exists)
        rmgr.create(KnowledgeRelationship(source_id=e1, target_id=e2))
        assert len(rmgr.get_outgoing(e1)) == 1
        assert len(rmgr.get_incoming(e2)) == 1


class TestGraphEngine:
    def test_bfs(self, populated_graph):
        svc, ids = populated_graph
        result = svc.graph.bfs(ids["alpha"], max_depth=3)
        assert 0 in result

    def test_dfs(self, populated_graph):
        svc, ids = populated_graph
        result = svc.graph.dfs(ids["alpha"], max_depth=3)
        assert len(result) >= 1

    def test_shortest_path(self, populated_graph):
        svc, ids = populated_graph
        path = svc.graph.shortest_path(ids["alpha"], ids["beta"])
        assert len(path) == 2

    def test_subgraph(self, populated_graph):
        svc, ids = populated_graph
        sub = svc.graph.subgraph([ids["alpha"], ids["beta"]])
        assert len(sub["entities"]) == 2


class TestGraphValidator:
    def test_validate_clean(self, populated_graph):
        svc, ids = populated_graph
        result = svc.validator.validate()
        assert result.valid


class TestGraphQueryService:
    def test_stats(self, populated_graph):
        svc, ids = populated_graph
        stats = svc.query.stats()
        assert stats["entities"] >= 3

    def test_search(self, populated_graph):
        svc, ids = populated_graph
        results = svc.query.search_text("Alpha")
        assert len(results) == 1

    def test_search_by_type(self, populated_graph):
        svc, ids = populated_graph
        results = svc.query.search_by_type("project")
        assert len(results) == 2


class TestIntegration:
    def test_memory_index(self, service):
        eid = service.index_memory("Test memory content", "mem-1", "conversation")
        assert service.entities.exists(eid)

    def test_document_index(self, service):
        eid = service.index_document("doc-1", "Test Doc", "Document content here", ["docs"])
        assert service.entities.exists(eid)

    def test_workspace_entities(self, service):
        pid = service.create_project_entity("proj-1", "My Project")
        fid = service.create_file_entity("file-1", "test.py", "/path/to/test.py")
        tid = service.create_task_entity("task-1", "Fix bug")
        assert all(service.entities.exists(eid) for eid in [pid, fid, tid])

    def test_agent_context(self, service):
        eid = service.entities.create(KnowledgeEntity(name="AgentTest"))
        ctx = service.get_context_for_agent(eid)
        assert ctx["entity"]["name"] == "AgentTest"

    def test_automation_query(self, service):
        result = service.execute_query("search", {"query": "test"})
        assert "results" in result
        result2 = service.execute_query("create_entity", {"name": "FromAutomation"})
        assert "entity_id" in result2

    def test_full_workflow(self):
        svc = KnowledgeGraphService()
        e1 = svc.entities.create(KnowledgeEntity(name="Project X", entity_type=EntityType.PROJECT))
        e2 = svc.entities.create(
            KnowledgeEntity(
                name="File Y", entity_type=EntityType.FILE, metadata={"path": "/x/y.py"}
            )
        )
        svc.relationships.create(
            KnowledgeRelationship(source_id=e1, target_id=e2, relation_type=RelationType.CONTAINS)
        )
        stats = svc.query.stats()
        assert stats["entities"] == 2
        assert stats["relationships"] == 1
