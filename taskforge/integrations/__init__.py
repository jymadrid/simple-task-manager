"""
Data export and import utilities
"""

import csv
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from taskforge.core.project import Project
from taskforge.core.task import Task
from taskforge.core.user import User
from taskforge.storage.base import StorageBackend


class DataExporter:
    """Export data to various formats"""

    def __init__(self, storage: StorageBackend):
        self.storage = storage

    async def export_tasks_to_json(
        self, project_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> str:
        """Export tasks to JSON format"""
        from taskforge.core.manager import TaskQuery

        query = TaskQuery(project_id=project_id, assigned_to=user_id, limit=10000)
        tasks = await self.storage.search_tasks(query, user_id or "system")

        tasks_data = [task.dict() for task in tasks]

        export_data = {
            "export_type": "tasks",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "project_id": project_id,
            "user_id": user_id,
            "count": len(tasks_data),
            "tasks": tasks_data,
        }

        return json.dumps(export_data, indent=2, default=str)

    async def export_tasks_to_csv(
        self, project_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> str:
        """Export tasks to CSV format"""
        from taskforge.core.manager import TaskQuery

        query = TaskQuery(project_id=project_id, assigned_to=user_id, limit=10000)
        tasks = await self.storage.search_tasks(query, user_id or "system")

        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "ID",
                "Title",
                "Description",
                "Status",
                "Priority",
                "Type",
                "Created By",
                "Assigned To",
                "Project ID",
                "Created At",
                "Due Date",
                "Progress",
                "Tags",
                "Category",
            ]
        )

        # Write tasks
        for task in tasks:
            writer.writerow(
                [
                    task.id,
                    task.title,
                    task.description or "",
                    task.status.value,
                    task.priority.value,
                    task.task_type.value,
                    task.created_by or "",
                    task.assigned_to or "",
                    task.project_id or "",
                    task.created_at.isoformat() if task.created_at else "",
                    task.due_date.isoformat() if task.due_date else "",
                    task.progress,
                    ", ".join(task.tags),
                    task.category or "",
                ]
            )

        return output.getvalue()

    async def export_tasks_to_markdown(
        self, project_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> str:
        """Export tasks to Markdown format"""
        from taskforge.core.manager import TaskQuery

        query = TaskQuery(project_id=project_id, assigned_to=user_id, limit=10000)
        tasks = await self.storage.search_tasks(query, user_id or "system")

        md_content = []
        md_content.append("# Task Export")
        md_content.append(
            f"\nExported on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if project_id:
            project = await self.storage.get_project(project_id)
            if project:
                md_content.append(f"Project: {project.name}")

        md_content.append(f"Total tasks: {len(tasks)}\n")

        # Group tasks by status
        status_groups = {}
        for task in tasks:
            status = task.status.value
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(task)

        for status, status_tasks in status_groups.items():
            md_content.append(
                f"## {status.replace('_', ' ').title()} ({len(status_tasks)})"
            )

            for task in status_tasks:
                md_content.append(f"\n### {task.title}")

                if task.description:
                    md_content.append(f"{task.description}")

                details = []
                details.append(f"**Priority:** {task.priority.value}")
                details.append(f"**Type:** {task.task_type.value}")
                details.append(f"**Progress:** {task.progress}%")

                if task.assigned_to:
                    details.append(f"**Assigned to:** {task.assigned_to}")

                if task.due_date:
                    details.append(f"**Due:** {task.due_date.strftime('%Y-%m-%d')}")

                if task.tags:
                    details.append(f"**Tags:** {', '.join(task.tags)}")

                md_content.append("\n".join(details))

        return "\n".join(md_content)

    async def export_full_backup(self) -> Dict[str, Any]:
        """Export complete database backup"""
        return await self.storage.export_data()

    async def export_projects_summary(self, user_id: str) -> str:
        """Export projects summary in JSON format"""
        projects = await self.storage.get_user_projects(user_id)

        projects_summary = []
        for project in projects:
            # Get project tasks
            from taskforge.core.manager import TaskQuery

            query = TaskQuery(project_id=project.id, limit=10000)
            tasks = await self.storage.search_tasks(query, user_id)

            summary = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status.value,
                "progress": project.progress,
                "task_count": len(tasks),
                "completed_tasks": len([t for t in tasks if t.status.value == "done"]),
                "created_at": (
                    project.created_at.isoformat() if project.created_at else None
                ),
                "owner_id": project.owner_id,
                "team_size": len(project.team_members),
            }
            projects_summary.append(summary)

        export_data = {
            "export_type": "projects_summary",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "count": len(projects_summary),
            "projects": projects_summary,
        }

        return json.dumps(export_data, indent=2, default=str)


class DataImporter:
    """Import data from various formats"""

    def __init__(self, storage: StorageBackend):
        self.storage = storage

    async def import_tasks_from_json(
        self, json_data: str, user_id: str
    ) -> Dict[str, Any]:
        """Import tasks from JSON format"""
        try:
            data = json.loads(json_data)

            if data.get("export_type") != "tasks":
                return {"error": "Invalid JSON format: not a task export"}

            tasks_data = data.get("tasks", [])
            imported_tasks = []
            errors = []

            for task_data in tasks_data:
                try:
                    # Create Task object
                    task = Task(**task_data)
                    # Override creator if needed
                    if not task.created_by:
                        task.created_by = user_id

                    created_task = await self.storage.create_task(task)
                    imported_tasks.append(created_task)

                except Exception as e:
                    errors.append(
                        f"Task '{task_data.get('title', 'Unknown')}': {str(e)}"
                    )

            return {
                "imported_count": len(imported_tasks),
                "error_count": len(errors),
                "errors": errors,
            }

        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {str(e)}"}
        except Exception as e:
            return {"error": f"Import failed: {str(e)}"}

    async def import_tasks_from_csv(
        self, csv_data: str, user_id: str
    ) -> Dict[str, Any]:
        """Import tasks from CSV format"""
        try:
            csv_reader = csv.DictReader(StringIO(csv_data))
            imported_tasks = []
            errors = []

            for row in csv_reader:
                try:
                    # Parse CSV row to Task
                    task_data = {
                        "title": row.get("Title", "").strip(),
                        "description": row.get("Description", "").strip() or None,
                        "status": row.get("Status", "todo").lower(),
                        "priority": row.get("Priority", "medium").lower(),
                        "task_type": row.get("Type", "other").lower(),
                        "created_by": user_id,
                        "assigned_to": row.get("Assigned To", "").strip() or None,
                        "project_id": row.get("Project ID", "").strip() or None,
                        "category": row.get("Category", "").strip() or None,
                        "progress": int(row.get("Progress", 0) or 0),
                    }

                    # Parse tags
                    tags_str = row.get("Tags", "").strip()
                    if tags_str:
                        task_data["tags"] = set(
                            tag.strip() for tag in tags_str.split(",")
                        )

                    # Parse due date
                    due_date_str = row.get("Due Date", "").strip()
                    if due_date_str:
                        try:
                            task_data["due_date"] = datetime.fromisoformat(due_date_str)
                        except ValueError:
                            pass  # Skip invalid dates

                    if not task_data["title"]:
                        errors.append(f"Row {csv_reader.line_num}: Title is required")
                        continue

                    task = Task(**task_data)
                    created_task = await self.storage.create_task(task)
                    imported_tasks.append(created_task)

                except Exception as e:
                    errors.append(f"Row {csv_reader.line_num}: {str(e)}")

            return {
                "imported_count": len(imported_tasks),
                "error_count": len(errors),
                "errors": errors,
            }

        except Exception as e:
            return {"error": f"CSV import failed: {str(e)}"}

    async def import_from_trello_backup(
        self, trello_json: str, user_id: str
    ) -> Dict[str, Any]:
        """Import from Trello JSON export"""
        try:
            data = json.loads(trello_json)

            # Create project from board
            board_name = data.get("name", "Imported from Trello")
            project = Project(
                name=board_name,
                description=data.get("desc", "Imported from Trello"),
                owner_id=user_id,
            )
            created_project = await self.storage.create_project(project)

            # Import cards as tasks
            cards = data.get("cards", [])
            lists = {lst["id"]: lst["name"] for lst in data.get("lists", [])}

            imported_tasks = []
            errors = []

            for card in cards:
                if card.get("closed"):
                    continue  # Skip archived cards

                try:
                    # Map Trello list to TaskForge status
                    list_name = lists.get(card.get("idList", ""), "").lower()
                    status = "todo"
                    if "doing" in list_name or "progress" in list_name:
                        status = "in_progress"
                    elif "done" in list_name or "complete" in list_name:
                        status = "done"

                    task = Task(
                        title=card.get("name", ""),
                        description=card.get("desc", "") or None,
                        status=status,
                        project_id=created_project.id,
                        created_by=user_id,
                        assigned_to=user_id,
                        external_links={"trello": card.get("url", "")},
                        integration_data={"trello_card_id": card.get("id", "")},
                    )

                    # Parse due date
                    if card.get("due"):
                        try:
                            task.due_date = datetime.fromisoformat(
                                card["due"].replace("Z", "+00:00")
                            )
                        except ValueError:
                            pass

                    # Parse labels as tags
                    labels = card.get("labels", [])
                    if labels:
                        task.tags = {
                            label["name"] for label in labels if label.get("name")
                        }

                    created_task = await self.storage.create_task(task)
                    imported_tasks.append(created_task)

                except Exception as e:
                    errors.append(f"Card '{card.get('name', 'Unknown')}': {str(e)}")

            return {
                "project_id": created_project.id,
                "project_name": created_project.name,
                "imported_count": len(imported_tasks),
                "error_count": len(errors),
                "errors": errors,
            }

        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {str(e)}"}
        except Exception as e:
            return {"error": f"Trello import failed: {str(e)}"}

    async def import_from_asana_csv(
        self, csv_data: str, user_id: str
    ) -> Dict[str, Any]:
        """Import from Asana CSV export"""
        try:
            csv_reader = csv.DictReader(StringIO(csv_data))

            # Group tasks by project
            projects_tasks = {}

            for row in csv_reader:
                project_name = row.get("Project", "Imported from Asana")
                if project_name not in projects_tasks:
                    projects_tasks[project_name] = []

                projects_tasks[project_name].append(row)

            imported_projects = []
            imported_tasks = []
            errors = []

            for project_name, tasks_data in projects_tasks.items():
                try:
                    # Create project
                    project = Project(
                        name=project_name,
                        description=f"Imported from Asana",
                        owner_id=user_id,
                    )
                    created_project = await self.storage.create_project(project)
                    imported_projects.append(created_project)

                    # Import tasks
                    for task_row in tasks_data:
                        try:
                            # Map Asana completion status
                            completed = task_row.get("Completed", "").lower() == "true"
                            status = "done" if completed else "todo"

                            # Parse priority
                            priority = "medium"
                            priority_str = task_row.get("Priority", "").lower()
                            if "high" in priority_str:
                                priority = "high"
                            elif "low" in priority_str:
                                priority = "low"

                            task = Task(
                                title=task_row.get("Name", "").strip(),
                                description=task_row.get("Notes", "").strip() or None,
                                status=status,
                                priority=priority,
                                project_id=created_project.id,
                                created_by=user_id,
                                assigned_to=task_row.get("Assignee", "").strip()
                                or user_id,
                            )

                            # Parse due date
                            due_date_str = task_row.get("Due Date", "").strip()
                            if due_date_str:
                                try:
                                    task.due_date = datetime.strptime(
                                        due_date_str, "%m/%d/%Y"
                                    )
                                except ValueError:
                                    pass

                            # Parse tags
                            tags_str = task_row.get("Tags", "").strip()
                            if tags_str:
                                task.tags = set(
                                    tag.strip() for tag in tags_str.split(",")
                                )

                            if task.title:
                                created_task = await self.storage.create_task(task)
                                imported_tasks.append(created_task)

                        except Exception as e:
                            errors.append(
                                f"Task '{task_row.get('Name', 'Unknown')}': {str(e)}"
                            )

                except Exception as e:
                    errors.append(f"Project '{project_name}': {str(e)}")

            return {
                "imported_projects": len(imported_projects),
                "imported_tasks": len(imported_tasks),
                "error_count": len(errors),
                "errors": errors,
            }

        except Exception as e:
            return {"error": f"Asana import failed: {str(e)}"}

    async def import_full_backup(self, backup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import complete database backup"""
        try:
            success = await self.storage.import_data(backup_data)
            if success:
                return {"message": "Backup imported successfully"}
            else:
                return {"error": "Backup import failed"}
        except Exception as e:
            return {"error": f"Backup import failed: {str(e)}"}


class IntegrationManager:
    """Manage integrations with external services"""

    def __init__(self, storage: StorageBackend):
        self.storage = storage
        self.exporter = DataExporter(storage)
        self.importer = DataImporter(storage)

    async def sync_with_external_service(
        self, service_type: str, service_config: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Sync data with external service"""
        if service_type == "github":
            return await self._sync_with_github(service_config, user_id)
        elif service_type == "trello":
            return await self._sync_with_trello(service_config, user_id)
        else:
            return {"error": f"Unsupported service type: {service_type}"}

    async def _sync_with_github(
        self, config: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Sync with GitHub Issues (placeholder)"""
        # This would integrate with GitHub API
        # Implementation depends on the GitHub plugin
        return {"message": "GitHub sync not implemented yet"}

    async def _sync_with_trello(
        self, config: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Sync with Trello (placeholder)"""
        # This would integrate with Trello API
        return {"message": "Trello sync not implemented yet"}

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get supported import/export formats"""
        return {
            "export": ["json", "csv", "markdown", "backup"],
            "import": ["json", "csv", "trello_json", "asana_csv", "backup"],
        }
