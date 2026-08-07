"""Tests for the plugin repository."""

import pytest

from sona_plugins.domain.lifecycle import PluginLifecycleState
from sona_plugins.domain.models import PluginInstance, PluginManifest, PluginStatus
from sona_plugins.infrastructure.plugin_repository import PluginRepository


def _make_instance(plugin_id: str = "test-plugin") -> PluginInstance:
    manifest = PluginManifest(
        plugin_id=plugin_id,
        name=f"Plugin {plugin_id}",
        version="1.0.0",
        author="Test",
        description="Test",
        entry_point=f"plugins.{plugin_id}.Main",
        permissions=[],
    )
    return PluginInstance(manifest=manifest, status=PluginStatus.INACTIVE)


@pytest.fixture
def repo() -> PluginRepository:
    return PluginRepository()


class TestPluginRepositoryAdd:
    """Tests for adding plugins."""

    @pytest.mark.asyncio
    async def test_add_plugin(self, repo: PluginRepository) -> None:
        await repo.add(_make_instance())
        assert await repo.exists("test-plugin")

    @pytest.mark.asyncio
    async def test_add_duplicate_raises(self, repo: PluginRepository) -> None:
        await repo.add(_make_instance())
        with pytest.raises(ValueError, match="already exists"):
            await repo.add(_make_instance())

    @pytest.mark.asyncio
    async def test_add_sets_discovered_state(self, repo: PluginRepository) -> None:
        await repo.add(_make_instance())
        state = await repo.get_lifecycle_state("test-plugin")
        assert state == PluginLifecycleState.DISCOVERED


class TestPluginRepositoryGet:
    """Tests for retrieving plugins."""

    @pytest.mark.asyncio
    async def test_get_existing(self, repo: PluginRepository) -> None:
        await repo.add(_make_instance("p1"))
        result = await repo.get("p1")
        assert result is not None
        assert result.manifest.plugin_id == "p1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, repo: PluginRepository) -> None:
        assert await repo.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_get_all(self, repo: PluginRepository) -> None:
        await repo.add(_make_instance("a"))
        await repo.add(_make_instance("b"))
        all_plugins = await repo.get_all()
        assert len(all_plugins) == 2

    @pytest.mark.asyncio
    async def test_get_manifest(self, repo: PluginRepository) -> None:
        await repo.add(_make_instance("p1"))
        manifest = await repo.get_manifest("p1")
        assert manifest is not None
        assert manifest.plugin_id == "p1"


class TestPluginRepositoryUpdate:
    """Tests for updating plugins."""

    @pytest.mark.asyncio
    async def test_update_status(self, repo: PluginRepository) -> None:
        instance = _make_instance("p1")
        await repo.add(instance)
        instance.status = PluginStatus.ACTIVE
        await repo.update(instance)
        result = await repo.get("p1")
        assert result is not None
        assert result.status == PluginStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_update_nonexistent_raises(self, repo: PluginRepository) -> None:
        with pytest.raises(ValueError, match="not found"):
            await repo.update(_make_instance("nonexistent"))


class TestPluginRepositoryRemove:
    """Tests for removing plugins."""

    @pytest.mark.asyncio
    async def test_remove_existing(self, repo: PluginRepository) -> None:
        await repo.add(_make_instance("p1"))
        result = await repo.remove("p1")
        assert result is True
        assert not await repo.exists("p1")

    @pytest.mark.asyncio
    async def test_remove_nonexistent(self, repo: PluginRepository) -> None:
        result = await repo.remove("nonexistent")
        assert result is False


class TestPluginRepositoryQueries:
    """Tests for repository queries."""

    @pytest.mark.asyncio
    async def test_get_by_status(self, repo: PluginRepository) -> None:
        inst_a = _make_instance("a")
        inst_b = _make_instance("b")
        inst_a.status = PluginStatus.ACTIVE
        await repo.add(inst_a)
        await repo.add(inst_b)
        active = await repo.get_by_status(PluginStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].manifest.plugin_id == "a"

    @pytest.mark.asyncio
    async def test_get_by_lifecycle_state(self, repo: PluginRepository) -> None:
        await repo.add(_make_instance("a"))
        await repo.add(_make_instance("b"))
        await repo.set_lifecycle_state("a", PluginLifecycleState.INSTALLED)
        installed = await repo.get_by_lifecycle_state(PluginLifecycleState.INSTALLED)
        assert len(installed) == 1

    @pytest.mark.asyncio
    async def test_count(self, repo: PluginRepository) -> None:
        await repo.add(_make_instance("a"))
        await repo.add(_make_instance("b"))
        assert await repo.count() == 2

    @pytest.mark.asyncio
    async def test_clear(self, repo: PluginRepository) -> None:
        await repo.add(_make_instance("a"))
        await repo.add(_make_instance("b"))
        await repo.clear()
        assert await repo.count() == 0


class TestPluginRepositoryConfig:
    """Tests for config storage."""

    @pytest.mark.asyncio
    async def test_set_get_config(self, repo: PluginRepository) -> None:
        await repo.add(_make_instance("p1"))
        await repo.set_config("p1", {"port": 8080})
        config = await repo.get_config("p1")
        assert config == {"port": 8080}

    @pytest.mark.asyncio
    async def test_get_config_empty(self, repo: PluginRepository) -> None:
        config = await repo.get_config("nonexistent")
        assert config == {}

    @pytest.mark.asyncio
    async def test_lifecycle_state_operations(self, repo: PluginRepository) -> None:
        await repo.add(_make_instance("p1"))
        await repo.set_lifecycle_state("p1", PluginLifecycleState.RUNNING)
        state = await repo.get_lifecycle_state("p1")
        assert state == PluginLifecycleState.RUNNING

    @pytest.mark.asyncio
    async def test_set_lifecycle_state_nonexistent_raises(self, repo: PluginRepository) -> None:
        with pytest.raises(ValueError, match="not found"):
            await repo.set_lifecycle_state("nonexistent", PluginLifecycleState.RUNNING)
