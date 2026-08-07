"""Tests for the plugin capability model."""

import pytest

from sona_plugins.domain.capability import PluginCapability, PluginCapabilityType


class TestPluginCapabilityType:
    """Tests for PluginCapabilityType enum."""

    def test_all_types_defined(self) -> None:
        assert len(PluginCapabilityType) == 6

    def test_type_values(self) -> None:
        assert PluginCapabilityType.TOOL == "tool"
        assert PluginCapabilityType.RESOURCE == "resource"
        assert PluginCapabilityType.PROMPT == "prompt"
        assert PluginCapabilityType.AGENT == "agent"
        assert PluginCapabilityType.MIDDLEWARE == "middleware"
        assert PluginCapabilityType.HOOK == "hook"

    def test_types_are_str(self) -> None:
        for cap_type in PluginCapabilityType:
            assert isinstance(cap_type, str)


class TestPluginCapability:
    """Tests for PluginCapability dataclass."""

    def test_creation_minimal(self) -> None:
        cap = PluginCapability(name="search", capability_type=PluginCapabilityType.TOOL)
        assert cap.name == "search"
        assert cap.capability_type == PluginCapabilityType.TOOL
        assert cap.description == ""
        assert cap.version == "1.0.0"

    def test_creation_full(self) -> None:
        cap = PluginCapability(
            name="translate",
            capability_type=PluginCapabilityType.RESOURCE,
            description="Translates text between languages",
            version="2.1.0",
        )
        assert cap.name == "translate"
        assert cap.capability_type == PluginCapabilityType.RESOURCE
        assert cap.description == "Translates text between languages"
        assert cap.version == "2.1.0"

    def test_is_frozen(self) -> None:
        cap = PluginCapability(name="test", capability_type=PluginCapabilityType.TOOL)
        with pytest.raises(AttributeError):
            cap.name = "changed"  # type: ignore[misc]

    def test_equality(self) -> None:
        cap1 = PluginCapability(name="echo", capability_type=PluginCapabilityType.TOOL)
        cap2 = PluginCapability(name="echo", capability_type=PluginCapabilityType.TOOL)
        assert cap1 == cap2

    def test_inequality_name(self) -> None:
        cap1 = PluginCapability(name="echo", capability_type=PluginCapabilityType.TOOL)
        cap2 = PluginCapability(name="format", capability_type=PluginCapabilityType.TOOL)
        assert cap1 != cap2

    def test_inequality_type(self) -> None:
        cap1 = PluginCapability(name="data", capability_type=PluginCapabilityType.TOOL)
        cap2 = PluginCapability(name="data", capability_type=PluginCapabilityType.RESOURCE)
        assert cap1 != cap2

    def test_all_capability_types_usable(self) -> None:
        for cap_type in PluginCapabilityType:
            cap = PluginCapability(name=f"test-{cap_type}", capability_type=cap_type)
            assert cap.capability_type == cap_type

    def test_hashable(self) -> None:
        cap = PluginCapability(name="echo", capability_type=PluginCapabilityType.TOOL)
        cap_set = {cap}
        assert cap in cap_set
