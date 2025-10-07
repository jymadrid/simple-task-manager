"""
JSON file-based storage backend
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

from taskforge.core.manager import TaskQuery
from taskforge.core.project import Project
from taskforge.core.task import Task, TaskStatus
from taskforge.core.user import User
from taskforge.storage.base import StorageBackend
from taskforge.utils.performance import time_function, async_timer


class JSONStorage(StorageBackend):
    """JSON file-based storage implementation"""

    def __init__(self, data_directory: str = "./data"):
        self.data_dir = Path(data_directory)
        self.tasks_file = self.data_dir / "tasks.json"
        self.projects_file = self.data_dir / "projects.json"
        self.users_file = self.data_dir / "users.json"

        # In-memory caches for performance
        self._tasks_cache: Dict[str, Task] = {}
        self._projects_cache: Dict[str, Project] = {}
        self._users_cache: Dict[str, User] = {}
        self._cache_loaded = False

    async def initialize(self) -> None:
        """Initialize the storage backend"""
        async with async_timer("json_storage.initialize"):
            # Create data directory if it doesn't exist
            self.data_dir.mkdir(parents=True, exist_ok=True)

            # Create empty files if they don't exist
            for file_path in [self.tasks_file, self.projects_file, self.users_file]:
                if not file_path.exists():
                    async with aiofiles.open(file_path, "w") as f:
                        await f.write("[]")

            # Load data into cache
            await self._load_cache()

    async def cleanup(self) -> None:
        """Cleanup and save data"""
        await self._save_all_data()

    async def _load_cache(self) -> None:
        """Load all data into memory cache"""
        try:
            # Load tasks
            async with aiofiles.open(self.tasks_file, "r") as f:
                tasks_data = json.loads(await f.read())
                for task_data in tasks_data:
                    # Convert list back to set for tags
                    if "tags" in task_data and isinstance(task_data["tags"], list):
                        task_data["tags"] = set(task_data["tags"])
                    if "custom_permissions" in task_data and isinstance(
                        task_data["custom_permissions"], list
                    ):
                        task_data["custom_permissions"] = set(
                            task_data["custom_permissions"]
                        )
                    task = Task(**task_data)
                    self._tasks_cache[task.id] = task

            # Load projects
            async with aiofiles.open(self.projects_file, "r") as f:
                projects_data = json.loads(await f.read())
                for project_data in projects_data:
                    # Convert list back to set for tags and team_members
                    if "tags" in project_data and isinstance(
                        project_data["tags"], list
                    ):
                        project_data["tags"] = set(project_data["tags"])
                    if "team_members" in project_data and isinstance(
                        project_data["team_members"], list
                    ):
                        project_data["team_members"] = set(project_data["team_members"])
                    project = Project(**project_data)
                    self._projects_cache[project.id] = project

            # Load users
            async with aiofiles.open(self.users_file, "r") as f:
                users_data = json.loads(await f.read())
                for user_data in users_data:
                    # Convert list back to set for custom_permissions and teams
                    if "custom_permissions" in user_data and isinstance(
                        user_data["custom_permissions"], list
                    ):
                        user_data["custom_permissions"] = set(
                            user_data["custom_permissions"]
                        )
                    if "teams" in user_data and isinstance(user_data["teams"], list):
                        user_data["teams"] = set(user_data["teams"])
                    user = User(**user_data)
                    self._users_cache[user.id] = user

            self._cache_loaded = True

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading cache: {e}")
            # Initialize empty caches
            self._tasks_cache = {}
            self._projects_cache = {}
            self._users_cache = {}
            self._cache_loaded = True

    async def _save_all_data(self) -> None:
        """Save all cached data to files"""
        try:
            # Save tasks
            tasks_data = []
            for task in self._tasks_cache.values():
                task_dict = task.model_dump()
                # Convert sets to lists for JSON serialization
                if "tags" in task_dict and isinstance(task_dict["tags"], set):
                    task_dict["tags"] = list(task_dict["tags"])
                tasks_data.append(task_dict)
            async with aiofiles.open(self.tasks_file, "w") as f:
                await f.write(json.dumps(tasks_data, indent=2, default=str))

            # Save projects
            projects_data = []
            for project in self._projects_cache.values():
                project_dict = project.model_dump()
                # Convert sets to lists for JSON serialization
                if "tags" in project_dict and isinstance(project_dict["tags"], set):
                    project_dict["tags"] = list(project_dict["tags"])
                if "team_members" in project_dict and isinstance(
                    project_dict["team_members"], set
                ):
                    project_dict["team_members"] = list(project_dict["team_members"])
                projects_data.append(project_dict)
            async with aiofiles.open(self.projects_file, "w") as f:
                await f.write(json.dumps(projects_data, indent=2, default=str))

            # Save users
            users_data = []
            for user in self._users_cache.values():
                user_dict = user.model_dump(exclude={"password_hash"})
                # Convert sets to lists for JSON serialization
                if "custom_permissions" in user_dict and isinstance(
                    user_dict["custom_permissions"], set
                ):
                    user_dict["custom_permissions"] = list(
                        user_dict["custom_permissions"]
                    )
                if "teams" in user_dict and isinstance(user_dict["teams"], set):
                    user_dict["teams"] = list(user_dict["teams"])
                users_data.append(user_dict)
            async with aiofiles.open(self.users_file, "w") as f:
                await f.write(json.dumps(users_data, indent=2, default=str))

        except Exception as e:
            print(f"Error saving data: {e}")

    # Task operations
    @time_function
    async def create_task(self, task: Task) -> Task:
        """Create a new task"""
        if not self._cache_loaded:
            await self._load_cache()

        if task.id in self._tasks_cache:
            raise ValueError(f"Task {task.id} already exists")

        self._tasks_cache[task.id] = task
        await self._save_all_data()
        return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        if not self._cache_loaded:
            await self._load_cache()

        return self._tasks_cache.get(task_id)

    async def update_task(self, task: Task) -> Task:
        """Update an existing task"""
        if not self._cache_loaded:
            await self._load_cache()

        if task.id not in self._tasks_cache:
            raise ValueError(f"Task {task.id} not found")

        task.updated_at = datetime.now(timezone.utc)
        self._tasks_cache[task.id] = task
        await self._save_all_data()
        return task

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        if not self._cache_loaded:
            await self._load_cache()

        if task_id in self._tasks_cache:
            del self._tasks_cache[task_id]
            await self._save_all_data()
            return True
        return False

    async def search_tasks(self, query: TaskQuery, user_id: str) -> List[Task]:
        """Search tasks with filtering"""
        if not self._cache_loaded:
            await self._load_cache()

        tasks = list(self._tasks_cache.values())

        # Apply filters
        if query.status:
            tasks = [t for t in tasks if t.status in query.status]

        if query.priority:
            tasks = [t for t in tasks if t.priority in query.priority]

        if query.assigned_to:
            tasks = [t for t in tasks if t.assigned_to == query.assigned_to]

        if query.project_id:
            tasks = [t for t in tasks if t.project_id == query.project_id]

        if query.tags:
            tasks = [t for t in tasks if any(tag in t.tags for tag in query.tags)]

        if query.created_after:
            tasks = [t for t in tasks if t.created_at >= query.created_after]

        if query.created_before:
            tasks = [t for t in tasks if t.created_at <= query.created_before]

        if query.due_after:
            tasks = [t for t in tasks if t.due_date and t.due_date >= query.due_after]

        if query.due_before:
            tasks = [t for t in tasks if t.due_date and t.due_date <= query.due_before]

        if query.search_text:
            search_lower = query.search_text.lower()
            tasks = [
                t
                for t in tasks
                if search_lower in t.title.lower()
                or (t.description and search_lower in t.description.lower())
            ]

        # Sort by creation date (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        # Apply pagination
        start_idx = query.offset
        end_idx = start_idx + query.limit
        return tasks[start_idx:end_idx]

    # Project operations
    async def create_project(self, project: Project) -> Project:
        """Create a new project"""
        if not self._cache_loaded:
            await self._load_cache()

        self._projects_cache[project.id] = project
        await self._save_all_data()
        return project

    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID"""
        if not self._cache_loaded:
            await self._load_cache()

        return self._projects_cache.get(project_id)

    async def update_project(self, project: Project) -> Project:
        """Update an existing project"""
        if not self._cache_loaded:
            await self._load_cache()

        if project.id not in self._projects_cache:
            raise ValueError(f"Project {project.id} not found")

        project.updated_at = datetime.now(timezone.utc)
        self._projects_cache[project.id] = project
        await self._save_all_data()
        return project

    async def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        if not self._cache_loaded:
            await self._load_cache()

        if project_id in self._projects_cache:
            del self._projects_cache[project_id]
            await self._save_all_data()
            return True
        return False

    async def get_user_projects(self, user_id: str) -> List[Project]:
        """Get all projects for a user"""
        if not self._cache_loaded:
            await self._load_cache()

        projects = []
        for project in self._projects_cache.values():
            if project.owner_id == user_id or user_id in project.team_members:
                projects.append(project)

        return projects

    # User operations
    async def create_user(self, user: User) -> User:
        """Create a new user"""
        if not self._cache_loaded:
            await self._load_cache()

        # Check for duplicate username/email
        for existing_user in self._users_cache.values():
            if existing_user.username == user.username:
                raise ValueError(f"Username {user.username} already exists")
            if existing_user.email == user.email:
                raise ValueError(f"Email {user.email} already exists")

        self._users_cache[user.id] = user
        await self._save_all_data()
        return user

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        if not self._cache_loaded:
            await self._load_cache()

        return self._users_cache.get(user_id)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        if not self._cache_loaded:
            await self._load_cache()

        for user in self._users_cache.values():
            if user.username == username:
                return user
        return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        if not self._cache_loaded:
            await self._load_cache()

        for user in self._users_cache.values():
            if user.email == email:
                return user
        return None

    async def update_user(self, user: User) -> User:
        """Update an existing user"""
        if not self._cache_loaded:
            await self._load_cache()

        if user.id not in self._users_cache:
            raise ValueError(f"User {user.id} not found")

        user.updated_at = datetime.now(timezone.utc)
        self._users_cache[user.id] = user
        await self._save_all_data()
        return user

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        if not self._cache_loaded:
            await self._load_cache()

        if user_id in self._users_cache:
            del self._users_cache[user_id]
            await self._save_all_data()
            return True
        return False

    # Statistics and analytics
    async def get_task_statistics(
        self, project_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get task statistics"""
        if not self._cache_loaded:
            await self._load_cache()

        tasks = list(self._tasks_cache.values())

        # Filter by project if specified
        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]

        # Filter by user if specified
        if user_id:
            tasks = [t for t in tasks if t.assigned_to == user_id]

        # Calculate statistics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.DONE])
        in_progress_tasks = len(
            [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        )
        overdue_tasks = len([t for t in tasks if t.is_overdue()])

        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0

        # Priority distribution
        priority_dist = {}
        for task in tasks:
            priority = (
                task.priority.value
                if hasattr(task.priority, "value")
                else task.priority
            )
            priority_dist[priority] = priority_dist.get(priority, 0) + 1

        # Status distribution
        status_dist = {}
        for task in tasks:
            status = task.status.value if hasattr(task.status, "value") else task.status
            status_dist[status] = status_dist.get(status, 0) + 1

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "overdue_tasks": overdue_tasks,
            "completion_rate": completion_rate,
            "priority_distribution": priority_dist,
            "status_distribution": status_dist,
        }

    # Bulk operations
    async def bulk_create_tasks(self, tasks: List[Task]) -> List[Task]:
        """Create multiple tasks at once"""
        if not self._cache_loaded:
            await self._load_cache()

        created_tasks = []
        for task in tasks:
            if task.id in self._tasks_cache:
                raise ValueError(f"Task {task.id} already exists")
            self._tasks_cache[task.id] = task
            created_tasks.append(task)

        await self._save_all_data()
        return created_tasks

    async def bulk_update_tasks(self, tasks: List[Task]) -> List[Task]:
        """Update multiple tasks at once"""
        if not self._cache_loaded:
            await self._load_cache()

        updated_tasks = []
        for task in tasks:
            if task.id not in self._tasks_cache:
                raise ValueError(f"Task {task.id} not found")
            task.updated_at = datetime.now(timezone.utc)
            self._tasks_cache[task.id] = task
            updated_tasks.append(task)

        await self._save_all_data()
        return updated_tasks

    async def bulk_delete_tasks(self, task_ids: List[str]) -> int:
        """Delete multiple tasks at once"""
        if not self._cache_loaded:
            await self._load_cache()

        deleted_count = 0
        for task_id in task_ids:
            if task_id in self._tasks_cache:
                del self._tasks_cache[task_id]
                deleted_count += 1

        await self._save_all_data()
        return deleted_count

    # Data export/import
    async def export_data(self) -> Dict[str, Any]:
        """Export all data"""
        if not self._cache_loaded:
            await self._load_cache()

        return {
            "tasks": [task.model_dump() for task in self._tasks_cache.values()],
            "projects": [
                project.model_dump() for project in self._projects_cache.values()
            ],
            "users": [user.to_public_dict() for user in self._users_cache.values()],
            "version": "1.0.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }
