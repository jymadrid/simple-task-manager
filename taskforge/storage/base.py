"""
Base storage interface for TaskForge
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from taskforge.core.task import Task
from taskforge.core.project import Project
from taskforge.core.user import User
from taskforge.core.queries import TaskQuery


class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup and close connections"""
        pass
    
    # Task operations
    @abstractmethod
    async def create_task(self, task: Task) -> Task:
        """Create a new task"""
        pass
    
    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        pass
    
    @abstractmethod
    async def update_task(self, task: Task) -> Task:
        """Update an existing task"""
        pass
    
    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        pass
    
    @abstractmethod
    async def search_tasks(self, query: TaskQuery, user_id: str) -> List[Task]:
        """Search tasks with filtering"""
        pass
    
    # Project operations
    @abstractmethod
    async def create_project(self, project: Project) -> Project:
        """Create a new project"""
        pass
    
    @abstractmethod
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID"""
        pass
    
    @abstractmethod
    async def update_project(self, project: Project) -> Project:
        """Update an existing project"""
        pass
    
    @abstractmethod
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        pass
    
    @abstractmethod
    async def get_user_projects(self, user_id: str) -> List[Project]:
        """Get all projects for a user"""
        pass
    
    # User operations
    @abstractmethod
    async def create_user(self, user: User) -> User:
        """Create a new user"""
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        pass
    
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        pass
    
    @abstractmethod
    async def update_user(self, user: User) -> User:
        """Update an existing user"""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        pass
    
    # Statistics and analytics
    @abstractmethod
    async def get_task_statistics(self, project_id: Optional[str] = None, 
                                user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get task statistics"""
        pass
    
    # Bulk operations
    async def bulk_create_tasks(self, tasks: List[Task]) -> List[Task]:
        """Create multiple tasks (default implementation)"""
        created_tasks = []
        for task in tasks:
            created_task = await self.create_task(task)
            created_tasks.append(created_task)
        return created_tasks
    
    async def bulk_update_tasks(self, tasks: List[Task]) -> List[Task]:
        """Update multiple tasks (default implementation)"""
        updated_tasks = []
        for task in tasks:
            updated_task = await self.update_task(task)
            updated_tasks.append(updated_task)
        return updated_tasks
    
    # Migration and backup
    async def export_data(self) -> Dict[str, Any]:
        """Export all data (default implementation)"""
        # This is a basic implementation that subclasses can override
        data = {
            'tasks': [],
            'projects': [],
            'users': [],
            'version': '1.0.0',
            'exported_at': None
        }
        return data
    
    async def import_data(self, data: Dict[str, Any]) -> bool:
        """Import data (default implementation)"""
        # This is a basic implementation that subclasses can override
        try:
            # Import users first
            for user_data in data.get('users', []):
                user = User(**user_data)
                await self.create_user(user)
            
            # Import projects
            for project_data in data.get('projects', []):
                project = Project(**project_data)
                await self.create_project(project)
            
            # Import tasks
            for task_data in data.get('tasks', []):
                task = Task(**task_data)
                await self.create_task(task)
            
            return True
        except Exception as e:
            print(f"Import failed: {e}")
            return False