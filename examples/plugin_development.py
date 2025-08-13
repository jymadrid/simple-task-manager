#!/usr/bin/env python3
"""
TaskForge Plugin Development Example
===================================

This example demonstrates how to create custom plugins for TaskForge,
including integration plugins, notification systems, and workflow automation.

Great for: Plugin developers, system integrators, advanced users
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from taskforge import Project, Task, TaskManager, TaskPriority, TaskStatus
from taskforge.core.user import User
from taskforge.plugins import PluginHook, PluginMetadata, TaskPlugin
from taskforge.storage import JsonStorage

# Configure logging for plugin development
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NotificationEvent:
    """Represents a notification event."""

    event_type: str
    task_id: str
    user_id: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any]


class CustomNotificationPlugin(TaskPlugin):
    """
    A custom notification plugin that demonstrates:
    - Hook-based event handling
    - External service integration simulation
    - Configurable notification rules
    """

    def __init__(self):
        self.notifications: List[NotificationEvent] = []
        self.config = {
            "email_enabled": True,
            "slack_enabled": True,
            "priority_threshold": "medium",
            "notification_channels": ["email", "slack", "webhook"],
        }
        self.webhook_url = "https://hooks.example.com/taskforge"

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Custom Notification System",
            version="1.2.0",
            description="Advanced notification system with multiple channels and smart filtering",
            author="TaskForge Community",
            homepage="https://github.com/taskforge-community/notification-plugin",
            requires=["requests>=2.28.0", "slack-sdk>=3.20.0"],
            config_schema={
                "email_enabled": {"type": "boolean", "default": True},
                "slack_enabled": {"type": "boolean", "default": True},
                "priority_threshold": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "default": "medium",
                },
                "webhook_url": {"type": "string", "format": "uri"},
            },
        )

    @PluginHook("task_created")
    async def on_task_created(self, task: Task, user: User, **kwargs):
        """Handle new task creation."""
        await self._send_notification(
            event_type="task_created",
            task=task,
            user=user,
            message=f"New task created: '{task.title}' by {user.username}",
        )
        logger.info(f"📝 Task created notification sent: {task.title}")

    @PluginHook("task_completed")
    async def on_task_completed(self, task: Task, user: User, **kwargs):
        """Handle task completion."""
        await self._send_notification(
            event_type="task_completed",
            task=task,
            user=user,
            message=f"🎉 Task completed: '{task.title}' by {user.username}",
        )
        logger.info(f"✅ Task completion notification sent: {task.title}")

    @PluginHook("task_overdue")
    async def on_task_overdue(self, task: Task, user: User, **kwargs):
        """Handle overdue tasks."""
        overdue_days = (datetime.now() - task.due_date).days if task.due_date else 0
        await self._send_notification(
            event_type="task_overdue",
            task=task,
            user=user,
            message=f"⚠️ Task overdue by {overdue_days} days: '{task.title}'",
            priority="high",
        )
        logger.warning(
            f"⚠️ Overdue notification sent: {task.title} ({overdue_days} days)"
        )

    @PluginHook("project_milestone_reached")
    async def on_project_milestone_reached(
        self, project: Project, milestone: str, user: User, **kwargs
    ):
        """Handle project milestone events."""
        await self._send_notification(
            event_type="project_milestone",
            task=None,  # Project-level event
            user=user,
            message=f"🏆 Project '{project.name}' reached milestone: {milestone}",
            metadata={"project_id": project.id, "milestone": milestone},
        )
        logger.info(f"🏆 Milestone notification sent: {project.name} - {milestone}")

    async def _send_notification(
        self,
        event_type: str,
        task: Optional[Task],
        user: User,
        message: str,
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Send notification through configured channels."""
        notification = NotificationEvent(
            event_type=event_type,
            task_id=task.id if task else "",
            user_id=user.username,
            message=message,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )

        self.notifications.append(notification)

        # Check if notification meets threshold requirements
        if task and not self._meets_priority_threshold(task.priority):
            return

        # Send through configured channels
        if self.config["email_enabled"]:
            await self._send_email_notification(notification)

        if self.config["slack_enabled"]:
            await self._send_slack_notification(notification)

        if "webhook" in self.config["notification_channels"]:
            await self._send_webhook_notification(notification)

    def _meets_priority_threshold(self, task_priority: TaskPriority) -> bool:
        """Check if task priority meets notification threshold."""
        priority_levels = {"low": 1, "medium": 2, "high": 3}
        threshold_level = priority_levels.get(self.config["priority_threshold"], 2)
        task_level = priority_levels.get(task_priority.value, 1)
        return task_level >= threshold_level

    async def _send_email_notification(self, notification: NotificationEvent):
        """Simulate email notification."""
        print(f"📧 EMAIL: {notification.message}")

    async def _send_slack_notification(self, notification: NotificationEvent):
        """Simulate Slack notification."""
        print(f"💬 SLACK: {notification.message}")

    async def _send_webhook_notification(self, notification: NotificationEvent):
        """Simulate webhook notification."""
        print(f"🔗 WEBHOOK: {notification.message}")
        # In a real implementation, you would send HTTP POST to webhook_url
        # async with httpx.AsyncClient() as client:
        #     await client.post(self.webhook_url, json=asdict(notification))


