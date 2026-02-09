"""
Simplified JSON storage for CI compatibility
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from taskforge.core.project import Project
from taskforge.core.queries import TaskQuery
from taskforge.core.task import Task, TaskStatus
from taskforge.core.user import User
from taskforge.storage.base import StorageBackend


class SimpleJSONStorage(StorageBackend):
    """Simplified JSON storage for CI testing"""

    def __init__(self, data_directory: str = "./data"):
        self.data_dir = Path(data_directory)
        self.tasks_file = self.data_dir / "tasks.json"
        self.projects_file = self.data_dir / "projects.json"
        self.users_file = self.data_dir / "users.json"

        # In-memory storage
        self._tasks: Dict[str, Task] = {}
        self._projects: Dict[str, Project] = {}
        self._users: Dict[str, User] = {}

    async def initialize(self) -> None:
        """Initialize storage"""
        self.data_dir.mkdir(exist_ok=True)
        
        # Load existing data if available
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, "r") as f:
                    tasks_data = json.load(f)
                    for task_data in tasks_data:
                        task = Task(**task_data)
                        self._tasks[task.id] = task
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    async def cleanup(self) -> None:
        """Save data and cleanup"""
        await self._save_all_data()

    async def _save_all_data(self) -> None:
        """Save all data to files"""
        # Save tasks
        tasks_data = [task.__dict__ for task in self._tasks.values()]
        with open(self.tasks_file, "w") as f:
            json.dump(tasks_data, f, indent=2, default=str)

    # Task operations
    async def create_task(self, task: Task) -> Task:
        """Create a new task"""
        self._tasks[task.id] = task
        await self._save_all_data()
        return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self._tasks.get(task_id)

    async def update_task(self, task: Task) -> Task:
        """Update an existing task"""
        if task.id not in self._tasks:
            raise ValueError(f"Task {task.id} not found")
        self._tasks[task.id] = task
        await self._save_all_data()
        return task

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            await self._save_all_data()
            return True
        return False

    async def search_tasks(self, query: TaskQuery, user_id: str) -> List[Task]:
        """Search tasks"""
        tasks = list(self._tasks.values())
        
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
        self._projects[project.id] = project
        await self._save_all_data()
        return project

    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID"""
        return self._projects.get(project_id)

    async def update_project(self, project: Project) -> Project:
        """Update an existing project"""
        if project.id not in self._projects:
            raise ValueError(f"Project {project.id} not found")
        self._projects[project.id] = project
        await self._save_all_data()
        return project

    async def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        if project_id in self._projects:
            del self._projects[project_id]
            await self._save_all_data()
            return True
        return False

    # User operations
    async def create_user(self, user: User) -> User:
        """Create a new user"""
        self._users[user.id] = user
        await self._save_all_data()
        return user

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        return self._users.get(user_id)

    async def update_user(self, user: User) -> User:
        """Update an existing user"""
        if user.id not in self._users:
            raise ValueError(f"User {user.id} not found")
        self._users[user.id] = user
        await self._save_all_data()
        return user

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        if user_id in self._users:
            del self._users[user_id]
            await self._save_all_data()
            return True
        return False

    # Statistics
    async def get_task_statistics(self, project_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get task statistics"""
        tasks = list(self._tasks.values())
        
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