"""
Notification system for TaskForge
"""

import asyncio
import logging
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from taskforge.core.project import Project
from taskforge.core.task import Task
from taskforge.core.user import User

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Types of notifications"""

    TASK_ASSIGNED = "task_assigned"
    TASK_DUE_SOON = "task_due_soon"
    TASK_OVERDUE = "task_overdue"
    TASK_COMPLETED = "task_completed"
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    TEAM_INVITATION = "team_invitation"
    REMINDER = "reminder"
    SYSTEM_ALERT = "system_alert"


@dataclass
class NotificationTemplate:
    """Notification template definition"""

    subject: str
    body_text: str
    body_html: Optional[str] = None
    variables: Dict[str, str] = None

    def __post_init__(self):
        if self.variables is None:
            self.variables = {}


@dataclass
class Notification:
    """Individual notification"""

    id: str
    recipient_id: str
    notification_type: NotificationType
    subject: str
    content: str
    html_content: Optional[str] = None
    created_at: datetime = None
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.metadata is None:
            self.metadata = {}


class NotificationChannel(ABC):
    """Abstract base class for notification channels"""

    @abstractmethod
    async def send(self, notification: Notification, recipient: User) -> bool:
        """Send a notification through this channel"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this channel is available/configured"""
        pass


class EmailChannel(NotificationChannel):
    """Email notification channel"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True,
        from_address: Optional[str] = None,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.from_address = from_address or username

    async def send(self, notification: Notification, recipient: User) -> bool:
        """Send email notification"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = notification.subject
            msg["From"] = self.from_address
            msg["To"] = recipient.email

            # Add text content
            text_part = MIMEText(notification.content, "plain", "utf-8")
            msg.attach(text_part)

            # Add HTML content if available
            if notification.html_content:
                html_part = MIMEText(notification.html_content, "html", "utf-8")
                msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                text = msg.as_string()
                server.sendmail(self.from_address, recipient.email, text)

            logger.info(f"Email sent to {recipient.email}: {notification.subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {recipient.email}: {e}")
            return False

    def is_available(self) -> bool:
        """Check if email channel is properly configured"""
        return all(
            [
                self.smtp_host,
                self.smtp_port,
                self.username,
                self.password,
                self.from_address,
            ]
        )


class InAppChannel(NotificationChannel):
    """In-application notification channel"""

    def __init__(self, storage_backend):
        self.storage = storage_backend

    async def send(self, notification: Notification, recipient: User) -> bool:
        """Store notification for in-app display"""
        try:
            # Store notification in database/storage
            await self.storage.create_notification(notification)
            logger.info(
                f"In-app notification created for user {recipient.id}: {notification.subject}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create in-app notification: {e}")
            return False

    def is_available(self) -> bool:
        """In-app channel is always available"""
        return True