class GitHubIntegrationPlugin(TaskPlugin):
    """
    GitHub integration plugin that demonstrates:
    - External API integration
    - Bidirectional synchronization
    - Issue and PR management
    """

    def __init__(self, github_token: str = None):
        self.github_token = github_token or "ghp_fake_token_for_demo"
        self.repo_mapping = {}  # Maps project_id -> github_repo
        self.sync_enabled = True

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="GitHub Integration",
            version="2.1.0",
            description="Bidirectional sync with GitHub Issues and Pull Requests",
            author="TaskForge Community",
            homepage="https://github.com/taskforge-community/github-plugin",
            requires=["pygithub>=1.58.0", "httpx>=0.24.0"],
            config_schema={
                "github_token": {
                    "type": "string",
                    "description": "GitHub personal access token",
                },
                "auto_sync": {"type": "boolean", "default": True},
                "create_branches": {"type": "boolean", "default": True},
                "default_labels": {"type": "array", "items": {"type": "string"}},
            },
        )

    def configure_repo_mapping(self, project_id: str, github_repo: str):
        """Configure GitHub repository mapping for a project."""
        self.repo_mapping[project_id] = github_repo
        logger.info(f"🔗 Mapped project {project_id} to GitHub repo {github_repo}")

    @PluginHook("task_created")
    async def on_task_created(self, task: Task, user: User, **kwargs):
        """Create corresponding GitHub issue when task is created."""
        if not self.sync_enabled or not task.project_id:
            return

        github_repo = self.repo_mapping.get(task.project_id)
        if not github_repo:
            return

        # Simulate GitHub API call
        issue_data = await self._create_github_issue(
            repo=github_repo,
            title=task.title,
            description=task.description or "Created from TaskForge",
            labels=self._get_issue_labels(task),
            assignees=[user.username] if hasattr(user, "github_username") else [],
        )

        # Store GitHub issue ID in task metadata
        task.metadata = task.metadata or {}
        task.metadata["github_issue_id"] = issue_data["number"]
        task.metadata["github_url"] = issue_data["html_url"]

        logger.info(
            f"🐙 Created GitHub issue #{issue_data['number']} for task: {task.title}"
        )

    @PluginHook("task_status_changed")
    async def on_task_status_changed(
        self,
        task: Task,
        old_status: TaskStatus,
        new_status: TaskStatus,
        user: User,
        **kwargs,
    ):
        """Update GitHub issue when task status changes."""
        github_issue_id = (
            task.metadata.get("github_issue_id") if task.metadata else None
        )
        if not github_issue_id:
            return

        github_repo = self.repo_mapping.get(task.project_id)
        if not github_repo:
            return

        # Update GitHub issue status
        if new_status == TaskStatus.COMPLETED:
            await self._close_github_issue(github_repo, github_issue_id, user.username)
            logger.info(
                f"🐙 Closed GitHub issue #{github_issue_id} for completed task: {task.title}"
            )
        elif new_status == TaskStatus.IN_PROGRESS:
            await self._add_github_comment(
                repo=github_repo,
                issue_number=github_issue_id,
                comment=f"Task started by {user.username} in TaskForge",
            )
            logger.info(
                f"🐙 Updated GitHub issue #{github_issue_id} - task in progress"
            )

    @PluginHook("task_assigned")
    async def on_task_assigned(self, task: Task, assignee: str, user: User, **kwargs):
        """Update GitHub issue assignee when task is assigned."""
        github_issue_id = (
            task.metadata.get("github_issue_id") if task.metadata else None
        )
        if not github_issue_id:
            return

        github_repo = self.repo_mapping.get(task.project_id)
        if github_repo:
            await self._assign_github_issue(github_repo, github_issue_id, assignee)
            logger.info(f"🐙 Assigned GitHub issue #{github_issue_id} to {assignee}")

    def _get_issue_labels(self, task: Task) -> List[str]:
        """Generate GitHub labels based on task properties."""
        labels = []

        # Priority-based labels
        if task.priority == TaskPriority.HIGH:
            labels.append("high-priority")
        elif task.priority == TaskPriority.LOW:
            labels.append("low-priority")

        # Task tags as labels
        if task.tags:
            labels.extend(task.tags)

        # Default labels
        labels.append("taskforge")

        return labels

    async def _create_github_issue(
        self,
        repo: str,
        title: str,
        description: str,
        labels: List[str],
        assignees: List[str],
    ) -> Dict[str, Any]:
        """Simulate GitHub issue creation."""
        issue_number = hash(title) % 1000 + 1  # Fake issue number
        return {
            "number": issue_number,
            "html_url": f"https://github.com/{repo}/issues/{issue_number}",
            "state": "open",
        }

    async def _close_github_issue(self, repo: str, issue_number: int, closer: str):
        """Simulate closing GitHub issue."""
        print(f"🐙 Closing GitHub issue #{issue_number} in {repo} (closed by {closer})")

    async def _add_github_comment(self, repo: str, issue_number: int, comment: str):
        """Simulate adding comment to GitHub issue."""
        print(f"🐙 Adding comment to issue #{issue_number} in {repo}: {comment}")

    async def _assign_github_issue(self, repo: str, issue_number: int, assignee: str):
        """Simulate assigning GitHub issue."""
        print(f"🐙 Assigning issue #{issue_number} in {repo} to {assignee}")


