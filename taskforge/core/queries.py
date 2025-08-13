"""
Query models for TaskForge
"""

from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

from taskforge.core.task import TaskStatus, TaskPriority


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