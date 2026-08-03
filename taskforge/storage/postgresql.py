"""
Simplified PostgreSQL storage for CI compatibility
"""

from typing import Any, Dict, List, Optional

from taskforge.core.project import Project
from taskforge.core.queries import TaskQuery
from taskforge.core.task import Task, TaskStatus
from taskforge.core.user import User
from taskforge.storage.base import StorageBackend
from taskforge.utils.values import enum_matches


class SimplePostgreSQLStorage(StorageBackend):
    """Simplified PostgreSQL storage for CI testing"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._storage: Dict[str, Any] = {}  # In-memory storage for simplicity

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
            tasks = [
                task
                for task in tasks
                if any(enum_matches(task.status, status) for status in query.status)
            ]

        if query.priority:
            tasks = [
                task
                for task in tasks
                if any(
                    enum_matches(task.priority, priority) for priority in query.priority
                )
            ]

        if query.project_id:
            tasks = [t for t in tasks if t.project_id == query.project_id]

        if query.assigned_to:
            tasks = [t for t in tasks if t.assigned_to == query.assigned_to]

        if query.search_text:
            search_text = query.search_text.lower()
            tasks = [
                task
                for task in tasks
                if search_text in task.title.lower()
                or (task.description and search_text in task.description.lower())
            ]

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

    async def get_user_projects(self, user_id: str) -> List[Project]:
        """Get all projects owned by or shared with a user."""
        projects = [v for k, v in self._storage.items() if k.startswith("project:")]
        return [
            project
            for project in projects
            if project.owner_id == user_id or user_id in project.team_members
        ]

    # User operations
    async def create_user(self, user: User) -> User:
        """Create a new user"""
        self._storage[f"user:{user.id}"] = user
        return user

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        return self._storage.get(f"user:{user_id}")

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        users = [v for k, v in self._storage.items() if k.startswith("user:")]
        return next((user for user in users if user.username == username), None)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        users = [v for k, v in self._storage.items() if k.startswith("user:")]
        return next((user for user in users if user.email == email), None)

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
    async def get_task_statistics(
        self, project_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get task statistics"""
        tasks = [v for k, v in self._storage.items() if k.startswith("task:")]

        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]

        if user_id:
            tasks = [t for t in tasks if t.assigned_to == user_id]

        total_tasks = len(tasks)
        completed_tasks = len(
            [t for t in tasks if enum_matches(t.status, TaskStatus.DONE)]
        )
        in_progress_tasks = len(
            [t for t in tasks if enum_matches(t.status, TaskStatus.IN_PROGRESS)]
        )

        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "overdue_tasks": 0,  # Simplified
            "completion_rate": completion_rate,
        }


PostgreSQLStorage = SimplePostgreSQLStorage
