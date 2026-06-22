from datetime import datetime, timezone

import pytest

from taskforge.core.queries import TaskQuery
from taskforge.core.task import Task, TaskPriority, TaskStatus, TaskType
from taskforge.core.user import User
from taskforge.storage.models import TaskModel, UserModel
from taskforge.utils.analytics import AnalyticsEngine
from taskforge.utils.auth import AuthManager
from taskforge.utils.notifications import NotificationManager
from taskforge.utils.search import SearchEngine, SearchFilter, SearchQuery, SearchResult
from taskforge.utils.values import enum_matches, enum_title, enum_value


class FakeTaskStorage:
    def __init__(self, tasks):
        self.tasks = tasks

    async def search_tasks(self, query: TaskQuery, user_id: str):
        return self.tasks


def test_value_helpers_normalize_enums_and_strings():
    assert enum_value(TaskStatus.DONE) == "done"
    assert enum_value("in_progress") == "in_progress"
    assert enum_matches("high", TaskPriority.HIGH)
    assert enum_title("in_progress") == "In Progress"


@pytest.mark.asyncio
async def test_analytics_handles_string_enum_fields():
    completed = Task(
        title="Completed",
        status="done",
        priority="high",
        task_type="feature",
        completed_at=datetime.now(timezone.utc),
        assigned_to="user-1",
    )
    in_progress = Task(
        title="In Progress",
        status="in_progress",
        priority="critical",
        task_type="bug",
        assigned_to="user-1",
    )
    completed.time_tracking.actual_hours = 2.5

    analytics = AnalyticsEngine(FakeTaskStorage([completed, in_progress]))

    stats = await analytics.get_task_statistics(user_id="user-1")
    productivity = await analytics.get_productivity_metrics("user-1", days=30)

    assert stats["completed_tasks"] == 1
    assert stats["in_progress_tasks"] == 1
    assert stats["status_distribution"] == {"done": 1, "in_progress": 1}
    assert stats["priority_distribution"] == {"high": 1, "critical": 1}
    assert stats["type_distribution"] == {"feature": 1, "bug": 1}
    assert productivity["tasks_completed"] == 1
    assert productivity["focus_score"] == 1.0
    assert productivity["time_by_type"] == {"feature": 2.5}


def test_search_engine_handles_string_enum_fields():
    task = Task(
        title="Searchable",
        status="done",
        priority="high",
        task_type="feature",
    )
    engine = SearchEngine()

    assert engine._filter_matches(
        task.status, SearchFilter("status", "eq", TaskStatus.DONE)
    )
    assert engine._filter_matches(
        task.priority,
        SearchFilter("priority", "in", [TaskPriority.HIGH, TaskPriority.CRITICAL]),
    )

    facets = engine._generate_facets([SearchResult(item=task, score=1.0)])

    assert facets["status"] == {"done": 1}
    assert facets["priority"] == {"high": 1}
    assert facets["task_type"] == {"feature": 1}


@pytest.mark.asyncio
async def test_search_index_task_handles_string_enum_fields():
    task = Task(
        title="Indexed",
        status="done",
        priority="high",
        task_type="feature",
    )
    engine = SearchEngine()

    await engine.index_task(task)

    document = engine.index.documents[f"task_{task.id}"]
    assert document["status"] == "done"
    assert document["priority"] == "high"
    assert document["task_type"] == "feature"


@pytest.mark.asyncio
async def test_search_text_rebuilds_task_from_indexed_document():
    task = Task(
        title="Indexed runtime lookup",
        status="done",
        priority="high",
        task_type="feature",
    )
    engine = SearchEngine()

    await engine.index_task(task)
    results = await engine.search_tasks(SearchQuery(text="runtime"), user_id="user-1")

    assert results.total_count == 1
    assert results.items[0].item.id == task.id
    assert results.items[0].item.status == TaskStatus.DONE


@pytest.mark.asyncio
async def test_notifications_handle_string_priority():
    manager = NotificationManager()
    task = Task(title="Assigned", priority="high")
    assignee = User.create_user("assignee", "assignee@example.com", "password")
    assigner = User.create_user("assigner", "assigner@example.com", "password")

    result = await manager.send_task_assigned(task, assignee, assigner)

    assert result == {"in_app": False}


def test_auth_and_orm_models_handle_string_enum_fields():
    user = User.create_user("viewer", "viewer@example.com", "password")
    user.role = "viewer"

    auth = AuthManager()

    assert auth.can_access_resource(user, "task", "read")
    assert not auth.can_access_resource(user, "task", "create")
    assert UserModel.from_user(user).role == "viewer"

    task = Task(title="ORM", status="done", priority="high", task_type="feature")
    task_model = TaskModel.from_task(task)

    assert task_model.status == "done"
    assert task_model.priority == "high"
    assert task_model.task_type == "feature"
