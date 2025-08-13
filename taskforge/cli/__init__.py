"""
Modern CLI interface using Typer
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich import print as rprint
from rich.prompt import Prompt, Confirm

from taskforge.core.manager import TaskManager, TaskQuery
from taskforge.core.task import Task, TaskStatus, TaskPriority, TaskType
from taskforge.core.project import Project, ProjectStatus
from taskforge.core.user import User, UserRole
from taskforge.storage.json_storage import JSONStorage
from taskforge.utils.config import Config

app = typer.Typer(
    name="taskforge",
    help="🔥 TaskForge - A comprehensive task management platform",
    add_completion=False,
    rich_markup_mode="rich"
)
console = Console()

# Global manager instance
manager: Optional[TaskManager] = None


def get_manager() -> TaskManager:
    """Get or create the task manager instance"""
    global manager
    if manager is None:
        config = Config.load()
        storage = JSONStorage(config.data_directory)
        manager = TaskManager(storage)
    return manager


# Task Commands
task_app = typer.Typer(name="task", help="Task management commands")
app.add_typer(task_app)


@task_app.command("add")
def add_task(
    title: str = typer.Argument(..., help="Task title"),
    description: Optional[str] = typer.Option(None, "-d", "--description", help="Task description"),
    priority: TaskPriority = typer.Option(TaskPriority.MEDIUM, "-p", "--priority", help="Task priority"),
    task_type: TaskType = typer.Option(TaskType.OTHER, "-t", "--type", help="Task type"),
    due_date: Optional[str] = typer.Option(None, "--due", help="Due date (YYYY-MM-DD)"),
    project: Optional[str] = typer.Option(None, "--project", help="Project ID or name"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", help="Task tags"),
):
    """Add a new task"""
    async def _add_task():
        mgr = get_manager()
        
        # Parse due date
        due_dt = None
        if due_date:
            try:
                due_dt = datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                rprint("[red]Invalid due date format. Use YYYY-MM-DD[/red]")
                return
        
        # Create task
        task = Task(
            title=title,
            description=description,
            priority=priority,
            task_type=task_type,
            due_date=due_dt,
            project_id=project,
            tags=set(tags) if tags else set()
        )
        
        try:
            created_task = await mgr.create_task(task, "default_user")  # TODO: Get from auth
            rprint(f"[green]✅ Task created: {created_task.title} (ID: {created_task.id[:8]})[/green]")
        except Exception as e:
            rprint(f"[red]❌ Error creating task: {e}[/red]")
    
    asyncio.run(_add_task())


@task_app.command("list")
def list_tasks(
    status: Optional[List[TaskStatus]] = typer.Option(None, "-s", "--status", help="Filter by status"),
    priority: Optional[List[TaskPriority]] = typer.Option(None, "-p", "--priority", help="Filter by priority"),
    project: Optional[str] = typer.Option(None, "--project", help="Filter by project"),
    assigned: Optional[str] = typer.Option(None, "--assigned", help="Filter by assignee"),
    limit: int = typer.Option(20, "-l", "--limit", help="Number of tasks to show"),
    overdue: bool = typer.Option(False, "--overdue", help="Show only overdue tasks"),
):
    """List tasks with filtering options"""
    async def _list_tasks():
        mgr = get_manager()
        
        # Special case for overdue tasks
        if overdue:
            tasks = await mgr.get_overdue_tasks("default_user")
        else:
            query = TaskQuery(
                status=status,
                priority=priority,
                project_id=project,
                assigned_to=assigned,
                limit=limit
            )
            tasks = await mgr.search_tasks(query, "default_user")
        
        if not tasks:
            rprint("[yellow]No tasks found[/yellow]")
            return
        
        # Create rich table
        table = Table(title=f"📋 Tasks ({len(tasks)} found)")
        table.add_column("ID", style="dim", width=8)
        table.add_column("Title", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Priority", justify="center")
        table.add_column("Due Date", justify="center")
        table.add_column("Progress", justify="center")
        
        for task in tasks:
            # Status styling
            status_color = {
                TaskStatus.TODO: "white",
                TaskStatus.IN_PROGRESS: "blue",
                TaskStatus.BLOCKED: "red",
                TaskStatus.REVIEW: "yellow",
                TaskStatus.DONE: "green",
                TaskStatus.CANCELLED: "dim",
            }.get(task.status, "white")
            
            # Priority styling
            priority_color = {
                TaskPriority.CRITICAL: "red",
                TaskPriority.HIGH: "orange",
                TaskPriority.MEDIUM: "yellow",
                TaskPriority.LOW: "green",
            }.get(task.priority, "white")
            
            # Due date formatting
            due_str = ""
            if task.due_date:
                if task.is_overdue():
                    due_str = f"[red]{task.due_date.strftime('%Y-%m-%d')} (overdue)[/red]"
                else:
                    due_str = task.due_date.strftime('%Y-%m-%d')
            
            # Progress bar
            progress_str = f"{task.progress}%"
            if task.progress == 100:
                progress_str = f"[green]{progress_str}[/green]"
            elif task.progress > 50:
                progress_str = f"[yellow]{progress_str}[/yellow]"
            
            table.add_row(
                task.id[:8],
                task.title,
                f"[{status_color}]{task.status.value}[/{status_color}]",
                f"[{priority_color}]{task.priority.value}[/{priority_color}]",
                due_str,
                progress_str
            )
        
        console.print(table)
    
    asyncio.run(_list_tasks())


@task_app.command("show")
def show_task(task_id: str = typer.Argument(..., help="Task ID")):
    """Show detailed task information"""
    async def _show_task():
        mgr = get_manager()
        task = await mgr.get_task(task_id)
        
        if not task:
            rprint(f"[red]❌ Task {task_id} not found[/red]")
            return
        
        # Create detailed panel
        details = f"""
