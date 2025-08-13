"""
TaskForge: A comprehensive, extensible task management platform

This package provides a modern, feature-rich task management system designed
for developers, teams, and organizations. It offers multiple interfaces
(CLI, Web API, GUI) and extensive customization through plugins.
"""

from taskforge.core.manager import TaskManager
from taskforge.core.project import Project
from taskforge.core.task import Task, TaskPriority, TaskStatus
from taskforge.core.user import User

__version__ = "0.1.0"
__author__ = "TaskForge Community"
__email__ = "maintainers@taskforge.dev"

__all__ = [
    "Task",
    "TaskStatus",
    "TaskPriority",
    "Project",
    "User",
    "TaskManager",
]
