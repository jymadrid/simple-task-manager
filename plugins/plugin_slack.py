"""
Example plugin: Slack integration for TaskForge
"""

import asyncio
from typing import Any, Dict

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from taskforge.core.task import Task, TaskStatus
from taskforge.core.user import User
from taskforge.plugins import NotificationPlugin, PluginHook, PluginMetadata


class SlackIntegrationPlugin(NotificationPlugin):
    """Plugin for Slack notifications and integration"""

    def __init__(self):
        super().__init__()
        self.slack_client = None
        self.settings = {
            "bot_token": "",
            "default_channel": "#taskforge",
            "mention_users": True,
            "notify_on_create": True,
            "notify_on_complete": True,
            "notify_on_overdue": True,
        }

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Slack Integration",
            version="1.0.0",
            description="Send task notifications to Slack channels",
            author="TaskForge Community",
            email="plugins@taskforge.dev",
            website="https://github.com/taskforge-community/plugin-slack",
            dependencies=["slack-sdk>=3.20.0"],
            min_taskforge_version="1.0.0",
        )

    def on_activate(self):
        """Initialize Slack client when plugin is activated"""
        if self.settings["bot_token"]:
            self.slack_client = WebClient(token=self.settings["bot_token"])

    def configure(self, settings: Dict[str, Any]):
        """Configure plugin settings"""
        self.settings.update(settings)
        if self.enabled and self.settings["bot_token"]:
            self.slack_client = WebClient(token=self.settings["bot_token"])

    @PluginHook("task_created", priority=50)
    def on_task_created(self, task: Task, user: User, **kwargs):
        """Send notification when task is created"""
        if not self.settings["notify_on_create"] or not self.slack_client:
            return

        message = self._format_task_created_message(task, user)
        self._send_slack_message(message, task.project_id)

    @PluginHook("task_status_changed", priority=50)
    def on_task_status_changed(
        self, task: Task, old_status: str, new_status: str, user: User, **kwargs
    ):
        """Send notification when task status changes"""
        if new_status == TaskStatus.DONE.value and self.settings["notify_on_complete"]:
            message = self._format_task_completed_message(task, user)
            self._send_slack_message(message, task.project_id)

    @PluginHook("task_due_reminder", priority=50)
    def send_due_reminder(self, task: Task, user: User, **kwargs):
        """Send due date reminder to Slack"""
        if not self.settings["notify_on_overdue"] or not self.slack_client:
            return

        message = self._format_due_reminder_message(task, user)
        self._send_slack_message(message, task.project_id, urgent=True)

    @PluginHook("send_notification", priority=50)
    def send_notification(self, message: str, user: User, **kwargs):
        """Send general notification to Slack"""
        if not self.slack_client:
            return

        channel = kwargs.get("channel", self.settings["default_channel"])
        self._send_slack_message(message, channel)

    def _format_task_created_message(self, task: Task, user: User) -> str:
        """Format task creation message"""
        user_mention = (
            f"<@{user.username}>" if self.settings["mention_users"] else user.username
        )

        message = f"🆕 New task created by {user_mention}\n"
        message += f"*{task.title}*\n"

        if task.description:
            message += f"_{task.description}_\n"

        message += f"Priority: {task.priority.value.title()}\n"
        message += f"Status: {task.status.value.replace('_', ' ').title()}\n"

        if task.due_date:
            message += f"Due: {task.due_date.strftime('%Y-%m-%d %H:%M')}\n"

        return message

    def _format_task_completed_message(self, task: Task, user: User) -> str:
        """Format task completion message"""
        user_mention = (
            f"<@{user.username}>" if self.settings["mention_users"] else user.username
        )

        message = f"✅ Task completed by {user_mention}\n"
        message += f"*{task.title}*\n"

        if task.time_tracking.actual_hours > 0:
            message += f"Time spent: {task.time_tracking.actual_hours:.1f} hours\n"

        return message

    def _format_due_reminder_message(self, task: Task, user: User) -> str:
        """Format due date reminder message"""
        user_mention = (
            f"<@{user.username}>" if self.settings["mention_users"] else user.username
        )

        days_overdue = task.days_until_due()
        if days_overdue is not None and days_overdue < 0:
            message = f"🚨 OVERDUE: Task is {abs(days_overdue)} days overdue!\n"
        else:
            message = f"⏰ Reminder: Task is due soon!\n"

        message += f"Assigned to: {user_mention}\n"
        message += f"*{task.title}*\n"
        message += f"Due: {task.due_date.strftime('%Y-%m-%d %H:%M')}\n"
        message += f"Priority: {task.priority.value.title()}\n"

        return message

    def _send_slack_message(
        self, message: str, channel_or_project: str = None, urgent: bool = False
    ):
        """Send message to Slack"""
        if not self.slack_client:
            return

        try:
            # Determine channel
            channel = channel_or_project or self.settings["default_channel"]
            if not channel.startswith("#") and not channel.startswith("@"):
                channel = f"#{channel}"

            # Add urgency indicators
            if urgent:
                message = f"<!here> {message}"

            # Send message
            response = self.slack_client.chat_postMessage(
                channel=channel, text=message, parse="full"
            )

            return response

        except SlackApiError as e:
            print(f"Slack API Error: {e.response['error']}")
        except Exception as e:
            print(f"Error sending Slack message: {e}")

    def create_task_from_slash_command(
        self, command_text: str, user_id: str
    ) -> Dict[str, Any]:
        """Handle /taskforge slash command to create tasks"""
        # Parse command: /taskforge create "Task title" priority:high due:2024-01-15
        # This would be called by a Slack slash command handler

        parts = command_text.split()
        if not parts or parts[0] != "create":
            return {
                "error": 'Invalid command. Use: /taskforge create "Title" [options]'
            }

        # Parse task creation from Slack command
        # Implementation would parse the command and create a task
        # This is a placeholder for the actual implementation

        return {"success": True, "message": "Task created successfully!"}


# Plugin entry point
def get_plugin_class():
    """Entry point for plugin loading"""
    return SlackIntegrationPlugin
