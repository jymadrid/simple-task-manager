"""
Test configuration and utilities
"""

import pytest
import asyncio
import tempfile
import shutil
from typing import Generator, AsyncGenerator
from pathlib import Path

from taskforge.core.manager import TaskManager
from taskforge.core.task import Task, TaskStatus, TaskPriority
from taskforge.core.project import Project
from taskforge.core.user import User, UserRole
from taskforge.storage.json_storage import JsonStorage


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
async def storage(temp_dir: Path) -> AsyncGenerator[JsonStorage, None]:
    """Create a test storage instance"""
    storage = JsonStorage(str(temp_dir))
    await storage.initialize()
    yield storage
    await storage.cleanup()


@pytest.fixture
async def task_manager(storage: JsonStorage) -> AsyncGenerator[TaskManager, None]:
    """Create a test task manager"""
    manager = TaskManager(storage)
    yield manager


@pytest.fixture
async def sample_user(task_manager: TaskManager) -> User:
    """Create a sample user for testing"""
    user = User.create_user(
        username="testuser",
        email="test@example.com",
        password="testpassword123",
        full_name="Test User",
        role=UserRole.DEVELOPER
    )
    created_user = await task_manager.storage.create_user(user)
    return created_user


@pytest.fixture
async def sample_project(task_manager: TaskManager, sample_user: User) -> Project:
    """Create a sample project for testing"""
    project = Project(
        name="Test Project",
        description="A test project",
        owner_id=sample_user.id
    )
    created_project = await task_manager.create_project(project, sample_user.id)
    return created_project


@pytest.fixture
async def sample_task(task_manager: TaskManager, sample_user: User, sample_project: Project) -> Task:
    """Create a sample task for testing"""
    task = Task(
        title="Test Task",
        description="A test task",
        priority=TaskPriority.HIGH,
        project_id=sample_project.id,
        assigned_to=sample_user.id
    )
    created_task = await task_manager.create_task(task, sample_user.id)
    return created_task


@pytest.fixture
def sample_tasks_data():
    """Sample task data for bulk testing"""
    return [
        {
            "title": "Implement authentication",
            "description": "Add user authentication system",
            "priority": TaskPriority.HIGH,
            "status": TaskStatus.IN_PROGRESS
        },
        {
            "title": "Write unit tests",
            "description": "Create comprehensive test suite",
            "priority": TaskPriority.MEDIUM,
            "status": TaskStatus.TODO
        },
        {
            "title": "Deploy to production",
            "description": "Deploy application to production environment",
            "priority": TaskPriority.CRITICAL,
            "status": TaskStatus.BLOCKED
        },
        {
            "title": "Update documentation",
            "description": "Update API documentation",
            "priority": TaskPriority.LOW,
            "status": TaskStatus.DONE
        }
    ]


# Test utilities
class TestHelper:
    """Helper class for test utilities"""
    
    @staticmethod
    async def create_tasks(manager: TaskManager, user_id: str, 
                          project_id: str, count: int = 10) -> list[Task]:
        """Create multiple test tasks"""
        tasks = []
        for i in range(count):
            task = Task(
                title=f"Test Task {i+1}",
                description=f"Description for test task {i+1}",
                priority=TaskPriority.MEDIUM,
                project_id=project_id,
                assigned_to=user_id
            )
            created_task = await manager.create_task(task, user_id)
            tasks.append(created_task)
        return tasks
    
    @staticmethod
    def assert_task_equals(task1: Task, task2: Task, ignore_fields: list = None):
        """Assert that two tasks are equal, ignoring specified fields"""
        ignore_fields = ignore_fields or ['updated_at', 'activity_log']
        
        task1_dict = task1.dict()
        task2_dict = task2.dict()
        
        for field in ignore_fields:
            task1_dict.pop(field, None)
            task2_dict.pop(field, None)
        
        assert task1_dict == task2_dict
    
    @staticmethod
    def mock_datetime(monkeypatch, mock_datetime):
        """Mock datetime for testing"""
        from unittest.mock import Mock
        mock_dt = Mock()
        mock_dt.utcnow.return_value = mock_datetime
        monkeypatch.setattr("taskforge.core.task.datetime", mock_dt)
        monkeypatch.setattr("taskforge.core.project.datetime", mock_dt)
        monkeypatch.setattr("taskforge.core.user.datetime", mock_dt)