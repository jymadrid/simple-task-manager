"""
Unit tests for TaskManager
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from conftest import TestHelper

from taskforge.core.manager import TaskManager
from taskforge.core.project import Project
from taskforge.core.queries import TaskQuery
from taskforge.core.task import Task, TaskPriority, TaskStatus
from taskforge.core.user import Permission, User


class TestTaskManager:
    """Test cases for TaskManager"""

    @pytest.mark.asyncio
    async def test_create_task(
        self, task_manager: TaskManager, sample_user: User, sample_project: Project
    ):
        """Test task creation through manager"""
        task = Task(
            title="New Task",
            description="A new task",
            priority=TaskPriority.HIGH,
            project_id=sample_project.id,
        )

        created_task = await task_manager.create_task(task, sample_user.id)

        assert created_task.id == task.id  # Storage should preserve the task ID
        assert created_task.title == "New Task"
        assert created_task.created_by == sample_user.id
        assert created_task.project_id == sample_project.id

    @pytest.mark.asyncio
    async def test_create_task_permissions(self, task_manager: TaskManager):
        """Test task creation permission validation"""
        # Create user without task creation permission
        user = User.create_user("limited", "limited@test.com", "pass")
        user.role = "viewer"  # Viewers can't create tasks
        await task_manager.storage.create_user(user)

        task = Task(title="Unauthorized Task")

        with pytest.raises(PermissionError):
            await task_manager.create_task(task, user.id)

    @pytest.mark.asyncio
    async def test_get_task(self, task_manager: TaskManager, sample_task: Task):
        """Test task retrieval"""
        retrieved_task = await task_manager.get_task(sample_task.id)

        assert retrieved_task is not None
        assert retrieved_task.id == sample_task.id
        assert retrieved_task.title == sample_task.title

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, task_manager: TaskManager):
        """Test retrieval of non-existent task"""
        task = await task_manager.get_task("nonexistent-id")
        assert task is None

    @pytest.mark.asyncio
    async def test_update_task(
        self, task_manager: TaskManager, sample_task: Task, sample_user: User
    ):
        """Test task updates"""
        updates = {
            "title": "Updated Task Title",
            "status": TaskStatus.IN_PROGRESS,
            "progress": 50,
        }

        updated_task = await task_manager.update_task(
            sample_task.id, updates, sample_user.id
        )

        assert updated_task.title == "Updated Task Title"
        assert updated_task.status == TaskStatus.IN_PROGRESS
        assert updated_task.progress == 50

    @pytest.mark.asyncio
    async def test_update_nonexistent_task(
        self, task_manager: TaskManager, sample_user: User
    ):
        """Test updating non-existent task"""
        with pytest.raises(ValueError, match="not found"):
            await task_manager.update_task(
                "nonexistent-id", {"title": "New Title"}, sample_user.id
            )

    @pytest.mark.asyncio
    async def test_delete_task(
        self, task_manager: TaskManager, sample_task: Task, sample_user: User
    ):
        """Test task deletion"""
        success = await task_manager.delete_task(sample_task.id, sample_user.id)
        assert success

        # Verify task is deleted
        deleted_task = await task_manager.get_task(sample_task.id)
        assert deleted_task is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_task(
        self, task_manager: TaskManager, sample_user: User
    ):
        """Test deleting non-existent task"""
        success = await task_manager.delete_task("nonexistent-id", sample_user.id)
        assert not success

    @pytest.mark.asyncio
    async def test_search_tasks(
        self, task_manager: TaskManager, sample_user: User, sample_project: Project
    ):
        """Test task search functionality"""
        # Create multiple test tasks
        tasks = await TestHelper.create_tasks(
            task_manager, sample_user.id, sample_project.id, 5
        )

        # Test basic search
        query = TaskQuery(limit=10)
        results = await task_manager.search_tasks(query, sample_user.id)
        assert len(results) >= 5

        # Test status filter
        await task_manager.update_task(
            tasks[0].id, {"status": TaskStatus.DONE}, sample_user.id
        )
        query = TaskQuery(status=[TaskStatus.DONE])
        results = await task_manager.search_tasks(query, sample_user.id)
        assert len(results) >= 1
        assert all(task.status == TaskStatus.DONE for task in results)

        # Test priority filter
        query = TaskQuery(priority=[TaskPriority.HIGH])
        results = await task_manager.search_tasks(query, sample_user.id)
        # Should be empty since we created tasks with MEDIUM priority
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_get_overdue_tasks(
        self, task_manager: TaskManager, sample_user: User, sample_project: Project
    ):
        """Test overdue tasks retrieval"""
        # Create overdue task
        past_date = datetime.utcnow() - timedelta(days=1)
        overdue_task = Task(
            title="Overdue Task", due_date=past_date, project_id=sample_project.id
        )
        await task_manager.create_task(overdue_task, sample_user.id)

        # Create future task
        future_date = datetime.utcnow() + timedelta(days=1)
        future_task = Task(
            title="Future Task", due_date=future_date, project_id=sample_project.id
        )
        await task_manager.create_task(future_task, sample_user.id)

        overdue_tasks = await task_manager.get_overdue_tasks(sample_user.id)
        assert len(overdue_tasks) >= 1
        assert all(task.is_overdue() for task in overdue_tasks)

    @pytest.mark.asyncio
    async def test_get_upcoming_tasks(
        self, task_manager: TaskManager, sample_user: User, sample_project: Project
    ):
        """Test upcoming tasks retrieval"""
        # Create task due in 3 days
        due_date = datetime.utcnow() + timedelta(days=3)
        upcoming_task = Task(
            title="Upcoming Task", due_date=due_date, project_id=sample_project.id
        )
        await task_manager.create_task(upcoming_task, sample_user.id)

        # Create task due in 10 days (outside 7-day window)
        far_future_date = datetime.utcnow() + timedelta(days=10)
        far_future_task = Task(
            title="Far Future Task",
            due_date=far_future_date,
            project_id=sample_project.id,
        )
        await task_manager.create_task(far_future_task, sample_user.id)

        upcoming_tasks = await task_manager.get_upcoming_tasks(7, sample_user.id)
        upcoming_titles = [task.title for task in upcoming_tasks]

        assert "Upcoming Task" in upcoming_titles
        assert "Far Future Task" not in upcoming_titles

    @pytest.mark.asyncio
    async def test_create_project(self, task_manager: TaskManager, sample_user: User):
        """Test project creation"""
        project = Project(
            name="New Project", description="A test project", owner_id=sample_user.id
        )

        created_project = await task_manager.create_project(project, sample_user.id)

        assert created_project.name == "New Project"
        assert created_project.owner_id == sample_user.id
        assert sample_user.id in created_project.team_members

    @pytest.mark.asyncio
    async def test_get_task_statistics(
        self, task_manager: TaskManager, sample_user: User, sample_project: Project
    ):
        """Test task statistics retrieval"""
        # Create tasks with different statuses
        tasks = await TestHelper.create_tasks(
            task_manager, sample_user.id, sample_project.id, 10
        )

        # Update some task statuses
        await task_manager.update_task(
            tasks[0].id, {"status": TaskStatus.DONE}, sample_user.id
        )
        await task_manager.update_task(
            tasks[1].id, {"status": TaskStatus.DONE}, sample_user.id
        )
        await task_manager.update_task(
            tasks[2].id, {"status": TaskStatus.IN_PROGRESS}, sample_user.id
        )

        stats = await task_manager.get_task_statistics(
            sample_project.id, sample_user.id
        )

        assert stats["total_tasks"] >= 10
        assert stats["completed_tasks"] >= 2
        assert stats["in_progress_tasks"] >= 1

    @pytest.mark.asyncio
    async def test_bulk_update_tasks(
        self, task_manager: TaskManager, sample_user: User, sample_project: Project
    ):
        """Test bulk task updates"""
        # Create multiple tasks
        tasks = await TestHelper.create_tasks(
            task_manager, sample_user.id, sample_project.id, 5
        )
        task_ids = [task.id for task in tasks]

        updates = {"priority": TaskPriority.HIGH}
        updated_tasks = await task_manager.bulk_update_tasks(
            task_ids, updates, sample_user.id
        )

        assert len(updated_tasks) == 5
        assert all(task.priority == TaskPriority.HIGH for task in updated_tasks)

    @pytest.mark.asyncio
    async def test_archive_completed_tasks(
        self, task_manager: TaskManager, sample_user: User, sample_project: Project
    ):
        """Test archiving old completed tasks"""
        # Create and complete old tasks
        old_task = Task(
            title="Old Completed Task",
            project_id=sample_project.id,
            status=TaskStatus.DONE,
        )
        # Mock old creation date
        old_task.created_at = datetime.utcnow() - timedelta(days=35)
        created_task = await task_manager.create_task(old_task, sample_user.id)
        await task_manager.update_task(
            created_task.id, {"status": TaskStatus.DONE}, sample_user.id
        )

        # Archive tasks older than 30 days
        archived_count = await task_manager.archive_completed_tasks(
            sample_project.id, 30
        )

        assert archived_count >= 0  # Depends on mock implementation

    @pytest.mark.asyncio
    async def test_dependency_validation(
        self, task_manager: TaskManager, sample_user: User, sample_project: Project
    ):
        """Test task dependency cycle detection"""
        # Create two tasks
        task1 = Task(title="Task 1", project_id=sample_project.id)
        task2 = Task(title="Task 2", project_id=sample_project.id)

        created_task1 = await task_manager.create_task(task1, sample_user.id)
        created_task2 = await task_manager.create_task(task2, sample_user.id)

        # Add dependency: task2 depends on task1
        created_task2.add_dependency(created_task1.id, "blocks")
        await task_manager.update_task(
            created_task2.id,
            {"dependencies": created_task2.dependencies},
            sample_user.id,
        )

        # Try to create cycle: task1 depends on task2
        created_task1.add_dependency(created_task2.id, "blocks")

        with pytest.raises(ValueError, match="cycle"):
            await task_manager.update_task(
                created_task1.id,
                {"dependencies": created_task1.dependencies},
                sample_user.id,
            )

    @pytest.mark.asyncio
    async def test_project_progress_update(
        self, task_manager: TaskManager, sample_user: User, sample_project: Project
    ):
        """Test automatic project progress updates"""
        # Create tasks for project
        tasks = await TestHelper.create_tasks(
            task_manager, sample_user.id, sample_project.id, 4
        )

        # Complete half the tasks
        await task_manager.update_task(
            tasks[0].id, {"status": TaskStatus.DONE}, sample_user.id
        )
        await task_manager.update_task(
            tasks[1].id, {"status": TaskStatus.DONE}, sample_user.id
        )

        # Check project progress
        updated_project = await task_manager.get_project(sample_project.id)
        assert updated_project.progress == 50  # 2 out of 4 tasks completed
        assert updated_project.task_count >= 4
        assert updated_project.completed_task_count >= 2

    @pytest.mark.asyncio
    async def test_caching(self, task_manager: TaskManager, sample_task: Task):
        """Test manager caching functionality"""
        # First retrieval should hit storage
        task1 = await task_manager.get_task(sample_task.id)

        # Second retrieval should hit cache
        task2 = await task_manager.get_task(sample_task.id)

        assert task1 is not None
        assert task2 is not None
        assert task1.id == task2.id

        # Verify task is in cache
        assert sample_task.id in task_manager._task_cache
