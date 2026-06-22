"""
Query models for TaskForge
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Literal, Optional, get_args

from taskforge.core.task import TaskPriority, TaskStatus

TaskSortField = Literal[
    "created_at",
    "updated_at",
    "due_date",
    "priority",
    "status",
    "title",
    "progress",
]


@dataclass
class TaskQuery:
    """Query parameters for task filtering and searching"""

    status: Optional[List[TaskStatus]] = None
    priority: Optional[List[TaskPriority]] = None
    assigned_to: Optional[str] = None
    project_id: Optional[str] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    due_after: Optional[datetime] = None
    due_before: Optional[datetime] = None
    search_text: Optional[str] = None
    limit: int = 100
    offset: int = 0
    sort_by: TaskSortField = "created_at"
    sort_desc: bool = True
    tags_match_all: bool = True

    def __post_init__(self) -> None:
        """Normalize pagination so storage backends receive safe bounds."""
        self.limit = max(0, self.limit)
        self.offset = max(0, self.offset)
        if self.sort_by not in get_args(TaskSortField):
            allowed = ", ".join(get_args(TaskSortField))
            raise ValueError(
                f"Unsupported task sort field: {self.sort_by}. Use: {allowed}"
            )