class ProjectAnalyticsPlugin(TaskPlugin):
    """
    Analytics plugin that demonstrates:
    - Data collection and analysis
    - Performance metrics
    - Reporting capabilities
    """

    def __init__(self):
        self.metrics_data = {
            "task_completion_times": [],
            "productivity_scores": {},
            "project_progress": {},
            "team_performance": {},
        }
        self.start_times = {}  # Track when tasks are started

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Project Analytics",
            version="1.5.0",
            description="Advanced analytics and reporting for task management insights",
            author="TaskForge Analytics Team",
            homepage="https://github.com/taskforge-community/analytics-plugin",
            requires=["pandas>=2.0.0", "matplotlib>=3.7.0", "numpy>=1.24.0"],
        )

    @PluginHook("task_status_changed")
    async def on_task_status_changed(
        self,
        task: Task,
        old_status: TaskStatus,
        new_status: TaskStatus,
        user: User,
        **kwargs,
    ):
        """Track task status changes for analytics."""
        if new_status == TaskStatus.IN_PROGRESS:
            self.start_times[task.id] = datetime.now()
            logger.info(f"📊 Started tracking time for task: {task.title}")

        elif new_status == TaskStatus.COMPLETED and task.id in self.start_times:
            completion_time = datetime.now() - self.start_times[task.id]
            self.metrics_data["task_completion_times"].append(
                {
                    "task_id": task.id,
                    "title": task.title,
                    "user": user.username,
                    "completion_time_hours": completion_time.total_seconds() / 3600,
                    "priority": task.priority.value,
                    "estimated_hours": task.estimated_hours or 0,
                    "actual_vs_estimate": (completion_time.total_seconds() / 3600)
                    / (task.estimated_hours or 1),
                }
            )
            del self.start_times[task.id]
            logger.info(
                f"📊 Recorded completion time for task: {task.title} ({completion_time})"
            )

    @PluginHook("project_created")
    async def on_project_created(self, project: Project, user: User, **kwargs):
        """Initialize project analytics tracking."""
        self.metrics_data["project_progress"][project.id] = {
            "created_at": datetime.now(),
            "creator": user.username,
            "task_count": 0,
            "completed_tasks": 0,
            "milestones": [],
        }
        logger.info(f"📊 Started analytics tracking for project: {project.name}")

    def generate_productivity_report(
        self, user_id: str = None, project_id: str = None
    ) -> Dict[str, Any]:
        """Generate productivity insights report."""
        completion_data = self.metrics_data["task_completion_times"]

        if user_id:
            completion_data = [d for d in completion_data if d["user"] == user_id]

        if not completion_data:
            return {"message": "No completion data available"}

        # Calculate metrics
        avg_completion_time = sum(
            d["completion_time_hours"] for d in completion_data
        ) / len(completion_data)
        total_tasks_completed = len(completion_data)

        # Estimate accuracy
        estimates_vs_actual = [
            d["actual_vs_estimate"] for d in completion_data if d["estimated_hours"] > 0
        ]
        avg_estimate_accuracy = (
            sum(estimates_vs_actual) / len(estimates_vs_actual)
            if estimates_vs_actual
            else 0
        )

        # Priority distribution
        priority_dist = {}
        for data in completion_data:
            priority = data["priority"]
            priority_dist[priority] = priority_dist.get(priority, 0) + 1

        report = {
            "summary": {
                "total_completed_tasks": total_tasks_completed,
                "average_completion_time_hours": round(avg_completion_time, 2),
                "estimate_accuracy_ratio": round(avg_estimate_accuracy, 2),
                "productivity_trend": (
                    "improving" if avg_estimate_accuracy < 1.2 else "needs_attention"
                ),
            },
            "priority_distribution": priority_dist,
            "recommendations": self._generate_recommendations(completion_data),
        }

        return report

    def _generate_recommendations(
        self, completion_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate personalized productivity recommendations."""
        recommendations = []

        if not completion_data:
            return ["Start completing tasks to get personalized recommendations!"]

        # Analyze completion times
        avg_time = sum(d["completion_time_hours"] for d in completion_data) / len(
            completion_data
        )

        if avg_time > 8:
            recommendations.append(
                "Consider breaking down large tasks into smaller, manageable chunks"
            )

        # Analyze estimate accuracy
        estimates = [
            d["actual_vs_estimate"] for d in completion_data if d["estimated_hours"] > 0
        ]
        if estimates:
            avg_accuracy = sum(estimates) / len(estimates)
            if avg_accuracy > 1.5:
                recommendations.append(
                    "Your time estimates tend to be optimistic - consider adding buffer time"
                )
            elif avg_accuracy < 0.8:
                recommendations.append(
                    "Your time estimates are often too high - you're more efficient than you think!"
                )

        # Priority analysis
        high_priority_count = len(
            [d for d in completion_data if d["priority"] == "high"]
        )
        total_count = len(completion_data)

        if high_priority_count / total_count > 0.7:
            recommendations.append(
                "You're handling many high-priority tasks - consider delegating or reprioritizing"
            )

        return recommendations


async def plugin_development_demo():
    """Demonstrate plugin development and usage."""
    print("🔌 TaskForge Plugin Development Demo")
    print("=" * 40)

    # Initialize TaskForge
    storage = JsonStorage("./examples_data/plugins")
    await storage.initialize()
    manager = TaskManager(storage)

    # Create demo user
    user = User(username="plugin_developer", email="dev@example.com")

    print("\n1. Initializing plugins...")

    # Initialize plugins
    notification_plugin = CustomNotificationPlugin()
    github_plugin = GitHubIntegrationPlugin()
    analytics_plugin = ProjectAnalyticsPlugin()

    # Display plugin metadata
    for plugin in [notification_plugin, github_plugin, analytics_plugin]:
        metadata = plugin.get_metadata()
        print(f"   📦 {metadata.name} v{metadata.version}")
        print(f"      {metadata.description}")

    print("\n2. Creating project with GitHub integration...")

    # Create a project
    project = Project(
        name="TaskForge Plugin Ecosystem",
        description="Develop a comprehensive plugin ecosystem for TaskForge",
        tags=["plugins", "ecosystem", "community"],
    )

    created_project = await manager.create_project(project, user.username)

    # Configure GitHub integration
    github_plugin.configure_repo_mapping(
        created_project.id, "taskforge-community/plugin-ecosystem"
    )

    # Trigger project creation hook
    await analytics_plugin.on_project_created(created_project, user)

    print(f"   ✅ Created project: {created_project.name}")

    print("\n3. Demonstrating plugin workflows...")

    # Create tasks that will trigger various plugin hooks
    sample_tasks = [
        Task(
            title="Design plugin architecture",
            description="Create comprehensive plugin system design",
            priority=TaskPriority.HIGH,
            project_id=created_project.id,
            estimated_hours=8,
            tags=["architecture", "design"],
        ),
        Task(
            title="Implement plugin loader",
            description="Build dynamic plugin loading system",
            priority=TaskPriority.HIGH,
            project_id=created_project.id,
            estimated_hours=12,
            tags=["implementation", "core"],
        ),
        Task(
            title="Create plugin documentation",
            description="Write comprehensive plugin development guide",
            priority=TaskPriority.MEDIUM,
            project_id=created_project.id,
            estimated_hours=6,
            tags=["documentation", "guides"],
        ),
        Task(
            title="Set up plugin marketplace",
            description="Build web interface for plugin discovery",
            priority=TaskPriority.MEDIUM,
            project_id=created_project.id,
            estimated_hours=16,
            tags=["marketplace", "web"],
        ),
    ]

    created_tasks = []
    for task in sample_tasks:
        created_task = await manager.create_task(task, user.username)
        created_tasks.append(created_task)

        # Trigger plugin hooks
        await notification_plugin.on_task_created(created_task, user)
        await github_plugin.on_task_created(created_task, user)

        print(f"   📝 Created task: {created_task.title}")

    print("\n4. Simulating task lifecycle with plugin events...")

    # Start working on first task
    first_task = created_tasks[0]
    old_status = first_task.status
    first_task.status = TaskStatus.IN_PROGRESS

    await notification_plugin.on_task_created(first_task, user)
    await github_plugin.on_task_status_changed(
        first_task, old_status, TaskStatus.IN_PROGRESS, user
    )
    await analytics_plugin.on_task_status_changed(
        first_task, old_status, TaskStatus.IN_PROGRESS, user
    )

    print(f"   🔄 Started task: {first_task.title}")

    # Simulate some work time
    await asyncio.sleep(0.1)  # Simulate brief work period

    # Complete the task
    old_status = first_task.status
    first_task.status = TaskStatus.COMPLETED

    await notification_plugin.on_task_completed(first_task, user)
    await github_plugin.on_task_status_changed(
        first_task, old_status, TaskStatus.COMPLETED, user
    )
    await analytics_plugin.on_task_status_changed(
        first_task, old_status, TaskStatus.COMPLETED, user
    )

    print(f"   ✅ Completed task: {first_task.title}")

    # Simulate overdue task
    overdue_task = created_tasks[2]
    overdue_task.due_date = datetime.now() - timedelta(days=2)
    await notification_plugin.on_task_overdue(overdue_task, user)

    print(f"   ⚠️ Overdue task notification: {overdue_task.title}")

    # Simulate project milestone
    await notification_plugin.on_project_milestone_reached(
        created_project, "Plugin Architecture Complete", user
    )

    print(f"   🏆 Project milestone reached!")

    print("\n5. Generating analytics report...")

    # Generate productivity report
    report = analytics_plugin.generate_productivity_report(user.username)

    print(f"   📊 Analytics Report for {user.username}:")
    print(f"      Total completed tasks: {report['summary']['total_completed_tasks']}")
    print(
        f"      Average completion time: {report['summary']['average_completion_time_hours']} hours"
    )
    print(f"      Estimate accuracy: {report['summary']['estimate_accuracy_ratio']}x")
    print(f"      Productivity trend: {report['summary']['productivity_trend']}")

    if report.get("recommendations"):
        print("      Recommendations:")
        for rec in report["recommendations"][:2]:  # Show first 2 recommendations
            print(f"        - {rec}")

    print("\n6. Plugin notification summary...")

    print(f"   📧 Total notifications sent: {len(notification_plugin.notifications)}")

    # Show recent notifications
    recent_notifications = notification_plugin.notifications[
        -3:
    ]  # Last 3 notifications
    for notif in recent_notifications:
        print(f"      {notif.timestamp.strftime('%H:%M:%S')} - {notif.message}")

    print("\n7. Plugin configuration examples...")

    # Show plugin configuration
    print("   ⚙️ Notification Plugin Config:")
    for key, value in notification_plugin.config.items():
        print(f"      {key}: {value}")

    print("   ⚙️ GitHub Integration Mapping:")
    for project_id, repo in github_plugin.repo_mapping.items():
        print(f"      {project_id} → {repo}")

    print("\n✨ Plugin development demo completed!")

    return {
        "plugins": [notification_plugin, github_plugin, analytics_plugin],
        "project": created_project,
        "tasks": created_tasks,
        "analytics_report": report,
    }


async def main():
    """Run plugin development examples."""
    print("🔌 TaskForge Plugin Development Examples")
    print("=" * 45)
    print("This demo showcases:")
    print("- Custom plugin development")
    print("- Hook-based event system")
    print("- External service integrations")
    print("- Analytics and reporting")
    print("- Plugin configuration")
    print("=" * 45)

    try:
        results = await plugin_development_demo()

        print("\n\n🎉 Plugin Development Demo Completed!")
        print("=" * 42)
        print(f"✅ Plugins demonstrated: {len(results['plugins'])}")
        print(f"🏗️ Project created: {results['project'].name}")
        print(f"📝 Tasks created: {len(results['tasks'])}")
        print(f"📊 Analytics data collected: {len(results['analytics_report'])}")

        print("\n💡 Plugin Development Tips:")
        print("- Use the @PluginHook decorator to handle TaskForge events")
        print("- Implement PluginMetadata for proper plugin registration")
        print("- Follow async/await patterns for non-blocking operations")
        print("- Add comprehensive error handling and logging")
        print("- Include configuration schemas for user customization")

        print("\n🔗 Useful Resources:")
        print("- Plugin API Documentation: https://docs.taskforge.dev/plugins")
        print("- Example Plugins: https://github.com/taskforge-community/plugins")
        print("- Plugin Development Guide: https://docs.taskforge.dev/dev/plugins")
        print("- Community Discord: https://discord.gg/taskforge")

    except Exception as e:
        print(f"\n❌ Error in plugin development demo: {e}")
        print("Please check your TaskForge installation and plugin dependencies.")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
