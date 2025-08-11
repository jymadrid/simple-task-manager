"""
Unit tests for Storage backends
"""

import pytest
import asyncio
import tempfile
import os
import shutil
from datetime import datetime, timedelta

from taskforge.core.task import Task, TaskStatus, TaskPriority
from taskforge.core.project import Project, ProjectStatus
from taskforge.core.user import User, UserRole
from taskforge.core.manager import TaskQuery
from taskforge.storage.json_storage import JsonStorage


class TestJsonStorage:
    """Test cases for JSON storage backend"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    async def storage(self, temp_dir):
        """Create and initialize a JSON storage backend"""
        storage = JsonStorage(temp_dir)
        await storage.initialize()
        yield storage
        await storage.cleanup()
    
    @pytest.mark.asyncio
    async def test_task_crud_operations(self, storage):
        """Test basic CRUD operations for tasks"""
        # Create a task
        task = Task(
            title="Test Task",
            description="A test task",
            priority=TaskPriority.HIGH
        )
        
        created_task = await storage.create_task(task)
        assert created_task.id == task.id
        assert created_task.title == "Test Task"
        
        # Read the task
        retrieved_task = await storage.get_task(task.id)
        assert retrieved_task is not None
        assert retrieved_task.title == "Test Task"
        assert retrieved_task.priority == TaskPriority.HIGH
        
        # Update the task
        task.title = "Updated Test Task"
        task.status = TaskStatus.IN_PROGRESS
        updated_task = await storage.update_task(task)
        assert updated_task.title == "Updated Test Task"
        assert updated_task.status == TaskStatus.IN_PROGRESS
        
        # Delete the task
        deleted = await storage.delete_task(task.id)
        assert deleted is True
        
        # Verify deletion
        deleted_task = await storage.get_task(task.id)
        assert deleted_task is None
    
    @pytest.mark.asyncio
    async def test_task_search(self, storage):
        """Test task search functionality"""
        # Create multiple test tasks
        tasks = [
            Task(title="Frontend Bug", priority=TaskPriority.HIGH, status=TaskStatus.TODO),
            Task(title="Backend Feature", priority=TaskPriority.MEDIUM, status=TaskStatus.IN_PROGRESS),
            Task(title="Database Optimization", priority=TaskPriority.LOW, status=TaskStatus.DONE),
            Task(title="UI Design", priority=TaskPriority.HIGH, status=TaskStatus.TODO),
        ]
        
        for task in tasks:
            await storage.create_task(task)
        
        # Search by status
        query = TaskQuery(status=[TaskStatus.TODO])
        todo_tasks = await storage.search_tasks(query, "test-user")
        assert len(todo_tasks) == 2
        
        # Search by priority
        query = TaskQuery(priority=[TaskPriority.HIGH])
        high_priority_tasks = await storage.search_tasks(query, "test-user")
        assert len(high_priority_tasks) == 2
        
        # Search by text
        query = TaskQuery(search_text="Backend")
        backend_tasks = await storage.search_tasks(query, "test-user")
        assert len(backend_tasks) == 1
        assert backend_tasks[0].title == "Backend Feature"
        
        # Combined search
        query = TaskQuery(
            status=[TaskStatus.TODO],
            priority=[TaskPriority.HIGH]
        )
        filtered_tasks = await storage.search_tasks(query, "test-user")
        assert len(filtered_tasks) == 2
    
    @pytest.mark.asyncio
    async def test_project_crud_operations(self, storage):
        """Test basic CRUD operations for projects"""
        # Create a project
        project = Project(
            name="Test Project",
            description="A test project",
            owner_id="user-123"
        )
        
        created_project = await storage.create_project(project)
        assert created_project.id == project.id
        assert created_project.name == "Test Project"
        
        # Read the project
        retrieved_project = await storage.get_project(project.id)
        assert retrieved_project is not None
        assert retrieved_project.name == "Test Project"
        
        # Update the project
        project.name = "Updated Project"
        project.status = ProjectStatus.ACTIVE
        updated_project = await storage.update_project(project)
        assert updated_project.name == "Updated Project"
        assert updated_project.status == ProjectStatus.ACTIVE
        
        # Delete the project
        deleted = await storage.delete_project(project.id)
        assert deleted is True
        
        # Verify deletion
        deleted_project = await storage.get_project(project.id)
        assert deleted_project is None
    
    @pytest.mark.asyncio
    async def test_user_crud_operations(self, storage):
        """Test basic CRUD operations for users"""
        # Create a user
        user = User.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User"
        )
        
        created_user = await storage.create_user(user)
        assert created_user.id == user.id
        assert created_user.username == "testuser"
        
        # Read the user
        retrieved_user = await storage.get_user(user.id)
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
        assert retrieved_user.email == "test@example.com"
        
        # Get by username
        user_by_username = await storage.get_user_by_username("testuser")
        assert user_by_username is not None
        assert user_by_username.id == user.id
        
        # Get by email
        user_by_email = await storage.get_user_by_email("test@example.com")
        assert user_by_email is not None
        assert user_by_email.id == user.id
        
        # Update the user
        user.full_name = "Updated User"
        user.is_verified = True
        updated_user = await storage.update_user(user)
        assert updated_user.full_name == "Updated User"
        assert updated_user.is_verified is True
        
        # Delete the user
        deleted = await storage.delete_user(user.id)
        assert deleted is True
        
        # Verify deletion
        deleted_user = await storage.get_user(user.id)
        assert deleted_user is None
    
    @pytest.mark.asyncio
    async def test_bulk_operations(self, storage):
        """Test bulk operations"""
        # Create multiple tasks
        tasks = [
            Task(title=f"Task {i}", priority=TaskPriority.MEDIUM)
            for i in range(5)
        ]
        
        # Bulk create
        created_tasks = await storage.bulk_create_tasks(tasks)
        assert len(created_tasks) == 5
        
        # Update all tasks
        for task in created_tasks:
            task.status = TaskStatus.IN_PROGRESS
        
        # Bulk update
        updated_tasks = await storage.bulk_update_tasks(created_tasks)
        assert len(updated_tasks) == 5
        assert all(task.status == TaskStatus.IN_PROGRESS for task in updated_tasks)
        
        # Bulk delete
        task_ids = [task.id for task in created_tasks]
        deleted_count = await storage.bulk_delete_tasks(task_ids)
        assert deleted_count == 5
    
    @pytest.mark.asyncio
    async def test_statistics(self, storage):
        """Test statistics functionality"""
        # Create test data
        user = User.create_user("testuser", "test@example.com", "pass")
        await storage.create_user(user)
        
        project = Project(name="Test Project", owner_id=user.id)
        await storage.create_project(project)
        
        # Create tasks with different statuses
        tasks = [
            Task(title="Task 1", status=TaskStatus.TODO, assigned_to=user.id, project_id=project.id),
            Task(title="Task 2", status=TaskStatus.IN_PROGRESS, assigned_to=user.id, project_id=project.id),
            Task(title="Task 3", status=TaskStatus.DONE, assigned_to=user.id, project_id=project.id),
            Task(title="Task 4", status=TaskStatus.DONE, assigned_to=user.id, project_id=project.id),
        ]
        
        for task in tasks:
            await storage.create_task(task)
        
        # Get statistics
        stats = await storage.get_task_statistics(project_id=project.id)
        
        assert stats['total_tasks'] == 4
        assert stats['completed_tasks'] == 2
        assert stats['in_progress_tasks'] == 1
        assert stats['completion_rate'] == 0.5
    
    @pytest.mark.asyncio
    async def test_error_handling(self, storage):
        """Test error handling"""
        # Test creating duplicate task
        task = Task(title="Test Task")
        await storage.create_task(task)
        
        with pytest.raises(ValueError):
            await storage.create_task(task)  # Should raise error for duplicate
        
        # Test updating non-existent task
        non_existent_task = Task(title="Non-existent", id="non-existent-id")
        with pytest.raises(ValueError):
            await storage.update_task(non_existent_task)
        
        # Test deleting non-existent task
        deleted = await storage.delete_task("non-existent-id")
        assert deleted is False
    
    @pytest.mark.asyncio
    async def test_data_persistence(self, temp_dir):
        """Test data persistence across storage instances"""
        # Create first storage instance
        storage1 = JsonStorage(temp_dir)
        await storage1.initialize()
        
        # Create test data
        task = Task(title="Persistent Task")
        await storage1.create_task(task)
        await storage1.cleanup()
        
        # Create second storage instance
        storage2 = JsonStorage(temp_dir)
        await storage2.initialize()
        
        # Verify data persistence
        retrieved_task = await storage2.get_task(task.id)
        assert retrieved_task is not None
        assert retrieved_task.title == "Persistent Task"
        
        await storage2.cleanup()
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, storage):
        """Test concurrent access to storage"""
        async def create_task(i):
            task = Task(title=f"Concurrent Task {i}")
            return await storage.create_task(task)
        
        # Create multiple tasks concurrently
        tasks = await asyncio.gather(*[create_task(i) for i in range(10)])
        
        assert len(tasks) == 10
        assert len(set(task.id for task in tasks)) == 10  # All should have unique IDs
        
        # Verify all tasks were created
        query = TaskQuery(limit=20)
        all_tasks = await storage.search_tasks(query, "test-user")
        assert len(all_tasks) >= 10
    
    @pytest.mark.asyncio
    async def test_date_filtering(self, storage):
        """Test date-based filtering"""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        # Create tasks with different dates
        tasks = [
            Task(title="Old Task", due_date=yesterday),
            Task(title="Current Task", due_date=now),
            Task(title="Future Task", due_date=tomorrow),
        ]
        
        for task in tasks:
            await storage.create_task(task)
        
        # Test due_before filter
        query = TaskQuery(due_before=now)
        past_tasks = await storage.search_tasks(query, "test-user")
        assert len(past_tasks) >= 1
        
        # Test due_after filter
        query = TaskQuery(due_after=now)
        future_tasks = await storage.search_tasks(query, "test-user")
        assert len(future_tasks) >= 1
    
    @pytest.mark.asyncio
    async def test_pagination(self, storage):
        """Test pagination functionality"""
        # Create many tasks
        tasks = [Task(title=f"Task {i:03d}") for i in range(25)]
        for task in tasks:
            await storage.create_task(task)
        
        # Test first page
        query = TaskQuery(limit=10, offset=0)
        page1 = await storage.search_tasks(query, "test-user")
        assert len(page1) == 10
        
        # Test second page
        query = TaskQuery(limit=10, offset=10)
        page2 = await storage.search_tasks(query, "test-user")
        assert len(page2) == 10
        
        # Test third page
        query = TaskQuery(limit=10, offset=20)
        page3 = await storage.search_tasks(query, "test-user")
        assert len(page3) >= 5  # At least 5 remaining tasks
        
        # Ensure no overlap between pages
        page1_ids = {task.id for task in page1}
        page2_ids = {task.id for task in page2}
        assert page1_ids.isdisjoint(page2_ids)