class SlackChannel(NotificationChannel):
    """Slack notification channel (placeholder)"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, notification: Notification, recipient: User) -> bool:
        """Send Slack notification (placeholder implementation)"""
        # TODO: Implement Slack webhook integration
        logger.info(f"Slack notification would be sent: {notification.subject}")
        return True

    def is_available(self) -> bool:
        """Check if Slack webhook is configured"""
        return bool(self.webhook_url)


class NotificationManager:
    """Central notification management system"""

    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {}
        self.templates: Dict[NotificationType, NotificationTemplate] = {}
        self.user_preferences: Dict[str, Dict[NotificationType, List[str]]] = {}

        # Initialize default templates
        self._initialize_default_templates()

    def add_channel(self, name: str, channel: NotificationChannel):
        """Add a notification channel"""
        if channel.is_available():
            self.channels[name] = channel
            logger.info(f"Notification channel '{name}' added")
        else:
            logger.warning(f"Notification channel '{name}' is not properly configured")

    def set_template(
        self, notification_type: NotificationType, template: NotificationTemplate
    ):
        """Set a notification template"""
        self.templates[notification_type] = template

    def set_user_preferences(
        self, user_id: str, preferences: Dict[NotificationType, List[str]]
    ):
        """Set user notification preferences"""
        self.user_preferences[user_id] = preferences

    def get_user_channels(
        self, user_id: str, notification_type: NotificationType
    ) -> List[str]:
        """Get user's preferred channels for a notification type"""
        prefs = self.user_preferences.get(user_id, {})
        return prefs.get(notification_type, ["in_app"])  # Default to in-app

    async def send_notification(
        self,
        notification_type: NotificationType,
        recipient: User,
        context: Dict[str, Any],
        channels: Optional[List[str]] = None,
    ) -> Dict[str, bool]:
        """Send a notification to a user"""

        # Get template
        template = self.templates.get(notification_type)
        if not template:
            logger.warning(
                f"No template found for notification type: {notification_type}"
            )
            return {}

        # Generate notification content
        notification = self._create_notification(
            notification_type, recipient.id, template, context
        )

        # Determine channels to use
        if channels is None:
            channels = self.get_user_channels(recipient.id, notification_type)

        # Send through each channel
        results = {}
        for channel_name in channels:
            if channel_name in self.channels:
                try:
                    success = await self.channels[channel_name].send(
                        notification, recipient
                    )
                    results[channel_name] = success

                    if success:
                        notification.sent_at = datetime.now(timezone.utc)
                except Exception as e:
                    logger.error(f"Failed to send notification via {channel_name}: {e}")
                    results[channel_name] = False
            else:
                logger.warning(f"Channel '{channel_name}' not found")
                results[channel_name] = False

        return results

    async def send_task_assigned(self, task: Task, assignee: User, assigner: User):
        """Send task assignment notification"""
        context = {
            "task_title": task.title,
            "task_id": task.id[:8],
            "task_description": task.description or "No description",
            "assignee_name": assignee.full_name or assignee.username,
            "assigner_name": assigner.full_name or assigner.username,
            "due_date": (
                task.due_date.strftime("%Y-%m-%d") if task.due_date else "No due date"
            ),
            "priority": task.priority.value.title(),
        }

        return await self.send_notification(
            NotificationType.TASK_ASSIGNED, assignee, context
        )

    async def send_task_due_soon(self, task: Task, assignee: User, days_until_due: int):
        """Send task due soon notification"""
        context = {
            "task_title": task.title,
            "task_id": task.id[:8],
            "assignee_name": assignee.full_name or assignee.username,
            "due_date": task.due_date.strftime("%Y-%m-%d"),
            "days_until_due": str(days_until_due),
            "priority": task.priority.value.title(),
        }

        return await self.send_notification(
            NotificationType.TASK_DUE_SOON, assignee, context
        )

    async def send_task_overdue(self, task: Task, assignee: User, days_overdue: int):
        """Send task overdue notification"""
        context = {
            "task_title": task.title,
            "task_id": task.id[:8],
            "assignee_name": assignee.full_name or assignee.username,
            "due_date": task.due_date.strftime("%Y-%m-%d"),
            "days_overdue": str(days_overdue),
            "priority": task.priority.value.title(),
        }

        return await self.send_notification(
            NotificationType.TASK_OVERDUE, assignee, context
        )

    async def send_bulk_notifications(
        self, notifications: List[tuple[NotificationType, User, Dict[str, Any]]]
    ) -> Dict[str, Dict[str, bool]]:
        """Send multiple notifications efficiently"""
        tasks = []
        for notification_type, recipient, context in notifications:
            task = self.send_notification(notification_type, recipient, context)
            tasks.append((f"{recipient.id}_{notification_type.value}", task))

        results = {}
        completed_tasks = await asyncio.gather(
            *[task for _, task in tasks], return_exceptions=True
        )

        for (key, _), result in zip(tasks, completed_tasks):
            if isinstance(result, Exception):
                logger.error(f"Bulk notification failed for {key}: {result}")
                results[key] = {"error": str(result)}
            else:
                results[key] = result

        return results

    def _create_notification(
        self,
        notification_type: NotificationType,
        recipient_id: str,
        template: NotificationTemplate,
        context: Dict[str, Any],
    ) -> Notification:
        """Create a notification from template and context"""

        # Replace template variables
        subject = self._replace_variables(template.subject, context)
        content = self._replace_variables(template.body_text, context)
        html_content = None

        if template.body_html:
            html_content = self._replace_variables(template.body_html, context)

        return Notification(
            id=f"notif_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{recipient_id}",
            recipient_id=recipient_id,
            notification_type=notification_type,
            subject=subject,
            content=content,
            html_content=html_content,
            metadata=context,
        )

    def _replace_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Replace variables in text with context values"""
        try:
            return text.format(**context)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            return text

    def _initialize_default_templates(self):
        """Initialize default notification templates"""

        # Task assigned template
        self.templates[NotificationType.TASK_ASSIGNED] = NotificationTemplate(
            subject="Task Assigned: {task_title}",
            body_text="""Hello {assignee_name},

