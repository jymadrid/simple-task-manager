import pytest

from taskforge.core.task import Task
from taskforge.core.user import User
from taskforge.utils.notifications import (
    Notification,
    NotificationChannel,
    NotificationManager,
    NotificationTemplate,
    NotificationType,
)


class RecordingChannel(NotificationChannel):
    def __init__(self, available: bool = True) -> None:
        self.available = available
        self.sent: list[Notification] = []

    async def send(self, notification: Notification, recipient: User) -> bool:
        self.sent.append(notification)
        return True

    def is_available(self) -> bool:
        return self.available


def test_notification_dataclasses_use_independent_defaults():
    first = NotificationTemplate(subject="One", body_text="Body")
    second = NotificationTemplate(subject="Two", body_text="Body")
    first.variables["name"] = "Alice"

    notification = Notification(
        id="n1",
        recipient_id="u1",
        notification_type=NotificationType.REMINDER,
        subject="Reminder",
        content="Content",
    )

    assert second.variables == {}
    assert notification.created_at.tzinfo is not None
    assert notification.metadata == {}


@pytest.mark.asyncio
async def test_due_notifications_handle_missing_due_date():
    manager = NotificationManager()
    channel = RecordingChannel()
    manager.add_channel("in_app", channel)

    task = Task(title="No deadline", priority="high")
    assignee = User.create_user("assignee", "assignee@example.com", "password")

    due_result = await manager.send_task_due_soon(task, assignee, days_until_due=1)
    overdue_result = await manager.send_task_overdue(task, assignee, days_overdue=2)

    assert due_result == {"in_app": True}
    assert overdue_result == {"in_app": True}
    assert "No due date" in channel.sent[0].content
    assert "No due date" in channel.sent[1].content


@pytest.mark.asyncio
async def test_bulk_notifications_collect_channel_results():
    manager = NotificationManager()
    channel = RecordingChannel()
    manager.add_channel("email", channel)
    user = User.create_user("bulkuser", "bulkuser@example.com", "password")
    manager.set_user_preferences(user.id, {NotificationType.REMINDER: ["email"]})
    manager.set_template(
        NotificationType.REMINDER,
        NotificationTemplate(subject="Reminder {id}", body_text="Task {id}"),
    )

    results = await manager.send_bulk_notifications(
        [(NotificationType.REMINDER, user, {"id": "42"})]
    )

    assert results == {f"{user.id}_reminder": {"email": True}}
    assert channel.sent[0].subject == "Reminder 42"
