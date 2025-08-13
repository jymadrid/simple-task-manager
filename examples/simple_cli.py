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
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add the parent directory to the path so we can import taskforge
sys.path.insert(0, str(Path(__file__).parent.parent))

from taskforge.core.task import Task, TaskStatus, TaskPriority
from taskforge.core.user import User
from taskforge.core.project import Project
from taskforge.storage.json_storage import JSONStorage

console = Console()

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
                full_name="Default User"
            )
            default_user.id = self.current_user_id
            await self.storage.create_user(default_user)
            console.print("✅ Created default user", style="green")
    
    async def add_task(self, title: str, description: str = "", priority: str = "medium"):
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
            assigned_to=self.current_user_id
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
@click.argument('title')
@click.option('--description', '-d', default="", help="Task description")
@click.option('--priority', '-p', default="medium", 
              type=click.Choice(['low', 'medium', 'high', 'critical'], case_sensitive=False),
              help="Task priority")
def add(title: str, description: str, priority: str):
    """Add a new task"""
    async def _add():
        await manager.initialize()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Creating task...", total=None)
            created_task = await manager.add_task(title, description, priority)
            progress.update(task, description="Task created!")
        
        console.print(Panel(
            f"Task created successfully!\n\n"
            f"[bold]ID:[/bold] {created_task.id[:8]}...\n"
            f"[bold]Title:[/bold] {created_task.title}\n"
            f"[bold]Priority:[/bold] {created_task.priority.value}\n"
            f"[bold]Status:[/bold] {created_task.status.value}",
            title="New Task",
            border_style="green"
        ))
    
    asyncio.run(_add())

@cli.command()
@click.option('--status', '-s', help="Filter by status (todo, in_progress, done)")
@click.option('--limit', '-l', default=20, help="Maximum number of tasks to show")
def list(status: Optional[str], limit: int):
    """List all tasks"""
    async def _list():
        await manager.initialize()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading tasks...", total=None)
            tasks = await manager.list_tasks(status)
            progress.update(task, description="Tasks loaded!")
        
        if not tasks:
            console.print("📝 No tasks found. Use 'add' command to create your first task!", style="yellow")
            return
        
        # Create a rich table
        table = Table(title=f"📋 Your Tasks ({len(tasks)} total)")
        table.add_column("ID", style="cyan", width=10)
        table.add_column("Title", style="white", width=40)
        table.add_column("Status", style="magenta", width=12)
        table.add_column("Priority", style="yellow", width=10)
        table.add_column("Created", style="green", width=12)
        
        for task in tasks[:limit]:
            # Format creation date
            created_date = task.created_at.strftime("%m/%d %H:%M")
            
            # Color code status
            status_color = {
                "todo": "red",
                "in_progress": "yellow", 
                "done": "green",
                "blocked": "red",
                "cancelled": "dim"
            }.get(task.status.value, "white")
            
            # Color code priority
            priority_color = {
                "critical": "red bold",
                "high": "red",
                "medium": "yellow",
                "low": "green"
            }.get(task.priority.value, "white")
            
            table.add_row(
                task.id[:8] + "...",
                task.title[:37] + "..." if len(task.title) > 40 else task.title,
                f"[{status_color}]{task.status.value}[/{status_color}]",
                f"[{priority_color}]{task.priority.value}[/{priority_color}]",
                created_date
            )
        
        console.print(table)
        
        if len(tasks) > limit:
            console.print(f"\n💡 Showing {limit} of {len(tasks)} tasks. Use --limit to see more.", style="dim")
    
    asyncio.run(_list())

@cli.command()
@click.argument('task_id')
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
            console.print(f"❌ Task with ID '{task_id}' not found", style="red")
            return
        
        if matching_task.status == TaskStatus.DONE:
            console.print(f"ℹ️  Task '{matching_task.title}' is already completed", style="yellow")
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Completing task...", total=None)
            updated_task = await manager.complete_task(matching_task.id)
            progress.update(task, description="Task completed!")
        
        console.print(Panel(
            f"🎉 Task completed!\n\n"
            f"[bold]Title:[/bold] {updated_task.title}\n"
            f"[bold]Status:[/bold] {updated_task.status.value}\n"
            f"[bold]Completed:[/bold] {updated_task.completed_at.strftime('%Y-%m-%d %H:%M')}",
            title="Task Completed",
            border_style="green"
        ))
    
    asyncio.run(_complete())

@cli.command()
@click.argument('task_id')
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
            console.print(f"❌ Task with ID '{task_id}' not found", style="red")
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Deleting task...", total=None)
            deleted = await manager.delete_task(matching_task.id)
            progress.update(task, description="Task deleted!")
        
        if deleted:
            console.print(f"🗑️  Task '{matching_task.title}' deleted successfully", style="green")
        else:
            console.print(f"❌ Failed to delete task", style="red")
    
    asyncio.run(_delete())

@cli.command()
def stats():
    """Show task statistics"""
    async def _stats():
        await manager.initialize()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Calculating statistics...", total=None)
            stats = await manager.get_statistics()
            progress.update(task, description="Statistics ready!")
        
        # Create statistics panel
        stats_text = f"""
[bold]Total Tasks:[/bold] {stats['total_tasks']}
[bold]Completed:[/bold] {stats['completed_tasks']} ({stats['completion_rate']:.1%})
[bold]In Progress:[/bold] {stats['in_progress_tasks']}
[bold]Overdue:[/bold] {stats['overdue_tasks']}

[bold]Priority Distribution:[/bold]
"""
        
        for priority, count in stats['priority_distribution'].items():
            stats_text += f"  • {priority.title()}: {count}\n"
        
        stats_text += "\n[bold]Status Distribution:[/bold]\n"
        for status, count in stats['status_distribution'].items():
            stats_text += f"  • {status.replace('_', ' ').title()}: {count}\n"
        
        console.print(Panel(
            stats_text.strip(),
            title="📊 Task Statistics",
            border_style="blue"
        ))
    
    asyncio.run(_stats())

@cli.command()
def demo():
    """Create demo tasks for testing"""
    async def _demo():
        await manager.initialize()
        
        demo_tasks = [
            ("Fix authentication bug", "Users can't log in with special characters", "high"),
            ("Update documentation", "Add examples for new API endpoints", "medium"),
            ("Implement dark mode", "Add dark theme support to the web interface", "low"),
            ("Optimize database queries", "Improve performance of task search", "high"),
            ("Write unit tests", "Add tests for the new user management features", "medium"),
        ]
        
        console.print("🎭 Creating demo tasks...", style="blue")
        
        with Progress(console=console) as progress:
            task = progress.add_task("Creating demo tasks...", total=len(demo_tasks))
            
            for title, description, priority in demo_tasks:
                await manager.add_task(title, description, priority)
                progress.advance(task)
        
        console.print("✅ Demo tasks created! Use 'list' command to see them.", style="green")
    
    asyncio.run(_demo())

if __name__ == "__main__":
    cli()