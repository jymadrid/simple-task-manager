"""
Central task management system
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set
from collections import defaultdict
import asyncio
from dataclasses import dataclass

from taskforge.core.task import Task, TaskStatus, TaskPriority
from taskforge.core.project import Project, ProjectStatus
from taskforge.core.user import User, Permission
from taskforge.storage.base import StorageBackend
from taskforge.utils.notifications import NotificationManager
from taskforge.utils.search import SearchEngine
from taskforge.utils.analytics import AnalyticsEngine


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


class TaskManager:
    """
    Central task management system
    
    This class provides the main interface for managing tasks, projects, and users.
    It coordinates between storage, notifications, search, and analytics components.
    """
    
    def __init__(self, storage: StorageBackend, 
                 notification_manager: Optional[NotificationManager] = None,
                 search_engine: Optional[SearchEngine] = None,
                 analytics_engine: Optional[AnalyticsEngine] = None):
        self.storage = storage
        self.notifications = notification_manager
        self.search = search_engine
        self.analytics = analytics_engine
        
        # In-memory caches for performance
        self._task_cache: Dict[str, Task] = {}
        self._project_cache: Dict[str, Project] = {}
        self._user_cache: Dict[str, User] = {}
        
        # Task dependency graph for validation
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)

    # Task Management
    async def create_task(self, task: Task, user_id: str) -> Task:
        """Create a new task with validation and notifications"""
        # Validate user permissions
        user = await self.get_user(user_id)
        if not user or not user.has_permission(Permission.TASK_CREATE):
            raise PermissionError("User does not have permission to create tasks")
        
        # Validate project access if specified
        if task.project_id:
            project = await self.get_project(task.project_id)
            if not project or not project.is_member(user_id):
                raise ValueError("User is not a member of the specified project")
        
        # Set creator
        task.created_by = user_id
        if not task.assigned_to:
            task.assigned_to = user_id
        
        # Validate dependencies
        await self._validate_dependencies(task)
        
        # Save to storage
        saved_task = await self.storage.create_task(task)
        self._task_cache[saved_task.id] = saved_task
        
        # Update dependency graph
        self._update_dependency_graph(saved_task)
        
        # Update project progress
        if saved_task.project_id:
            await self._update_project_progress(saved_task.project_id)
        
        # Send notifications
        if self.notifications:
            await self.notifications.notify_task_created(saved_task, user)
        
        # Index for search
        if self.search:
            await self.search.index_task(saved_task)
        
        # Record analytics
        if self.analytics:
            await self.analytics.record_task_created(saved_task, user_id)
        
        return saved_task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by ID with caching"""
        if task_id in self._task_cache:
            return self._task_cache[task_id]
        
        task = await self.storage.get_task(task_id)
        if task:
            self._task_cache[task_id] = task
        return task

    async def update_task(self, task_id: str, updates: Dict[str, Any], user_id: str) -> Task:
        """Update a task with validation and notifications"""
        # Get existing task
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Validate user permissions
        user = await self.get_user(user_id)
        if not user or not user.has_permission(Permission.TASK_UPDATE):
            raise PermissionError("User does not have permission to update tasks")
        
        # Apply updates
        for field, value in updates.items():
            if hasattr(task, field):
                setattr(task, field, value)
        
        # Validate dependencies if changed
        if 'dependencies' in updates:
            await self._validate_dependencies(task)
        
        # Save changes
        updated_task = await self.storage.update_task(task)
        self._task_cache[task_id] = updated_task
        
        # Update dependency graph
        self._update_dependency_graph(updated_task)
        
        # Update project progress
        if updated_task.project_id:
            await self._update_project_progress(updated_task.project_id)
        
        # Send notifications
        if self.notifications:
            await self.notifications.notify_task_updated(updated_task, user)
        
        # Update search index
        if self.search:
            await self.search.update_task_index(updated_task)
        
        # Record analytics
        if self.analytics:
            await self.analytics.record_task_updated(updated_task, user_id)
        
        return updated_task

    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task with cascade handling"""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        # Validate user permissions
        user = await self.get_user(user_id)
        if not user or not user.has_permission(Permission.TASK_DELETE):
            raise PermissionError("User does not have permission to delete tasks")
        
        # Handle subtasks
        for subtask_id in task.subtasks:
            await self.delete_task(subtask_id, user_id)
        
        # Update dependent tasks
        dependent_tasks = await self._get_dependent_tasks(task_id)
        for dep_task in dependent_tasks:
            dep_task.remove_dependency(task_id)
            await self.storage.update_task(dep_task)
        
        # Delete from storage
        success = await self.storage.delete_task(task_id)
        
        if success:
            # Remove from cache
            self._task_cache.pop(task_id, None)
            
            # Update dependency graph
            self._dependency_graph.pop(task_id, None)
            for deps in self._dependency_graph.values():
                deps.discard(task_id)
            
            # Update project progress
            if task.project_id:
                await self._update_project_progress(task.project_id)
            
            # Remove from search index
            if self.search:
                await self.search.remove_task_from_index(task_id)
            
            # Record analytics
            if self.analytics:
                await self.analytics.record_task_deleted(task, user_id)
        
        return success

    async def search_tasks(self, query: TaskQuery, user_id: str) -> List[Task]:
        """Search tasks with filtering and pagination"""
        user = await self.get_user(user_id)
        if not user or not user.has_permission(Permission.TASK_READ):
            raise PermissionError("User does not have permission to read tasks")
        
        # Use search engine if available and text search is requested
        if self.search and query.search_text:
            return await self.search.search_tasks(query, user_id)
        
        # Otherwise use storage backend
        return await self.storage.search_tasks(query, user_id)

    async def get_overdue_tasks(self, user_id: Optional[str] = None) -> List[Task]:
        """Get all overdue tasks"""
        query = TaskQuery(
            status=[TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED],
            due_before=datetime.utcnow(),
            assigned_to=user_id
        )
        return await self.search_tasks(query, user_id or "system")

    async def get_upcoming_tasks(self, days: int = 7, user_id: Optional[str] = None) -> List[Task]:
        """Get tasks due in the next N days"""
        end_date = datetime.utcnow() + timedelta(days=days)
        query = TaskQuery(
            status=[TaskStatus.TODO, TaskStatus.IN_PROGRESS],
            due_after=datetime.utcnow(),
            due_before=end_date,
            assigned_to=user_id
        )
        return await self.search_tasks(query, user_id or "system")

    # Project Management
    async def create_project(self, project: Project, user_id: str) -> Project:
        """Create a new project"""
        user = await self.get_user(user_id)
        if not user or not user.has_permission(Permission.PROJECT_CREATE):
            raise PermissionError("User does not have permission to create projects")
        
        project.owner_id = user_id
        saved_project = await self.storage.create_project(project)
        self._project_cache[saved_project.id] = saved_project
        
        # Add creator as team member
        user.join_team(saved_project.id)
        await self.storage.update_user(user)
        
        return saved_project

    async def get_project(self, project_id: str) -> Optional[Project]:
        """Retrieve a project by ID"""
        if project_id in self._project_cache:
            return self._project_cache[project_id]
        
        project = await self.storage.get_project(project_id)
        if project:
            self._project_cache[project_id] = project
        return project

    # User Management
    async def get_user(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID"""
        if user_id in self._user_cache:
            return self._user_cache[user_id]
        
        user = await self.storage.get_user(user_id)
        if user:
            self._user_cache[user_id] = user
        return user

    # Analytics and Reporting  
    async def get_task_statistics(self, project_id: Optional[str] = None, 
                                user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive task statistics"""
        if self.analytics:
            return await self.analytics.get_task_statistics(project_id, user_id)
        
        # Basic statistics from storage
        return await self.storage.get_task_statistics(project_id, user_id)

    async def get_productivity_metrics(self, user_id: str, 
                                     days: int = 30) -> Dict[str, Any]:
        """Get user productivity metrics"""
        if self.analytics:
            return await self.analytics.get_productivity_metrics(user_id, days)
        
        # Basic metrics calculation
        start_date = datetime.utcnow() - timedelta(days=days)
        query = TaskQuery(
            assigned_to=user_id,
            created_after=start_date
        )
        tasks = await self.search_tasks(query, user_id)
        
        completed_tasks = [t for t in tasks if t.status == TaskStatus.DONE]
        return {
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
            "completion_rate": len(completed_tasks) / len(tasks) if tasks else 0,
            "avg_completion_time": self._calculate_avg_completion_time(completed_tasks)
        }

    # Internal helper methods
    async def _validate_dependencies(self, task: Task) -> None:
        """Validate task dependencies for cycles"""
        for dep in task.dependencies:
            if await self._creates_cycle(task.id, dep.task_id):
                raise ValueError(f"Dependency would create a cycle: {task.id} -> {dep.task_id}")

    async def _creates_cycle(self, source_id: str, target_id: str) -> bool:
        """Check if adding a dependency would create a cycle"""
        visited = set()
        
        async def dfs(node_id: str) -> bool:
            if node_id == source_id:
                return True
            if node_id in visited:
                return False
            
            visited.add(node_id)
            for dependency in self._dependency_graph.get(node_id, set()):
                if await dfs(dependency):
                    return True
            return False
        
        return await dfs(target_id)

    def _update_dependency_graph(self, task: Task) -> None:
        """Update the in-memory dependency graph"""
        self._dependency_graph[task.id] = {dep.task_id for dep in task.dependencies}

    async def _get_dependent_tasks(self, task_id: str) -> List[Task]:
        """Get tasks that depend on the given task"""
        dependent_tasks = []
        for tid, deps in self._dependency_graph.items():
            if task_id in deps:
                task = await self.get_task(tid)
                if task:
                    dependent_tasks.append(task)
        return dependent_tasks

    async def _update_project_progress(self, project_id: str) -> None:
        """Update project progress based on task completion"""
        project = await self.get_project(project_id)
        if not project:
            return
        
        query = TaskQuery(project_id=project_id, limit=1000)
        tasks = await self.storage.search_tasks(query, "system")
        
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.DONE])
        project.update_progress(completed_tasks, len(tasks))
        
        await self.storage.update_project(project)
        self._project_cache[project_id] = project

    def _calculate_avg_completion_time(self, completed_tasks: List[Task]) -> Optional[float]:
        """Calculate average time to complete tasks in hours"""
        if not completed_tasks:
            return None
        
        total_hours = 0
        valid_tasks = 0
        
        for task in completed_tasks:
            if task.completed_at and task.created_at:
                delta = task.completed_at - task.created_at
                total_hours += delta.total_seconds() / 3600
                valid_tasks += 1
        
        return total_hours / valid_tasks if valid_tasks > 0 else None

    # Batch operations
    async def bulk_update_tasks(self, task_ids: List[str], updates: Dict[str, Any], 
                              user_id: str) -> List[Task]:
        """Update multiple tasks in batch"""
        updated_tasks = []
        for task_id in task_ids:
            try:
                task = await self.update_task(task_id, updates, user_id)
                updated_tasks.append(task)
            except Exception as e:
                # Log error but continue with other tasks
                print(f"Failed to update task {task_id}: {e}")
        
        return updated_tasks

    async def archive_completed_tasks(self, project_id: Optional[str] = None,
                                    older_than_days: int = 30) -> int:
        """Archive old completed tasks"""
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        query = TaskQuery(
            status=[TaskStatus.DONE],
            project_id=project_id,
            created_before=cutoff_date
        )
        
        tasks = await self.storage.search_tasks(query, "system")
        archived_count = 0
        
        for task in tasks:
            task.status = TaskStatus.ARCHIVED  
            await self.storage.update_task(task)
            archived_count += 1
        
        return archived_count