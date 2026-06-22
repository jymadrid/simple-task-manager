"""
Plugin system for TaskForge extensibility
"""

import importlib.util
import inspect
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypedDict, cast

from taskforge.core.project import Project
from taskforge.core.task import Task
from taskforge.core.user import User

logger = logging.getLogger(__name__)


HookCallable = Callable[..., Any]


class PluginHookInfo(TypedDict):
    """Hook method registered on a plugin instance."""

    method: HookCallable
    priority: int


class RegisteredHookInfo(PluginHookInfo):
    """Hook method registered globally with its owning plugin."""

    plugin: str


@dataclass
class PluginMetadata:
    """Metadata for a plugin"""

    name: str
    version: str
    description: str
    author: str
    email: Optional[str] = None
    website: Optional[str] = None
    homepage: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    min_taskforge_version: Optional[str] = None
    max_taskforge_version: Optional[str] = None

    def __post_init__(self) -> None:
        if self.homepage is None:
            self.homepage = self.website
        elif self.website is None:
            self.website = self.homepage


class PluginHook:
    """Decorator for registering plugin hooks"""

    def __init__(self, hook_name: str, priority: int = 100):
        self.hook_name = hook_name
        self.priority = priority

    def __call__(self, func: HookCallable) -> HookCallable:
        setattr(func, "_hook_name", self.hook_name)
        setattr(func, "_hook_priority", self.priority)
        return func


class BasePlugin(ABC):
    """Base class for all TaskForge plugins"""

    def __init__(self) -> None:
        self.metadata = self.get_metadata()
        self.enabled = True
        self.hooks: Dict[str, List[PluginHookInfo]] = {}
        self._register_hooks()

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass

    def _register_hooks(self) -> None:
        """Register all hooks defined in the plugin"""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            hook_name = getattr(method, "_hook_name", None)
            if hook_name is not None:
                priority = int(getattr(method, "_hook_priority", 100))
                hook_method = cast(HookCallable, method)

                if hook_name not in self.hooks:
                    self.hooks[hook_name] = []

                self.hooks[hook_name].append(
                    {"method": hook_method, "priority": priority}
                )

        # Sort hooks by priority
        for hook_name in self.hooks:
            self.hooks[hook_name].sort(key=lambda x: x["priority"])

    def activate(self) -> None:
        """Activate the plugin"""
        self.enabled = True
        self.on_activate()

    def deactivate(self) -> None:
        """Deactivate the plugin"""
        self.enabled = False
        self.on_deactivate()

    def on_activate(self) -> None:
        """Called when plugin is activated"""
        pass

    def on_deactivate(self) -> None:
        """Called when plugin is deactivated"""
        pass


class TaskPlugin(BasePlugin):
    """Base class for task-related plugins"""

    @PluginHook("task_created")
    def on_task_created(self, task: Task, user: User, **kwargs: Any) -> None:
        """Called when a task is created"""
        pass

    @PluginHook("task_updated")
    def on_task_updated(
        self, task: Task, old_task: Task, user: User, **kwargs: Any
    ) -> None:
        """Called when a task is updated"""
        pass

    @PluginHook("task_deleted")
    def on_task_deleted(self, task: Task, user: User, **kwargs: Any) -> None:
        """Called when a task is deleted"""
        pass

    @PluginHook("task_status_changed")
    def on_task_status_changed(
        self, task: Task, old_status: str, new_status: str, user: User, **kwargs: Any
    ) -> None:
        """Called when task status changes"""
        pass


class ProjectPlugin(BasePlugin):
    """Base class for project-related plugins"""

    @PluginHook("project_created")
    def on_project_created(self, project: Project, user: User, **kwargs: Any) -> None:
        """Called when a project is created"""
        pass

    @PluginHook("project_updated")
    def on_project_updated(
        self, project: Project, old_project: Project, user: User, **kwargs: Any
    ) -> None:
        """Called when a project is updated"""
        pass


class IntegrationPlugin(BasePlugin):
    """Base class for external integration plugins"""

    @abstractmethod
    def sync_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """Sync tasks with external service"""
        pass

    @abstractmethod
    def import_tasks(self) -> List[Task]:
        """Import tasks from external service"""
        pass


class NotificationPlugin(BasePlugin):
    """Base class for notification plugins"""

    @PluginHook("send_notification")
    def send_notification(self, message: str, user: User, **kwargs: Any) -> None:
        """Send notification to user"""
        pass

    @PluginHook("task_due_reminder")
    def send_due_reminder(self, task: Task, user: User, **kwargs: Any) -> None:
        """Send due date reminder"""
        pass


