"""
Simplified PostgreSQL storage for CI compatibility
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from taskforge.core.project import Project
from taskforge.core.queries import TaskQuery
from taskforge.core.task import Task, TaskStatus
from taskforge.core.user import User
from taskforge.storage.base import StorageBackend


class SimplePostgreSQLStorage(StorageBackend):
    """Simplified PostgreSQL storage for CI testing"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._storage = {}  # In-memory storage for simplicity

    async def initialize(self) -> None:
        """Initialize storage"""
        pass  # Simplified for CI

    async def cleanup(self) -> None:
        """Cleanup storage"""
        pass

    # Task operations
    async def create_task(self, task: Task) -> Task:
        """Create a new task"""
        self._storage[f"task:{task.id}"] = task
        return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self._storage.get(f"task:{task_id}")

    async def update_task(self, task: Task) -> Task:
        """Update an existing task"""
        self._storage[f"task:{task.id}"] = task
        return task

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        key = f"task:{task_id}"
        if key in self._storage:
            del self._storage[key]
            return True
        return False

    async def search_tasks(self, query: TaskQuery, user_id: str) -> List[Task]:
        """Search tasks"""
        tasks = [v for k, v in self._storage.items() if k.startswith("task:")]
        
        # Apply basic filtering
        if query.status:
            tasks = [t for t in tasks if t.status in query.status]
        
        if query.project_id:
            tasks = [t for t in tasks if t.project_id == query.project_id]
        
        # Apply pagination
        start_idx = query.offset or 0
        end_idx = start_idx + (query.limit or 50)
        return tasks[start_idx:end_idx]

    # Project operations
    async def create_project(self, project: Project) -> Project:
        """Create a new project"""
        self._storage[f"project:{project.id}"] = project
        return project

    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID"""
        return self._storage.get(f"project:{project_id}")

    async def update_project(self, project: Project) -> Project:
        """Update an existing project"""
        self._storage[f"project:{project.id}"] = project
        return project

    async def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        key = f"project:{project_id}"
        if key in self._storage:
            del self._storage[key]
            return True
        return False

    # User operations
    async def create_user(self, user: User) -> User:
        """Create a new user"""
        self._storage[f"user:{user.id}"] = user
        return user

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        return self._storage.get(f"user:{user_id}")

    async def update_user(self, user: User) -> User:
        """Update an existing user"""
        self._storage[f"user:{user.id}"] = user
        return user

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        key = f"user:{user_id}"
        if key in self._storage:
            del self._storage[key]
            return True
        return False

    # Statistics
    async def get_task_statistics(self, project_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get task statistics"""
        tasks = [v for k, v in self._storage.items() if k.startswith("task:")]
        
        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.DONE])
        in_progress_tasks = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
        
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "overdue_tasks": 0,  # Simplified
            "completion_rate": completion_rate,
        }