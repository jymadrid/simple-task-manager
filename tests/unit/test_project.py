"""
Unit tests for Project model
"""

from datetime import datetime, timedelta

import pytest

from taskforge.core.project import Project, ProjectStatus
from taskforge.core.user import User, UserRole


class TestProject:
    """Test cases for Project model"""

    def test_project_creation(self):
        """Test basic project creation"""
        project = Project(
            name="Test Project", description="A test project", owner_id="user-123"
        )

        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.owner_id == "user-123"
        assert project.status == ProjectStatus.PLANNING
        assert project.progress == 0
        assert len(project.id) > 0
        assert isinstance(project.created_at, datetime)

    def test_project_validation(self):
        """Test project field validation"""
        # Test empty name
        with pytest.raises(ValueError):
            Project(name="", owner_id="user-123")

        # Test invalid progress
        with pytest.raises(ValueError):
            Project(name="Test", owner_id="user-123", progress=-1)

        with pytest.raises(ValueError):
            Project(name="Test", owner_id="user-123", progress=101)

    def test_project_status_updates(self):
        """Test project status updates"""
        project = Project(name="Test Project", owner_id="user-123")

        # Test status change
        project.update_status(ProjectStatus.ACTIVE, "user-456")
        assert project.status == ProjectStatus.ACTIVE
        assert len(project.activity_log) == 1
        assert project.activity_log[0]["action"] == "status_changed"

    def test_team_member_management(self):
        """Test team member addition and removal"""
        project = Project(name="Test Project", owner_id="user-123")

        # Add team members
        project.add_member("user-456", UserRole.DEVELOPER)
        project.add_member("user-789", UserRole.MANAGER)

        assert project.is_member("user-456")
        assert project.is_member("user-789")
        assert project.is_member("user-123")  # Owner is always a member
        assert len(project.team_members) == 3  # Including owner

        # Remove team member
        project.remove_member("user-456")
        assert not project.is_member("user-456")
        assert project.is_member("user-789")
        assert len(project.team_members) == 2

    def test_owner_permissions(self):
        """Test owner cannot be removed"""
        project = Project(name="Test Project", owner_id="user-123")

        # Owner should not be removable
        with pytest.raises(ValueError):
            project.remove_member("user-123")

    def test_progress_updates(self):
        """Test project progress updates"""
        project = Project(name="Test Project", owner_id="user-123")

        # Test progress update
        project.update_progress(75, "user-123")
        assert project.progress == 75
        assert len(project.activity_log) == 1
        assert project.activity_log[0]["action"] == "progress_updated"

    def test_task_count_updates(self):
        """Test task count tracking"""
        project = Project(name="Test Project", owner_id="user-123")

        # Add tasks
        project.add_task_count(5)
        assert project.task_count == 5

        # Complete some tasks
        project.complete_task_count(2)
        assert project.completed_task_count == 2

        # Calculate completion rate
        completion_rate = project.get_completion_rate()
        assert completion_rate == 0.4  # 2/5 = 0.4

    def test_budget_tracking(self):
        """Test budget and time tracking"""
        project = Project(
            name="Test Project",
            owner_id="user-123",
            budget=10000.0,
            estimated_hours=100.0,
        )

        assert project.budget == 10000.0
        assert project.estimated_hours == 100.0
        assert project.actual_hours == 0.0

        # Add actual hours
        project.add_actual_hours(25.5)
        assert project.actual_hours == 25.5

        # Calculate budget utilization
        utilization = project.get_time_utilization()
        assert utilization == 0.255  # 25.5/100 = 0.255

    def test_project_dates(self):
        """Test project date management"""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)

        project = Project(
            name="Test Project",
            owner_id="user-123",
            start_date=start_date,
            end_date=end_date,
        )

        assert project.start_date == start_date
        assert project.end_date == end_date

        # Test duration calculation
        duration = project.get_duration_days()
        assert duration == 30

        # Test if project is active (within date range)
        assert project.is_active_period()

    def test_project_tags(self):
        """Test project tag management"""
        project = Project(name="Test Project", owner_id="user-123")

        # Add tags
        project.add_tag("web")
        project.add_tag("frontend")

        assert "web" in project.tags
        assert "frontend" in project.tags
        assert len(project.tags) == 2

        # Remove tag
        project.remove_tag("web")
        assert "web" not in project.tags
        assert "frontend" in project.tags
        assert len(project.tags) == 1

    def test_custom_fields(self):
        """Test project custom fields"""
        project = Project(
            name="Test Project",
            owner_id="user-123",
            custom_fields={
                "client": "ABC Corp",
                "contract_type": "Fixed Price",
                "priority": "High",
            },
        )

        assert project.custom_fields["client"] == "ABC Corp"
        assert project.custom_fields["contract_type"] == "Fixed Price"
        assert project.custom_fields["priority"] == "High"

    def test_project_settings(self):
        """Test project settings management"""
        project = Project(name="Test Project", owner_id="user-123")

        # Update settings
        project.update_setting("auto_assign", True)
        project.update_setting("notification_level", "all")
        project.update_setting("visibility", "private")

        assert project.get_setting("auto_assign") is True
        assert project.get_setting("notification_level") == "all"
        assert project.get_setting("visibility") == "private"
        assert project.get_setting("nonexistent") is None

    def test_activity_logging(self):
        """Test project activity logging"""
        project = Project(name="Test Project", owner_id="user-123")

        # Various actions should log activity
        project.add_member("user-456", UserRole.DEVELOPER)
        project.update_status(ProjectStatus.ACTIVE)
        project.update_progress(50)
        project.add_tag("urgent")

        assert len(project.activity_log) == 4

        actions = [entry["action"] for entry in project.activity_log]
        assert "member_added" in actions
        assert "status_changed" in actions
        assert "progress_updated" in actions
        assert "tag_added" in actions

    def test_project_health_score(self):
        """Test project health score calculation"""
        project = Project(
            name="Test Project",
            owner_id="user-123",
            start_date=datetime.utcnow() - timedelta(days=10),
            end_date=datetime.utcnow() + timedelta(days=20),
        )

        # Set some progress
        project.task_count = 100
        project.completed_task_count = 40
        project.estimated_hours = 100
        project.actual_hours = 30

        health_score = project.calculate_health_score()
        assert isinstance(health_score, float)
        assert 0.0 <= health_score <= 1.0

    def test_project_serialization(self):
        """Test project serialization to dict"""
        project = Project(
            name="Test Project",
            description="A test project",
            owner_id="user-123",
            tags={"web", "frontend"},
        )

        project_dict = project.to_dict()

        assert isinstance(project_dict, dict)
        assert project_dict["name"] == "Test Project"
        assert project_dict["owner_id"] == "user-123"
        assert isinstance(project_dict["tags"], list)  # Sets converted to lists

    def test_project_string_representation(self):
        """Test project string representations"""
        project = Project(
            name="Test Project", owner_id="user-123", status=ProjectStatus.ACTIVE
        )

        str_repr = str(project)
        assert "Test Project" in str_repr
        assert "active" in str_repr
        assert project.id[:8] in str_repr

        repr_str = repr(project)
        assert "Project" in repr_str
        assert project.id[:8] in repr_str

    def test_project_comparison(self):
        """Test project equality comparison"""
        project1 = Project(name="Test 1", owner_id="user-123")
        project2 = Project(name="Test 2", owner_id="user-456")
        project3 = Project(id=project1.id, name="Test 1", owner_id="user-123")

        # Different projects should not be equal
        assert project1 != project2

        # Same ID should be equal
        assert project1 == project3

    def test_project_archiving(self):
        """Test project archiving functionality"""
        project = Project(name="Test Project", owner_id="user-123")

        # Project starts active
        assert not project.is_archived()

        # Archive project
        project.archive("user-123")
        assert project.is_archived()
        assert project.status == ProjectStatus.ARCHIVED
        assert len(project.activity_log) == 1
        assert project.activity_log[0]["action"] == "archived"

        # Unarchive project
        project.unarchive("user-123")
        assert not project.is_archived()
        assert project.status == ProjectStatus.ACTIVE

    def test_project_role_management(self):
        """Test project-specific role management"""
        project = Project(name="Test Project", owner_id="user-123")

        # Add members with different roles
        project.add_member("dev1", UserRole.DEVELOPER)
        project.add_member("manager1", UserRole.MANAGER)

        # Get members by role
        developers = project.get_members_by_role(UserRole.DEVELOPER)
        managers = project.get_members_by_role(UserRole.MANAGER)

        assert "dev1" in developers
        assert "manager1" in managers
        assert len(developers) >= 1
        assert len(managers) >= 1

    def test_project_deadline_warning(self):
        """Test project deadline warnings"""
        # Project ending soon
        soon_end = datetime.utcnow() + timedelta(days=3)
        project1 = Project(name="Ending Soon", owner_id="user-123", end_date=soon_end)

        assert project1.days_until_deadline() == 3
        assert project1.is_deadline_approaching(days_threshold=7)

        # Project already overdue
        past_end = datetime.utcnow() - timedelta(days=2)
        project2 = Project(name="Overdue", owner_id="user-123", end_date=past_end)

        assert project2.days_until_deadline() == -2
        assert project2.is_overdue()

    def test_project_statistics(self):
        """Test project statistics calculation"""
        project = Project(name="Test Project", owner_id="user-123")

        # Set up some data
        project.task_count = 50
        project.completed_task_count = 30
        project.estimated_hours = 200
        project.actual_hours = 120
        project.add_member("user-456", UserRole.DEVELOPER)
        project.add_member("user-789", UserRole.MANAGER)

        stats = project.get_statistics()

        assert stats["task_count"] == 50
        assert stats["completed_task_count"] == 30
        assert stats["completion_rate"] == 0.6  # 30/50
        assert stats["team_size"] == 3  # Including owner
        assert stats["time_utilization"] == 0.6  # 120/200
