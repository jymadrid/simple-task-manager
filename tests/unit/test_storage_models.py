from datetime import datetime, timezone

from taskforge.core.project import Project, ProjectStatus
from taskforge.core.task import Task, TaskPriority, TaskStatus, TaskType
from taskforge.core.user import Permission, User, UserRole
from taskforge.storage.models import ProjectModel, TaskModel, UserModel


def test_task_model_round_trips_full_task_data():
    task = Task(
        title="Persist me",
        description="Round trip",
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.HIGH,
        task_type=TaskType.FEATURE,
        tags={"Backend", "API"},
        labels=["release"],
        custom_fields={"estimate": 3},
        progress=40,
        due_date=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    task.add_dependency("blocked-by")
    task.add_time_entry(1.5, "implementation")

    restored = TaskModel.from_task(task).to_task()

    assert restored.id == task.id
    assert restored.status == TaskStatus.IN_PROGRESS
    assert restored.priority == TaskPriority.HIGH
    assert restored.task_type == TaskType.FEATURE
    assert restored.tags == task.tags
    assert restored.dependencies[0].task_id == "blocked-by"
    assert restored.time_tracking.actual_hours == 1.5
    assert restored.custom_fields == {"estimate": 3}


def test_project_model_round_trips_project_data():
    project = Project(
        name="Storage Project",
        owner_id="owner-1",
        status=ProjectStatus.ACTIVE,
        team_members={"owner-1", "user-2"},
        tags={"ops"},
        progress=65,
        task_count=10,
        completed_task_count=6,
        settings={"visibility": "team"},
    )

    restored = ProjectModel.from_project(project).to_project()

    assert restored.id == project.id
    assert restored.status == ProjectStatus.ACTIVE
    assert restored.team_members == {"owner-1", "user-2"}
    assert restored.tags == {"ops"}
    assert restored.progress == 65
    assert restored.settings == {"visibility": "team"}


def test_user_model_round_trips_user_data():
    user = User.create_user(
        "manager",
        "manager@example.com",
        "password",
        full_name="Project Manager",
        role=UserRole.MANAGER,
    )
    user.grant_permission(Permission.SYSTEM_CONFIG)
    user.teams.add("project-1")
    user.update_setting("theme", "dark")

    restored = UserModel.from_user(user).to_user()

    assert restored.id == user.id
    assert restored.username == "manager"
    assert restored.role == UserRole.MANAGER
    assert Permission.SYSTEM_CONFIG in restored.custom_permissions
    assert restored.teams == {"project-1"}
    assert restored.settings == {"theme": "dark"}
