from datetime import datetime, timedelta, timezone

import pytest

from taskforge.core.manager import TaskManager
from taskforge.core.queries import TaskQuery
from taskforge.core.task import Task, TaskStatus
from taskforge.core.user import UserRole
from taskforge.storage.json_storage import JSONStorage
from taskforge.web.helpers import (
    display_value,
    ensure_dashboard_user,
    is_overdue_task,
    is_upcoming_task,
)


@pytest.mark.asyncio
async def test_ensure_dashboard_user_initializes_storage_and_persists_user(tmp_path):
    storage = JSONStorage(str(tmp_path))
    manager = TaskManager(storage)

    user = await ensure_dashboard_user(manager, "dashboard_user")

    assert user.id == "dashboard_user"
    assert user.role == UserRole.MANAGER
    assert (tmp_path / "users.json").exists()

    second_storage = JSONStorage(str(tmp_path))
    await second_storage.initialize()
    persisted_user = await second_storage.get_user("dashboard_user")

    assert persisted_user is not None
    assert persisted_user.username == "dashboard_user"
    assert persisted_user.has_permission("task:create")

    await storage.cleanup()
    await second_storage.cleanup()


@pytest.mark.asyncio
async def test_ensure_dashboard_user_does_not_reload_dirty_storage(tmp_path):
    storage = JSONStorage(str(tmp_path), save_delay=60)
    manager = TaskManager(storage)
    try:
        user = await ensure_dashboard_user(manager, "dashboard_user")

        await manager.create_task(Task(title="Unsaved Dashboard Task"), user.id)
        await ensure_dashboard_user(manager, "dashboard_user")

        tasks = await manager.search_tasks(TaskQuery(limit=10), user.id)

        assert [task.title for task in tasks] == ["Unsaved Dashboard Task"]
    finally:
        await storage.cleanup()


def test_due_date_classification_handles_naive_and_aware_datetimes():
    now = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
    overdue = Task(title="Overdue", due_date=now - timedelta(hours=1))
    upcoming = Task(
        title="Upcoming",
        due_date=(now + timedelta(days=2)).replace(tzinfo=None),
    )
    completed = Task(
        title="Completed",
        status=TaskStatus.DONE,
        due_date=now - timedelta(days=1),
    )

    assert is_overdue_task(overdue, now)
    assert not is_overdue_task(upcoming, now)
    assert not is_overdue_task(completed, now)
    assert is_upcoming_task(upcoming, now=now)
    assert not is_upcoming_task(overdue, now=now)


def test_display_value_handles_enums_and_plain_strings():
    assert display_value(TaskStatus.DONE) == "done"
    assert display_value("in_progress") == "in_progress"
