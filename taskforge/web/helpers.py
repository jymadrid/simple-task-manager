"""Shared helpers for Streamlit dashboards."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from taskforge.core.manager import TaskManager
from taskforge.core.task import Task, TaskStatus
from taskforge.core.user import User, UserRole


def display_value(value: Any) -> str:
    """Return a stable display value for enum-like or plain-string fields."""
    return str(getattr(value, "value", value))


def as_utc(value: datetime) -> datetime:
    """Normalize a datetime to timezone-aware UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


async def ensure_dashboard_user(
    manager: TaskManager,
    user_id: str = "default_user",
) -> User:
    """Initialize dashboard storage and ensure a usable local user exists."""
    if not getattr(manager.storage, "_taskforge_web_initialized", False):
        await manager.storage.initialize()
        setattr(manager.storage, "_taskforge_web_initialized", True)

    user = await manager.storage.get_user(user_id)
    if user:
        return user

    user = User.create_user(
        username=user_id,
        email=f"{user_id}@taskforge.local",
        password=secrets.token_urlsafe(32),
        role=UserRole.MANAGER,
    )
    user.id = user_id
    await manager.storage.create_user(user)

    force_save = getattr(manager.storage, "force_save", None)
    if callable(force_save):
        await force_save()

    return user


def is_overdue_task(task: Task, now: Optional[datetime] = None) -> bool:
    """Return whether a task is overdue using UTC-safe comparisons."""
    if task.status in {TaskStatus.DONE, TaskStatus.CANCELLED, "done", "cancelled"}:
        return False
    if not task.due_date:
        return False

    current_time = as_utc(now or datetime.now(timezone.utc))
    return as_utc(task.due_date) < current_time


def is_upcoming_task(
    task: Task,
    days: int = 7,
    now: Optional[datetime] = None,
) -> bool:
    """Return whether a task is due within the next number of days."""
    if task.status in {TaskStatus.DONE, TaskStatus.CANCELLED, "done", "cancelled"}:
        return False
    if not task.due_date:
        return False

    current_time = as_utc(now or datetime.now(timezone.utc))
    due_date = as_utc(task.due_date)
    return current_time <= due_date <= current_time + timedelta(days=days)
