"""
JSON file-based storage backend
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

from taskforge.core.project import Project
from taskforge.core.queries import TaskQuery
from taskforge.core.task import Task, TaskStatus
from taskforge.core.user import User
from taskforge.storage.base import StorageBackend
from taskforge.utils.performance import async_timer, time_function


class JSONStorage(StorageBackend):
    """JSON file-based storage implementation with performance optimizations"""

    def __init__(self, data_directory: str = "./data", save_delay: float = 0.5):
        self.data_dir = Path(data_directory)
        self.tasks_file = self.data_dir / "tasks.json"
        self.projects_file = self.data_dir / "projects.json"
        self.users_file = self.data_dir / "users.json"

        # In-memory caches for performance
        self._tasks_cache: Dict[str, Task] = {}
        self._projects_cache: Dict[str, Project] = {}
        self._users_cache: Dict[str, User] = {}
        self._cache_loaded = False

        # Performance optimization: dirty flags for delayed writes
        self._tasks_dirty = False
        self._projects_dirty = False
        self._users_dirty = False

        # Delayed write mechanism
        self._save_delay = save_delay
        self._pending_save_task: Optional[asyncio.Task] = None
        self._write_lock = asyncio.Lock()

        # Performance optimization: indexes for fast queries
        self._task_status_index: Dict[TaskStatus, set[str]] = {}
        self._task_priority_index: Dict[str, set[str]] = {}
        self._task_project_index: Dict[str, set[str]] = {}
        self._task_assignee_index: Dict[Optional[str], set[str]] = {}
        self._task_tags_index: Dict[str, set[str]] = {}

        # Performance monitoring
        self._cache_hits = 0
        self._cache_misses = 0

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
        # Cancel any pending save task
        if self._pending_save_task and not self._pending_save_task.done():
            self._pending_save_task.cancel()
        # Force immediate save on cleanup
        await self._save_all_data()

    async def _schedule_save(self) -> None:
        """Schedule a delayed save operation"""
        if self._pending_save_task and not self._pending_save_task.done():
            self._pending_save_task.cancel()

        self._pending_save_task = asyncio.create_task(self._delayed_save())

    async def _delayed_save(self) -> None:
        """Wait for delay period then save if dirty"""
        await asyncio.sleep(self._save_delay)

        if any([self._tasks_dirty, self._projects_dirty, self._users_dirty]):
            async with self._write_lock:
                await self._save_all_data_internal()
                self._tasks_dirty = False
                self._projects_dirty = False
                self._users_dirty = False

    async def _save_all_data(self) -> None:
        """Save all cached data to files (legacy method)"""
        async with self._write_lock:
            await self._save_all_data_internal()

    async def _save_all_data_internal(self) -> None:
        """Internal save method without locking"""
        try:
            # Only save if dirty
            if self._tasks_dirty:
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

            if self._projects_dirty:
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
                        project_dict["team_members"] = list(
                            project_dict["team_members"]
                        )
                    projects_data.append(project_dict)
                async with aiofiles.open(self.projects_file, "w") as f:
                    await f.write(json.dumps(projects_data, indent=2, default=str))

            if self._users_dirty:
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

    # Index management methods
    def _update_task_indexes(self, task: Task) -> None:
        """Update indexes for a task"""
        # Status index
        if task.status not in self._task_status_index:
            self._task_status_index[task.status] = set()
        self._task_status_index[task.status].add(task.id)

        # Priority index
        priority_val = (
            task.priority.value
            if hasattr(task.priority, "value")
            else str(task.priority)
        )
        if priority_val not in self._task_priority_index:
            self._task_priority_index[priority_val] = set()
        self._task_priority_index[priority_val].add(task.id)

        # Project index
        if task.project_id:
            if task.project_id not in self._task_project_index:
                self._task_project_index[task.project_id] = set()
            self._task_project_index[task.project_id].add(task.id)

        # Assignee index
        if task.assigned_to not in self._task_assignee_index:
            self._task_assignee_index[task.assigned_to] = set()
        self._task_assignee_index[task.assigned_to].add(task.id)

        # Tags index
        for tag in task.tags:
            if tag not in self._task_tags_index:
                self._task_tags_index[tag] = set()
            self._task_tags_index[tag].add(task.id)

    def _remove_task_from_indexes(self, task: Task) -> None:
        """Remove a task from all indexes"""
        # Remove from status index
        if task.status in self._task_status_index:
            self._task_status_index[task.status].discard(task.id)

        # Remove from priority index
        priority_val = (
            task.priority.value
            if hasattr(task.priority, "value")
            else str(task.priority)
        )
        if priority_val in self._task_priority_index:
            self._task_priority_index[priority_val].discard(task.id)

        # Remove from project index
        if task.project_id and task.project_id in self._task_project_index:
            self._task_project_index[task.project_id].discard(task.id)

        # Remove from assignee index
        if task.assigned_to in self._task_assignee_index:
            self._task_assignee_index[task.assigned_to].discard(task.id)

        # Remove from tags index
        for tag in task.tags:
            if tag in self._task_tags_index:
                self._task_tags_index[tag].discard(task.id)

    def _rebuild_indexes(self) -> None:
        """Rebuild all indexes from scratch"""
        # Clear existing indexes
        self._task_status_index.clear()
        self._task_priority_index.clear()
        self._task_project_index.clear()
        self._task_assignee_index.clear()
        self._task_tags_index.clear()

        # Rebuild from cache
        for task in self._tasks_cache.values():
            self._update_task_indexes(task)

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

            # Performance optimization: rebuild indexes after loading
            self._rebuild_indexes()

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading cache: {e}")
            # Initialize empty caches and indexes
            self._tasks_cache = {}
            self._projects_cache = {}
            self._users_cache = {}
            self._task_status_index.clear()
            self._task_priority_index.clear()
            self._task_project_index.clear()
            self._task_assignee_index.clear()
            self._task_tags_index.clear()
            self._cache_loaded = True

    # Task operations
    @time_function
    async def create_task(self, task: Task) -> Task:
        """Create a new task"""
        if not self._cache_loaded:
            await self._load_cache()

        if task.id in self._tasks_cache:
            raise ValueError(f"Task {task.id} already exists")

        self._tasks_cache[task.id] = task
        # Performance optimization: update indexes
        self._update_task_indexes(task)
        # Performance optimization: delayed write
        self._tasks_dirty = True
        await self._schedule_save()
        return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        if not self._cache_loaded:
            await self._load_cache()

        self._cache_hits += 1 if task_id in self._tasks_cache else self._cache_misses
        return self._tasks_cache.get(task_id)

    async def update_task(self, task: Task) -> Task:
        """Update an existing task"""
        if not self._cache_loaded:
            await self._load_cache()

        if task.id not in self._tasks_cache:
            raise ValueError(f"Task {task.id} not found")

        # Remove old task from indexes
        old_task = self._tasks_cache[task.id]
        self._remove_task_from_indexes(old_task)

        # Update task
        task.updated_at = datetime.now(timezone.utc)
        self._tasks_cache[task.id] = task
        self._update_task_indexes(task)

        # Performance optimization: delayed write
        self._tasks_dirty = True
        await self._schedule_save()
        return task

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        if not self._cache_loaded:
            await self._load_cache()

        if task_id in self._tasks_cache:
            task = self._tasks_cache[task_id]
            # Performance optimization: remove from indexes
            self._remove_task_from_indexes(task)
            del self._tasks_cache[task_id]
            # Performance optimization: delayed write
            self._tasks_dirty = True
            await self._schedule_save()
            return True
        return False

    async def search_tasks(self, query: TaskQuery, user_id: str) -> List[Task]:
        """Search tasks with filtering using optimized indexes"""
        if not self._cache_loaded:
            await self._load_cache()

        # Performance optimization: start with smallest candidate set
        candidate_task_ids = None

        # Use indexes to narrow down candidates
        index_selectivity = []

        # Status index (highly selective)
        if query.status:
            status_ids = set()
            for status in query.status:
                status_ids.update(self._task_status_index.get(status, set()))
            index_selectivity.append((len(status_ids), status_ids))
            if candidate_task_ids is None:
                candidate_task_ids = status_ids
            else:
                candidate_task_ids &= status_ids

        # Priority index (highly selective)
        if query.priority:
            priority_ids = set()
            for priority in query.priority:
                priority_val = (
                    priority.value if hasattr(priority, "value") else str(priority)
                )
                priority_ids.update(self._task_priority_index.get(priority_val, set()))
            index_selectivity.append((len(priority_ids), priority_ids))
            if candidate_task_ids is None:
                candidate_task_ids = priority_ids
            else:
                candidate_task_ids &= priority_ids

        # Project index (moderately selective)
        if query.project_id:
            project_ids = self._task_project_index.get(query.project_id, set())
            index_selectivity.append((len(project_ids), project_ids))
            if candidate_task_ids is None:
                candidate_task_ids = project_ids
            else:
                candidate_task_ids &= project_ids

        # Assignee index (moderately selective)
        if query.assigned_to:
            assignee_ids = self._task_assignee_index.get(query.assigned_to, set())
            index_selectivity.append((len(assignee_ids), assignee_ids))
            if candidate_task_ids is None:
                candidate_task_ids = assignee_ids
            else:
                candidate_task_ids &= assignee_ids

        # Tags index (variable selectivity)
        if query.tags:
            tag_ids = set()
            for tag in query.tags:
                tag_ids.update(self._task_tags_index.get(tag, set()))
            index_selectivity.append((len(tag_ids), tag_ids))
            if candidate_task_ids is None:
                candidate_task_ids = tag_ids
            else:
                candidate_task_ids &= tag_ids

        # If no indexes could be used, start with all tasks
        if candidate_task_ids is None:
            candidate_task_ids = set(self._tasks_cache.keys())

        # Performance optimization: convert IDs to tasks
        tasks = [
            self._tasks_cache[task_id]
            for task_id in candidate_task_ids
            if task_id in self._tasks_cache
        ]

        # Apply non-indexed filters
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
        # Performance optimization: delayed write
        self._projects_dirty = True
        await self._schedule_save()
        return project

    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID"""
        if not self._cache_loaded:
            await self._load_cache()

        self._cache_hits += (
            1 if project_id in self._projects_cache else self._cache_misses
        )
        return self._projects_cache.get(project_id)

    async def update_project(self, project: Project) -> Project:
        """Update an existing project"""
        if not self._cache_loaded:
            await self._load_cache()

        if project.id not in self._projects_cache:
            raise ValueError(f"Project {project.id} not found")

        project.updated_at = datetime.now(timezone.utc)
        self._projects_cache[project.id] = project
        # Performance optimization: delayed write
        self._projects_dirty = True
        await self._schedule_save()
        return project

    async def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        if not self._cache_loaded:
            await self._load_cache()

        if project_id in self._projects_cache:
            del self._projects_cache[project_id]
            # Performance optimization: delayed write
            self._projects_dirty = True
            await self._schedule_save()
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
        # Performance optimization: delayed write
        self._users_dirty = True
        await self._schedule_save()
        return user

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        if not self._cache_loaded:
            await self._load_cache()

        self._cache_hits += 1 if user_id in self._users_cache else self._cache_misses
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
        # Performance optimization: delayed write
        self._users_dirty = True
        await self._schedule_save()
        return user

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        if not self._cache_loaded:
            await self._load_cache()

        if user_id in self._users_cache:
            del self._users_cache[user_id]
            # Performance optimization: delayed write
            self._users_dirty = True
            await self._schedule_save()
            return True
        return False

    # Statistics and analytics
    async def get_task_statistics(
        self, project_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get task statistics using optimized indexes"""
        if not self._cache_loaded:
            await self._load_cache()

        # Performance optimization: use indexes to get candidate tasks
        candidate_task_ids = set(self._tasks_cache.keys())

        if project_id:
            project_ids = self._task_project_index.get(project_id, set())
            candidate_task_ids &= project_ids

        if user_id:
            assignee_ids = self._task_assignee_index.get(user_id, set())
            candidate_task_ids &= assignee_ids

        tasks = [
            self._tasks_cache[task_id]
            for task_id in candidate_task_ids
            if task_id in self._tasks_cache
        ]

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

    # Performance monitoring methods
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache hit/miss statistics"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0.0

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "tasks_cached": len(self._tasks_cache),
            "projects_cached": len(self._projects_cache),
            "users_cached": len(self._users_cache),
        }

    def get_index_statistics(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            "status_index_size": len(self._task_status_index),
            "priority_index_size": len(self._task_priority_index),
            "project_index_size": len(self._task_project_index),
            "assignee_index_size": len(self._task_assignee_index),
            "tags_index_size": len(self._task_tags_index),
            "total_indexed_tasks": len(set(self._tasks_cache.keys())),
        }

    def is_dirty(self) -> bool:
        """Check if any data is dirty (needs saving)"""
        return any([self._tasks_dirty, self._projects_dirty, self._users_dirty])

    async def force_save(self) -> None:
        """Force immediate save of all dirty data"""
        if self.is_dirty():
            await self._save_all_data()
            self._tasks_dirty = False
            self._projects_dirty = False
            self._users_dirty = False

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
            # Remove old task from indexes
            old_task = self._tasks_cache[task.id]
            self._remove_task_from_indexes(old_task)
            # Update task
            task.updated_at = datetime.now(timezone.utc)
            self._tasks_cache[task.id] = task
            self._update_task_indexes(task)
            updated_tasks.append(task)

        self._tasks_dirty = True
        await self._schedule_save()
        return updated_tasks

    async def bulk_delete_tasks(self, task_ids: List[str]) -> int:
        """Delete multiple tasks at once (optimized batch operation)"""
        if not self._cache_loaded:
            await self._load_cache()

        deleted_count = 0
        for task_id in task_ids:
            if task_id in self._tasks_cache:
                task = self._tasks_cache[task_id]
                self._remove_task_from_indexes(task)
                del self._tasks_cache[task_id]
                deleted_count += 1

        self._tasks_dirty = True
        await self._schedule_save()
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
