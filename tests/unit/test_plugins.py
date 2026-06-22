from pathlib import Path
from typing import Any

from taskforge.plugins import BasePlugin, PluginHook, PluginManager, PluginMetadata


class RecordingPlugin(BasePlugin):
    """Small test plugin with two hooks for priority and state checks."""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="recording",
            version="1.0.0",
            description="records hook execution",
            author="TaskForge",
        )

    @PluginHook("record", priority=20)
    def record_late(self, value: str, **kwargs: Any) -> str:
        return f"late:{value}"

    @PluginHook("record", priority=5)
    def record_early(self, value: str, **kwargs: Any) -> str:
        return f"early:{value}"


def test_plugin_metadata_uses_independent_dependency_lists() -> None:
    first = PluginMetadata(
        name="first",
        version="1.0.0",
        description="first plugin",
        author="TaskForge",
    )
    second = PluginMetadata(
        name="second",
        version="1.0.0",
        description="second plugin",
        author="TaskForge",
    )

    first.dependencies.append("requests")

    assert first.dependencies == ["requests"]
    assert second.dependencies == []


def test_plugin_metadata_supports_homepage_alias() -> None:
    metadata = PluginMetadata(
        name="homepage",
        version="1.0.0",
        description="homepage plugin",
        author="TaskForge",
        homepage="https://example.com/plugin",
    )
    legacy_metadata = PluginMetadata(
        name="website",
        version="1.0.0",
        description="website plugin",
        author="TaskForge",
        website="https://example.com/legacy",
    )

    assert metadata.website == "https://example.com/plugin"
    assert metadata.homepage == "https://example.com/plugin"
    assert legacy_metadata.website == "https://example.com/legacy"
    assert legacy_metadata.homepage == "https://example.com/legacy"


def test_execute_hook_respects_priority_and_enabled_state() -> None:
    manager = PluginManager()
    plugin = RecordingPlugin()
    manager.plugins["recording"] = plugin
    manager._register_plugin_hooks("recording", plugin)

    assert manager.execute_hook("record", "task") == [
        {"plugin": "recording", "result": "early:task"},
        {"plugin": "recording", "result": "late:task"},
    ]

    manager.deactivate_plugin("recording")

    assert manager.execute_hook("record", "task") == []


def test_load_plugin_from_directory(tmp_path: Path) -> None:
    plugin_file = tmp_path / "plugin_demo.py"
    plugin_file.write_text(
        """
from typing import Any

from taskforge.plugins import BasePlugin, PluginHook, PluginMetadata


class DemoPlugin(BasePlugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="demo",
            version="1.0.0",
            description="demo plugin",
            author="TaskForge",
        )

    @PluginHook("demo", priority=1)
    def run(self, value: int, **kwargs: Any) -> int:
        return value * 2
""".lstrip(),
        encoding="utf-8",
    )

    manager = PluginManager()
    manager.add_plugin_directory(tmp_path)

    assert manager.discover_plugins() == ["demo"]
    assert manager.load_plugin("demo") is True
    assert manager.execute_hook("demo", 3) == [{"plugin": "demo", "result": 6}]
