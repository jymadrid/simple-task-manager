"""
Unit tests for Task model
"""

import pytest
from datetime import datetime, timedelta
from taskforge.core.task import Task, TaskStatus, TaskPriority, TaskType, TaskDependency


class TestTask:
    """Test cases for Task model"""
    
    def test_task_creation(self):
        """Test basic task creation"""
        task = Task(
            title="Test Task",
            description="A test task",
            priority=TaskPriority.HIGH
        )
        
        assert task.title == "Test Task"
        assert task.description == "A test task"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.TODO
        assert task.progress == 0
        assert len(task.id) > 0
        assert isinstance(task.created_at, datetime)
    
    def test_task_validation(self):
        """Test task field validation"""
        # Test empty title
        with pytest.raises(ValueError):
            Task(title="")
        
        # Test invalid progress
        with pytest.raises(ValueError):
            Task(title="Test", progress=-1)
        
        with pytest.raises(ValueError):
            Task(title="Test", progress=101)
    
    def test_task_status_updates(self):
        """Test task status updates"""
        task = Task(title="Test Task")
        
        # Test status change
        task.update_status(TaskStatus.IN_PROGRESS, "user123")
        assert task.status == TaskStatus.IN_PROGRESS
        assert len(task.activity_log) == 1
        assert task.activity_log[0]["action"] == "status_changed"
        
        # Test completion
        task.update_status(TaskStatus.DONE, "user123")
        assert task.status == TaskStatus.DONE
        assert task.completed_at is not None
        assert task.progress == 100
    
    def test_progress_updates(self):
        """Test task progress updates"""
        task = Task(title="Test Task")
        
        # Test progress update
        task.update_progress(50, "user123")
        assert task.progress == 50
        assert len(task.activity_log) == 1
        
        # Test auto-completion at 100%
        task.update_progress(100, "user123")
        assert task.progress == 100
        assert task.status == TaskStatus.DONE
        assert task.completed_at is not None
    
    def test_tag_management(self):
        """Test tag addition and removal"""
        task = Task(title="Test Task")
        
        # Add tags
        task.add_tag("urgent")
        task.add_tag("frontend")
        assert "urgent" in task.tags
        assert "frontend" in task.tags
        assert len(task.activity_log) == 2
        
        # Remove tag
        task.remove_tag("urgent")
        assert "urgent" not in task.tags
        assert "frontend" in task.tags
    
    def test_dependency_management(self):
        """Test task dependency management"""
        task = Task(title="Test Task")
        
        # Add dependency
        task.add_dependency("task-123", "blocks")
        assert len(task.dependencies) == 1
        assert task.dependencies[0].task_id == "task-123"
        assert task.dependencies[0].dependency_type == "blocks"
        
        # Remove dependency
        task.remove_dependency("task-123")
        assert len(task.dependencies) == 0
    
    def test_time_tracking(self):
        """Test time tracking functionality"""
        task = Task(title="Test Task")
        
        # Add time entry
        task.add_time_entry(2.5, "Working on implementation", "user123")
        
        assert task.time_tracking.actual_hours == 2.5
        assert len(task.time_tracking.time_entries) == 1
        assert task.time_tracking.time_entries[0]["hours"] == 2.5
        assert task.time_tracking.time_entries[0]["description"] == "Working on implementation"
    
    def test_overdue_detection(self):
        """Test overdue task detection"""
        # Task with future due date
        future_date = datetime.utcnow() + timedelta(days=1)
        task1 = Task(title="Future Task", due_date=future_date)
        assert not task1.is_overdue()
        
        # Task with past due date
        past_date = datetime.utcnow() - timedelta(days=1)
        task2 = Task(title="Past Task", due_date=past_date)
        assert task2.is_overdue()
        
        # Completed task should not be overdue
        task3 = Task(title="Completed Task", due_date=past_date, status=TaskStatus.DONE)
        assert not task3.is_overdue()
    
    def test_days_until_due(self):
        """Test days until due calculation"""
        # Task with no due date
        task1 = Task(title="No Due Date")
        assert task1.days_until_due() is None
        
        # Task due in 5 days
        future_date = datetime.utcnow() + timedelta(days=5)
        task2 = Task(title="Future Task", due_date=future_date)
        assert task2.days_until_due() == 5
        
        # Overdue task
        past_date = datetime.utcnow() - timedelta(days=3)
        task3 = Task(title="Overdue Task", due_date=past_date)
        assert task3.days_until_due() == -3
    
    def test_blocked_dependencies(self):
        """Test blocked dependencies retrieval"""
        task = Task(title="Test Task")
        
        # Add various dependency types
        task.add_dependency("task-1", "blocks")
        task.add_dependency("task-2", "subtask")
        task.add_dependency("task-3", "blocks")
        
        blocked_deps = task.get_blocked_dependencies()
        assert len(blocked_deps) == 2
        assert "task-1" in blocked_deps
        assert "task-3" in blocked_deps
        assert "task-2" not in blocked_deps
    
    def test_activity_logging(self):
        """Test activity logging"""
        task = Task(title="Test Task")
        
        # Various actions should log activity
        task.add_tag("test")
        task.update_status(TaskStatus.IN_PROGRESS)
        task.update_progress(50)
        task.add_time_entry(1.0, "Test work")
        
        assert len(task.activity_log) == 4
        
        actions = [entry["action"] for entry in task.activity_log]
        assert "tag_added" in actions
        assert "status_changed" in actions
        assert "progress_updated" in actions
        assert "time_logged" in actions
    
    def test_task_serialization(self):
        """Test task serialization to dict"""
        task = Task(
            title="Test Task",
            description="A test task",
            priority=TaskPriority.HIGH,
            tags={"urgent", "frontend"}
        )
        
        task_dict = task.to_dict()
        
        assert isinstance(task_dict, dict)
        assert task_dict["title"] == "Test Task"
        assert task_dict["priority"] == "high"
        assert isinstance(task_dict["tags"], list)  # Sets converted to lists
        assert "urgent" in task_dict["tags"]
    
    def test_task_string_representation(self):
        """Test task string representations"""
        task = Task(title="Test Task", status=TaskStatus.IN_PROGRESS)
        
        str_repr = str(task)
        assert "Test Task" in str_repr
        assert "in_progress" in str_repr
        assert task.id[:8] in str_repr
        
        repr_str = repr(task)
        assert "Task" in repr_str
        assert task.id[:8] in repr_str
    
    def test_custom_fields(self):
        """Test custom fields functionality"""
        task = Task(
            title="Test Task",
            custom_fields={
                "story_points": 5,
                "sprint": "Sprint 1",
                "reviewer": "john.doe"
            }
        )
        
        assert task.custom_fields["story_points"] == 5
        assert task.custom_fields["sprint"] == "Sprint 1"
        assert task.custom_fields["reviewer"] == "john.doe"
    
    def test_external_integration_data(self):
        """Test external integration data"""
        task = Task(
            title="Test Task",
            external_links={
                "github": "https://github.com/org/repo/issues/123",
                "jira": "https://company.atlassian.net/browse/PROJ-123"
            },
            integration_data={
                "github_issue_id": 123,
                "jira_key": "PROJ-123"
            }
        )
        
        assert "github" in task.external_links
        assert "jira" in task.external_links
        assert task.integration_data["github_issue_id"] == 123