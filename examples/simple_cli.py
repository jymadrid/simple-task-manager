#!/usr/bin/env python3
"""
Simple CLI Example for TaskForge

This example demonstrates how to build a basic task management CLI
using TaskForge as a library. It shows the core functionality and
serves as a starting point for more complex applications.

Usage:
    python examples/simple_cli.py --help
    python examples/simple_cli.py add "Fix bug in authentication"
    python examples/simple_cli.py list
    python examples/simple_cli.py complete <task_id>
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.theme import Theme
from rich.text import Text

# Add the parent directory to the path so we can import taskforge
sys.path.insert(0, str(Path(__file__).parent.parent))

from taskforge.core.project import Project
from taskforge.core.task import Task, TaskPriority, TaskStatus
from taskforge.core.user import User
from taskforge.storage.json_storage import JSONStorage

# Apple-inspired theme for Rich
apple_theme = Theme({
    "primary": "#007AFF",      # SF Blue
    "success": "#34C759",      # SF Green
    "warning": "#FF9500",      # SF Orange
    "error": "#FF3B30",        # SF Red
    "secondary": "#5856D6",    # SF Purple
    "muted": "#8E8E93",        # SF Gray
    "accent": "#AF52DE",       # SF Purple variant
    "info": "#00C7BE",         # SF Teal
})

console = Console(theme=apple_theme)


class SimpleTaskManager:
    """Simple task manager wrapper for CLI operations"""

    def __init__(self, data_dir: str = "./data"):
        self.storage = JSONStorage(data_dir)
        self.current_user_id = "default-user"

    async def initialize(self):
        """Initialize storage and create default user if needed"""
        await self.storage.initialize()

        # Create default user if it doesn't exist
        user = await self.storage.get_user(self.current_user_id)
        if not user:
            default_user = User.create_user(
                username="default",
                email="user@example.com",
                password="password",
                full_name="Default User",
            )
            default_user.id = self.current_user_id
            await self.storage.create_user(default_user)
            console.print("✅ Created default user", style="success")

    async def add_task(
        self, title: str, description: str = "", priority: str = "medium"
    ):
        """Add a new task"""
        try:
            priority_enum = TaskPriority(priority.lower())
        except ValueError:
            priority_enum = TaskPriority.MEDIUM

        task = Task(
            title=title,
            description=description,
            priority=priority_enum,
            created_by=self.current_user_id,
            assigned_to=self.current_user_id,
        )

        created_task = await self.storage.create_task(task)
        return created_task

    async def list_tasks(self, status_filter: Optional[str] = None):
        """List all tasks with optional status filter"""
        from taskforge.core.queries import TaskQuery

        query = TaskQuery(limit=100)
        if status_filter:
            try:
                status_enum = TaskStatus(status_filter.lower())
                query.status = [status_enum]
            except ValueError:
                pass

        tasks = await self.storage.search_tasks(query, self.current_user_id)
        return tasks

    async def complete_task(self, task_id: str):
        """Mark a task as completed"""
        task = await self.storage.get_task(task_id)
        if not task:
            return None

        task.update_status(TaskStatus.DONE, self.current_user_id)
        updated_task = await self.storage.update_task(task)
        return updated_task

    async def delete_task(self, task_id: str):
        """Delete a task"""
        return await self.storage.delete_task(task_id)

    async def get_statistics(self):
        """Get task statistics"""
        return await self.storage.get_task_statistics(user_id=self.current_user_id)


# Global manager instance
manager = SimpleTaskManager()


@click.group()
@click.version_option(version="1.0.0", prog_name="TaskForge Simple CLI")
def cli():
    """TaskForge Simple CLI - A demonstration of TaskForge library usage"""
    pass


@cli.command()
@click.argument("title")
@click.option("--description", "-d", default="", help="Task description")
@click.option(
    "--priority",
    "-p",
    default="medium",
    type=click.Choice(["low", "medium", "high", "critical"], case_sensitive=False),
    help="Task priority",
)
def add(title: str, description: str, priority: str):
    """Add a new task"""

    async def _add():
        await manager.initialize()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating task...", total=None)
            created_task = await manager.add_task(title, description, priority)
            progress.update(task, description="Task created!")

        console.print(
            Panel(
                f"✨ Task created successfully!\n\n"
                f"[bold primary]ID:[/bold primary] {created_task.id[:8]}...\n"
                f"[bold primary]Title:[/bold primary] {created_task.title}\n"
                f"[bold primary]Priority:[/bold primary] {created_task.priority.value}\n"
                f"[bold primary]Status:[/bold primary] {created_task.status.value}",
                title="[bold accent]⚡ New Task[/bold accent]",
                border_style="primary",
                padding=(1, 2),
            )
        )

    asyncio.run(_add())


@cli.command()
@click.option("--status", "-s", help="Filter by status (todo, in_progress, done)")
@click.option("--limit", "-l", default=20, help="Maximum number of tasks to show")
def list(status: Optional[str], limit: int):
    """List all tasks"""

    async def _list():
        await manager.initialize()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Loading tasks...", total=None)
            tasks = await manager.list_tasks(status)
            progress.update(task, description="Tasks loaded!")

        if not tasks:
            console.print(
                "📝 No tasks found. Use [primary]add[/primary] command to create your first task!",
                style="muted",
            )
            return

        # Create a beautiful Apple-style table
        table = Table(
            title=f"[bold accent]📋 Your Tasks[/bold accent] [muted]({len(tasks)} total)[/muted]",
            title_style="bold",
            show_header=True,
            header_style="bold primary",
            border_style="primary",
            box=None,
            pad_edge=False,
        )
        table.add_column("ID", style="muted", width=10, no_wrap=True)
        table.add_column("Title", style="bold", min_width=30, max_width=50)
        table.add_column("Status", style="", width=12, justify="center")
        table.add_column("Priority", style="", width=10, justify="center")
        table.add_column("Created", style="muted", width=12, justify="right")

        for task in tasks[:limit]:
            # Format creation date
            created_date = task.created_at.strftime("%m/%d %H:%M")

            # Apple-inspired status styling
            status_styles = {
                "todo": "[warning]●[/warning] [warning]To Do[/warning]",
                "in_progress": "[info]●[/info] [info]In Progress[/info]",
                "done": "[success]●[/success] [success]Done[/success]",
                "blocked": "[error]●[/error] [error]Blocked[/error]",
                "cancelled": "[muted]●[/muted] [muted]Cancelled[/muted]",
            }

            # Apple-inspired priority styling
            priority_styles = {
                "critical": "[error]!![/error] [error]Critical[/error]",
                "high": "[warning]![/warning] [warning]High[/warning]",
                "medium": "[secondary]—[/secondary] [secondary]Medium[/secondary]",
                "low": "[success]—[/success] [success]Low[/success]",
            }

            status_display = status_styles.get(task.status.value, task.status.value)
            priority_display = priority_styles.get(task.priority.value, task.priority.value)

            # Truncate long titles with elegant ellipsis
            title_display = task.title
            if len(title_display) > 47:
                title_display = title_display[:44] + "..."

            table.add_row(
                f"[muted]{task.id[:8]}[/muted]",
                title_display,
                status_display,
                priority_display,
                f"[muted]{created_date}[/muted]",
            )

        console.print(table)

        if len(tasks) > limit:
            console.print(
                f"\n💡 Showing [primary]{limit}[/primary] of [primary]{len(tasks)}[/primary] tasks. Use [primary]--limit[/primary] to see more.",
                style="muted",
            )

    asyncio.run(_list())


@cli.command()
@click.argument("task_id")
def complete(task_id: str):
    """Mark a task as completed"""

    async def _complete():
        await manager.initialize()

        # Try to find task by partial ID
        all_tasks = await manager.list_tasks()
        matching_task = None
        for task in all_tasks:
            if task.id.startswith(task_id):
                matching_task = task
                break

        if not matching_task:
            console.print(f"❌ Task with ID '[primary]{task_id}[/primary]' not found", style="error")
            return

        if matching_task.status == TaskStatus.DONE:
            console.print(
                f"ℹ️  Task '[accent]{matching_task.title}[/accent]' is already completed", style="warning"
            )
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Completing task...", total=None)
            updated_task = await manager.complete_task(matching_task.id)
            progress.update(task, description="Task completed!")

        console.print(
            Panel(
                f"🎉 Task completed!\n\n"
                f"[bold primary]Title:[/bold primary] {updated_task.title}\n"
                f"[bold primary]Status:[/bold primary] [success]{updated_task.status.value}[/success]\n"
                f"[bold primary]Completed:[/bold primary] {updated_task.completed_at.strftime('%Y-%m-%d %H:%M')}",
                title="[bold success]✅ Task Completed[/bold success]",
                border_style="success",
                padding=(1, 2),
            )
        )

    asyncio.run(_complete())


@cli.command()
@click.argument("task_id")
@click.confirmation_option(prompt="Are you sure you want to delete this task?")
def delete(task_id: str):
    """Delete a task"""

    async def _delete():
        await manager.initialize()

        # Try to find task by partial ID
        all_tasks = await manager.list_tasks()
        matching_task = None
        for task in all_tasks:
            if task.id.startswith(task_id):
                matching_task = task
                break

        if not matching_task:
            console.print(f"❌ Task with ID '[primary]{task_id}[/primary]' not found", style="error")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Deleting task...", total=None)
            deleted = await manager.delete_task(matching_task.id)
            progress.update(task, description="Task deleted!")

        if deleted:
            console.print(
                f"🗑️  Task '[accent]{matching_task.title}[/accent]' deleted successfully", style="success"
            )
        else:
            console.print(f"❌ Failed to delete task", style="error")

    asyncio.run(_delete())


@cli.command()
def stats():
    """Show task statistics"""

    async def _stats():
        await manager.initialize()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Calculating statistics...", total=None)
            stats = await manager.get_statistics()
            progress.update(task, description="Statistics ready!")

        # Create beautiful Apple-style statistics panel
        stats_content = []

        # Main stats with visual elements
        stats_content.append(f"[bold primary]📊 Overview[/bold primary]")
        stats_content.append(f"Total Tasks: [bold]{stats['total_tasks']}[/bold]")
        stats_content.append(f"Completed: [success]{stats['completed_tasks']}[/success] ([success]{stats['completion_rate']:.1%}[/success])")
        stats_content.append(f"In Progress: [info]{stats['in_progress_tasks']}[/info]")
        stats_content.append(f"Overdue: [error]{stats['overdue_tasks']}[/error]")
        stats_content.append("")

        # Priority distribution with visual bars
        stats_content.append(f"[bold secondary]🎯 Priority Distribution[/bold secondary]")
        for priority, count in stats["priority_distribution"].items():
            # Create simple visual bar
            bar_length = min(count, 20)  # Max 20 chars
            bar = "█" * bar_length

            priority_styles = {
                "critical": f"[error]{bar}[/error]",
                "high": f"[warning]{bar}[/warning]",
                "medium": f"[secondary]{bar}[/secondary]",
                "low": f"[success]{bar}[/success]",
            }

            visual_bar = priority_styles.get(priority, bar)
            stats_content.append(f"  {priority.title()}: {visual_bar} [muted]({count})[/muted]")

        stats_content.append("")

        # Status distribution
        stats_content.append(f"[bold accent]🔄 Status Distribution[/bold accent]")
        for status, count in stats["status_distribution"].items():
            bar_length = min(count, 20)
            bar = "●" * bar_length

            status_styles = {
                "todo": f"[warning]{bar}[/warning]",
                "in_progress": f"[info]{bar}[/info]",
                "done": f"[success]{bar}[/success]",
                "blocked": f"[error]{bar}[/error]",
                "cancelled": f"[muted]{bar}[/muted]",
            }

            visual_bar = status_styles.get(status, bar)
            display_status = status.replace('_', ' ').title()
            stats_content.append(f"  {display_status}: {visual_bar} [muted]({count})[/muted]")

        console.print(
            Panel(
                "\n".join(stats_content),
                title="[bold primary]📈 Task Analytics[/bold primary]",
                border_style="primary",
                padding=(1, 2),
            )
        )

    asyncio.run(_stats())


@cli.command()
def demo():
    """Create demo tasks for testing"""

    async def _demo():
        await manager.initialize()

        demo_tasks = [
            (
                "Fix authentication bug",
                "Users can't log in with special characters",
                "high",
            ),
            ("Update documentation", "Add examples for new API endpoints", "medium"),
            (
                "Implement dark mode",
                "Add dark theme support to the web interface",
                "low",
            ),
            ("Optimize database queries", "Improve performance of task search", "high"),
            (
                "Write unit tests",
                "Add tests for the new user management features",
                "medium",
            ),
        ]

        console.print("🎭 Creating demo tasks...", style="primary")

        with Progress(console=console) as progress:
            task = progress.add_task("[primary]Creating demo tasks...", total=len(demo_tasks))

            for title, description, priority in demo_tasks:
                await manager.add_task(title, description, priority)
                progress.advance(task)

        console.print(
            "✅ Demo tasks created! Use '[primary]list[/primary]' command to see them.", style="success"
        )

    asyncio.run(_demo())


if __name__ == "__main__":
    cli()