You have been assigned a new task:

Task: {task_title}
ID: {task_id}
Priority: {priority}
Due Date: {due_date}
Assigned by: {assigner_name}

Description:
{task_description}

Please log into TaskForge to view the full details and start working on this task.

Best regards,
TaskForge Team""",
            body_html="""<html>
<body>
<h2>New Task Assignment</h2>
<p>Hello <strong>{assignee_name}</strong>,</p>
<p>You have been assigned a new task:</p>
<ul>
<li><strong>Task:</strong> {task_title}</li>
<li><strong>ID:</strong> {task_id}</li>
<li><strong>Priority:</strong> <span style="color: orange">{priority}</span></li>
<li><strong>Due Date:</strong> {due_date}</li>
<li><strong>Assigned by:</strong> {assigner_name}</li>
</ul>
<p><strong>Description:</strong><br/>{task_description}</p>
<p>Please log into TaskForge to view the full details and start working on this task.</p>
<p>Best regards,<br/>TaskForge Team</p>
</body>
</html>""",
        )

        # Task due soon template
        self.templates[NotificationType.TASK_DUE_SOON] = NotificationTemplate(
            subject="Reminder: Task '{task_title}' is due in {days_until_due} days",
            body_text="""Hello {assignee_name},

This is a reminder that your task is due soon:

Task: {task_title}
ID: {task_id}
Priority: {priority}
Due Date: {due_date}
Days until due: {days_until_due}

Please make sure to complete this task on time.

Best regards,
TaskForge Team""",
        )

        # Task overdue template
        self.templates[NotificationType.TASK_OVERDUE] = NotificationTemplate(
            subject="URGENT: Task '{task_title}' is {days_overdue} days overdue",
            body_text="""Hello {assignee_name},

URGENT: Your task is overdue:

Task: {task_title}
ID: {task_id}
Priority: {priority}
Due Date: {due_date}
Days overdue: {days_overdue}

Please complete this task as soon as possible.

Best regards,
TaskForge Team""",
        )


# Factory function for easy setup
def create_notification_manager(config: Dict[str, Any]) -> NotificationManager:
    """Create a configured notification manager"""
    manager = NotificationManager()

    # Add email channel if configured
    email_config = config.get("email", {})
    if email_config.get("enabled", False):
        email_channel = EmailChannel(
            smtp_host=email_config.get("smtp_host"),
            smtp_port=email_config.get("smtp_port", 587),
            username=email_config.get("username"),
            password=email_config.get("password"),
            use_tls=email_config.get("use_tls", True),
            from_address=email_config.get("from_address"),
        )
        manager.add_channel("email", email_channel)

    # Add Slack channel if configured
    slack_config = config.get("slack", {})
    if slack_config.get("enabled", False):
        slack_channel = SlackChannel(webhook_url=slack_config.get("webhook_url"))
        manager.add_channel("slack", slack_channel)

    # In-app channel is always available
    # Note: This would need the storage backend
    # manager.add_channel('in_app', InAppChannel(storage_backend))

    return manager