[bold]Title:[/bold] {task.title}
[bold]ID:[/bold] {task.id}
[bold]Status:[/bold] {task.status.value}
[bold]Priority:[/bold] {task.priority.value}
[bold]Type:[/bold] {task.task_type.value}
[bold]Progress:[/bold] {task.progress}%
[bold]Created:[/bold] {task.created_at.strftime('%Y-%m-%d %H:%M')}
"""
        
        if task.description:
            details += f"[bold]Description:[/bold] {task.description}\n"
        
        if task.due_date:
            due_color = "red" if task.is_overdue() else "white"
            details += f"[bold]Due Date:[/bold] [{due_color}]{task.due_date.strftime('%Y-%m-%d %H:%M')}[/{due_color}]\n"
        
        if task.tags:
            details += f"[bold]Tags:[/bold] {', '.join(task.tags)}\n"
        
        if task.dependencies:
            deps = [dep.task_id[:8] for dep in task.dependencies]
            details += f"[bold]Dependencies:[/bold] {', '.join(deps)}\n"
        
        console.print(Panel(details.strip(), title="📝 Task Details", border_style="blue"))
    
    asyncio.run(_show_task())


@task_app.command("update")
def update_task(
    task_id: str = typer.Argument(..., help="Task ID"),
    title: Optional[str] = typer.Option(None, "--title", help="New title"),
    description: Optional[str] = typer.Option(None, "-d", "--description", help="New description"),
    status: Optional[TaskStatus] = typer.Option(None, "-s", "--status", help="New status"),
    priority: Optional[TaskPriority] = typer.Option(None, "-p", "--priority", help="New priority"),
    progress: Optional[int] = typer.Option(None, "--progress", help="Progress percentage (0-100)"),
):
    """Update an existing task"""
    async def _update_task():
        mgr = get_manager()
        
        # Build updates dict
        updates = {}
        if title is not None:
            updates['title'] = title
        if description is not None:
            updates['description'] = description
        if status is not None:
            updates['status'] = status
        if priority is not None:
            updates['priority'] = priority
        if progress is not None:
            updates['progress'] = progress
        
        if not updates:
            rprint("[yellow]No updates specified[/yellow]")
            return
        
        try:
            updated_task = await mgr.update_task(task_id, updates, "default_user")
            rprint(f"[green]✅ Task updated: {updated_task.title}[/green]")
        except Exception as e:
            rprint(f"[red]❌ Error updating task: {e}[/red]")
    
    asyncio.run(_update_task())


@task_app.command("delete")
def delete_task(task_id: str = typer.Argument(..., help="Task ID")):
    """Delete a task"""
    async def _delete_task():
        mgr = get_manager()
        
        # Confirm deletion
        if not Confirm.ask(f"Are you sure you want to delete task {task_id[:8]}?"):
            rprint("[yellow]Cancelled[/yellow]")
            return
        
        try:
            success = await mgr.delete_task(task_id, "default_user")
            if success:
                rprint(f"[green]✅ Task {task_id[:8]} deleted[/green]")
            else:
                rprint(f"[red]❌ Task {task_id} not found[/red]")
        except Exception as e:
            rprint(f"[red]❌ Error deleting task: {e}[/red]")
    
    asyncio.run(_delete_task())


# Project Commands
project_app = typer.Typer(name="project", help="Project management commands")
app.add_typer(project_app)


@project_app.command("create")
def create_project(
    name: str = typer.Argument(..., help="Project name"),
    description: Optional[str] = typer.Option(None, "-d", "--description", help="Project description"),
):
    """Create a new project"""
    async def _create_project():
        mgr = get_manager()
        
        project = Project(
            name=name,
            description=description,
            owner_id="default_user"
        )
        
        try:
            created_project = await mgr.create_project(project, "default_user")
            rprint(f"[green]✅ Project created: {created_project.name} (ID: {created_project.id[:8]})[/green]")
        except Exception as e:
            rprint(f"[red]❌ Error creating project: {e}[/red]")
    
    asyncio.run(_create_project())


# Statistics and Reports
@app.command("stats")
def show_statistics(
    project: Optional[str] = typer.Option(None, "--project", help="Project ID"),
    user: Optional[str] = typer.Option(None, "--user", help="User ID"),
):
    """Show task statistics and metrics"""
    async def _show_stats():
        mgr = get_manager()
        
        try:
            stats = await mgr.get_task_statistics(project, user)
            
            # Create statistics table
            table = Table(title="📊 Task Statistics")
            table.add_column("Metric", style="bold")
            table.add_column("Value", justify="right")
            
            table.add_row("Total Tasks", str(stats.get('total_tasks', 0)))
            table.add_row("Completed Tasks", str(stats.get('completed_tasks', 0)))
            table.add_row("In Progress", str(stats.get('in_progress_tasks', 0)))
            table.add_row("Overdue Tasks", str(stats.get('overdue_tasks', 0)))
            
            completion_rate = stats.get('completion_rate', 0)
            table.add_row("Completion Rate", f"{completion_rate:.1%}")
            
            console.print(table)
            
        except Exception as e:
            rprint(f"[red]❌ Error getting statistics: {e}[/red]")
    
    asyncio.run(_show_stats())


@app.command("dashboard")
def show_dashboard():
    """Show interactive dashboard"""
    async def _show_dashboard():
        mgr = get_manager()
        
        try:
            # Get overview data
            overdue_tasks = await mgr.get_overdue_tasks("default_user")
            upcoming_tasks = await mgr.get_upcoming_tasks(7, "default_user")
            stats = await mgr.get_task_statistics()
            
            console.print(Panel.fit("🔥 TaskForge Dashboard", style="bold blue"))
            
            # Quick stats
            stats_table = Table.grid(padding=1)
            stats_table.add_column(style="bold")
            stats_table.add_column(justify="right")
            
            stats_table.add_row("📋 Total Tasks:", str(stats.get('total_tasks', 0)))
            stats_table.add_row("✅ Completed:", str(stats.get('completed_tasks', 0)))
            stats_table.add_row("🔄 In Progress:", str(stats.get('in_progress_tasks', 0)))
            stats_table.add_row("⚠️ Overdue:", f"[red]{len(overdue_tasks)}[/red]")
            
            console.print(Panel(stats_table, title="Quick Stats", border_style="green"))
            
            # Overdue tasks warning
            if overdue_tasks:
                console.print(f"\n[red]⚠️ You have {len(overdue_tasks)} overdue tasks![/red]")
                for task in overdue_tasks[:3]:  # Show first 3
                    days_overdue = (datetime.utcnow() - task.due_date).days
                    console.print(f"  • {task.title} ({days_overdue} days overdue)")
            
            # Upcoming tasks
            if upcoming_tasks:
                console.print(f"\n[yellow]📅 {len(upcoming_tasks)} tasks due in the next 7 days[/yellow]")
                for task in upcoming_tasks[:5]:  # Show first 5
                    days_until = task.days_until_due()
                    console.print(f"  • {task.title} (due in {days_until} days)")
            
        except Exception as e:
            rprint(f"[red]❌ Error showing dashboard: {e}[/red]")
    
    asyncio.run(_show_dashboard())


def main():
    """Main CLI entry point"""
    app()


if __name__ == "__main__":
    main()