class PluginManager:
    """Manages plugin loading, activation, and hook execution"""

    def __init__(self) -> None:
        self.plugins: Dict[str, BasePlugin] = {}
        self.hooks: Dict[str, List[RegisteredHookInfo]] = {}
        self.plugin_directories: List[Path] = []

    def add_plugin_directory(self, directory: Path) -> None:
        """Add a directory to search for plugins"""
        plugin_directory = directory.expanduser()
        if plugin_directory.exists() and plugin_directory.is_dir():
            self.plugin_directories.append(plugin_directory)

    def discover_plugins(self) -> List[str]:
        """Discover all available plugins"""
        discovered = []

        for directory in self.plugin_directories:
            for plugin_file in directory.glob("*.py"):
                if plugin_file.name.startswith("plugin_"):
                    plugin_name = plugin_file.stem[7:]  # Remove "plugin_" prefix
                    discovered.append(plugin_name)

        return discovered

    def load_plugin(self, plugin_name: str) -> bool:
        """Load a plugin by name"""
        try:
            # Try to find the plugin file
            plugin_file = None
            for directory in self.plugin_directories:
                candidate = directory / f"plugin_{plugin_name}.py"
                if candidate.exists():
                    plugin_file = candidate
                    break

            if not plugin_file:
                logger.error(f"Plugin file not found: plugin_{plugin_name}.py")
                return False

            # Import the plugin module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_name}", plugin_file
            )
            if spec is None or spec.loader is None:
                logger.error(f"Unable to import plugin module from {plugin_file}")
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the plugin class
            plugin_class: Optional[Type[BasePlugin]] = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, BasePlugin)
                    and obj != BasePlugin
                    and not obj.__name__.startswith("Base")
                ):
                    plugin_class = obj
                    break

            if not plugin_class:
                logger.error(f"No plugin class found in {plugin_file}")
                return False

            # Instantiate the plugin
            plugin_instance = plugin_class()
            self.plugins[plugin_name] = plugin_instance

            # Register plugin hooks
            self._register_plugin_hooks(plugin_name, plugin_instance)

            logger.info(f"Loaded plugin: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        if plugin_name not in self.plugins:
            return False

        plugin = self.plugins[plugin_name]
        plugin.deactivate()

        # Remove plugin hooks
        self._unregister_plugin_hooks(plugin_name)

        del self.plugins[plugin_name]
        logger.info(f"Unloaded plugin: {plugin_name}")
        return True

    def activate_plugin(self, plugin_name: str) -> bool:
        """Activate a plugin"""
        if plugin_name not in self.plugins:
            return False

        self.plugins[plugin_name].activate()
        logger.info(f"Activated plugin: {plugin_name}")
        return True

    def deactivate_plugin(self, plugin_name: str) -> bool:
        """Deactivate a plugin"""
        if plugin_name not in self.plugins:
            return False

        self.plugins[plugin_name].deactivate()
        logger.info(f"Deactivated plugin: {plugin_name}")
        return True

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get a plugin instance by name"""
        return self.plugins.get(plugin_name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins with their metadata"""
        result = []
        for name, plugin in self.plugins.items():
            result.append(
                {
                    "name": name,
                    "metadata": plugin.metadata,
                    "enabled": plugin.enabled,
                    "hooks": list(plugin.hooks.keys()),
                }
            )
        return result

    def execute_hook(self, hook_name: str, *args: Any, **kwargs: Any) -> List[Any]:
        """Execute all hooks for a given hook name"""
        results: List[Any] = []

        if hook_name not in self.hooks:
            return results

        for hook_info in self.hooks[hook_name]:
            plugin_name = hook_info["plugin"]
            method = hook_info["method"]

            # Skip if plugin is disabled
            if not self.plugins[plugin_name].enabled:
                continue

            try:
                result = method(*args, **kwargs)
                results.append({"plugin": plugin_name, "result": result})
            except Exception as e:
                logger.error(
                    f"Error executing hook {hook_name} in plugin {plugin_name}: {e}"
                )
                results.append({"plugin": plugin_name, "error": str(e)})

        return results

    def _register_plugin_hooks(self, plugin_name: str, plugin: BasePlugin) -> None:
        """Register all hooks from a plugin"""
        for hook_name, hook_methods in plugin.hooks.items():
            if hook_name not in self.hooks:
                self.hooks[hook_name] = []

            for hook_info in hook_methods:
                self.hooks[hook_name].append(
                    {
                        "plugin": plugin_name,
                        "method": hook_info["method"],
                        "priority": hook_info["priority"],
                    }
                )

            # Sort by priority
            self.hooks[hook_name].sort(key=lambda x: x["priority"])

    def _unregister_plugin_hooks(self, plugin_name: str) -> None:
        """Unregister all hooks from a plugin"""
        for hook_name in list(self.hooks.keys()):
            self.hooks[hook_name] = [
                hook for hook in self.hooks[hook_name] if hook["plugin"] != plugin_name
            ]

            # Remove empty hook lists
            if not self.hooks[hook_name]:
                del self.hooks[hook_name]


# Global plugin manager instance
plugin_manager = PluginManager()


def register_plugin_directory(directory: str) -> None:
    """Register a directory for plugin discovery"""
    plugin_manager.add_plugin_directory(Path(directory))


def load_plugin(plugin_name: str) -> bool:
    """Load a plugin"""
    return plugin_manager.load_plugin(plugin_name)


def execute_hook(hook_name: str, *args: Any, **kwargs: Any) -> List[Any]:
    """Execute a hook"""
    return plugin_manager.execute_hook(hook_name, *args, **kwargs)


# Default plugin directories
register_plugin_directory("./plugins")
register_plugin_directory("~/.taskforge/plugins")
register_plugin_directory("/usr/local/share/taskforge/plugins")
