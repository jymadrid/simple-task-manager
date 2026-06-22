"""
SQLAlchemy models for database storage
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, cast

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import declarative_base

from taskforge.core.project import Project, ProjectStatus
from taskforge.core.task import Task, TaskPriority, TaskStatus, TaskType
from taskforge.core.user import User, UserRole
from taskforge.utils.values import enum_value

Base: Any = declarative_base()


class TaskModel(Base):
    """SQLAlchemy model for Task"""

    __tablename__ = "tasks"

    # Core fields
    id = Column(String, primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)

    # Status and priority
    status = Column(String(50), nullable=False, default="todo")
    priority = Column(String(50), nullable=False, default="medium")
    task_type = Column(String(50), nullable=False, default="other")

    # Ownership and assignment
    created_by = Column(String)
    assigned_to = Column(String)
    project_id = Column(String)

    # Temporal fields
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(DateTime)
    due_date = Column(DateTime)
    start_date = Column(DateTime)
    completed_at = Column(DateTime)

    # Categorization (stored as JSON arrays)
    tags = Column(JSON, default=list)
    labels = Column(JSON, default=list)
    category = Column(String(100))

    # Advanced features (stored as JSON)
    dependencies = Column(JSON, default=list)
    subtasks = Column(JSON, default=list)
    parent_task = Column(String)

    # Time tracking (stored as JSON)
    time_tracking = Column(JSON, default=dict)

    # Recurrence (stored as JSON)
    recurrence = Column(JSON)

    # Custom fields (stored as JSON)
    custom_fields = Column(JSON, default=dict)

    # Activity and history (stored as JSON)
    activity_log = Column(JSON, default=list)

    # Progress tracking
    progress = Column(Integer, default=0)
    completion_criteria = Column(JSON, default=list)

    # External integration (stored as JSON)
    external_links = Column(JSON, default=dict)
    integration_data = Column(JSON, default=dict)

    @classmethod
    def from_task(cls, task: Task) -> "TaskModel":
        """Create TaskModel from Task"""
        return cls(
            id=task.id,
            title=task.title,
            description=task.description,
            status=enum_value(task.status),
            priority=enum_value(task.priority),
            task_type=enum_value(task.task_type),
            created_by=task.created_by,
            assigned_to=task.assigned_to,
            project_id=task.project_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
            due_date=task.due_date,
            start_date=task.start_date,
            completed_at=task.completed_at,
            tags=list(task.tags),
            labels=task.labels,
            category=task.category,
            dependencies=[dep.model_dump() for dep in task.dependencies],
            subtasks=task.subtasks,
            parent_task=task.parent_task,
            time_tracking=task.time_tracking.__dict__,
            recurrence=task.recurrence.model_dump() if task.recurrence else None,
            custom_fields=task.custom_fields,
            activity_log=task.activity_log,
            progress=task.progress,
            completion_criteria=task.completion_criteria,
            external_links=task.external_links,
            integration_data=task.integration_data,
        )

    def to_task(self) -> Task:
        """Convert TaskModel to Task"""
        from taskforge.core.task import TaskDependency, TaskRecurrence, TimeTracking

        model = cast(Any, self)

        # Convert dependencies
        dependencies = []
        for dep_data in model.dependencies or []:
            dependencies.append(TaskDependency(**dep_data))

        # Convert time tracking
        time_tracking = TimeTracking(**(model.time_tracking or {}))

        # Convert recurrence
        recurrence = None
        if model.recurrence:
            recurrence = TaskRecurrence(**model.recurrence)

        return Task(
            id=model.id,
            title=model.title,
            description=model.description,
            status=TaskStatus(model.status),
            priority=TaskPriority(model.priority),
            task_type=TaskType(model.task_type),
            created_by=model.created_by,
            assigned_to=model.assigned_to,
            project_id=model.project_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            due_date=model.due_date,
            start_date=model.start_date,
            completed_at=model.completed_at,
            tags=set(model.tags or []),
            labels=model.labels or [],
            category=model.category,
            dependencies=dependencies,
            subtasks=model.subtasks or [],
            parent_task=model.parent_task,
            time_tracking=time_tracking,
            recurrence=recurrence,
            custom_fields=model.custom_fields or {},
            activity_log=model.activity_log or [],
            progress=model.progress or 0,
            completion_criteria=model.completion_criteria or [],
            external_links=model.external_links or {},
            integration_data=model.integration_data or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for updates"""
        model = cast(Any, self)
        return {
            "title": model.title,
            "description": model.description,
            "status": model.status,
            "priority": model.priority,
            "task_type": model.task_type,
            "created_by": model.created_by,
            "assigned_to": model.assigned_to,
            "project_id": model.project_id,
            "updated_at": model.updated_at,
            "due_date": model.due_date,
            "start_date": model.start_date,
            "completed_at": model.completed_at,
            "tags": model.tags,
            "labels": model.labels,
            "category": model.category,
            "dependencies": model.dependencies,
            "subtasks": model.subtasks,
            "parent_task": model.parent_task,
            "time_tracking": model.time_tracking,
            "recurrence": model.recurrence,
            "custom_fields": model.custom_fields,
            "activity_log": model.activity_log,
            "progress": model.progress,
            "completion_criteria": model.completion_criteria,
            "external_links": model.external_links,
            "integration_data": model.integration_data,
        }


class ProjectModel(Base):
    """SQLAlchemy model for Project"""

    __tablename__ = "projects"

    # Core fields
    id = Column(String, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Status and metadata
    status = Column(String(50), nullable=False, default="planning")
    color = Column(String(7))  # Hex color
    icon = Column(String(50))

    # Ownership and team
    owner_id = Column(String, nullable=False)
    team_members = Column(JSON, default=list)  # List of user IDs

    # Temporal fields
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(DateTime)
    start_date = Column(DateTime)
    end_date = Column(DateTime)

    # Organization
    tags = Column(JSON, default=list)
    category = Column(String(100))

    # Progress tracking
    progress = Column(Integer, default=0)
    task_count = Column(Integer, default=0)
    completed_task_count = Column(Integer, default=0)

    # Budget and resources
    budget = Column(Float)
    estimated_hours = Column(Float)
    actual_hours = Column(Float, default=0.0)

    # Custom fields and metadata
    custom_fields = Column(JSON, default=dict)
    settings = Column(JSON, default=dict)

    # Activity tracking
    activity_log = Column(JSON, default=list)

    @classmethod
    def from_project(cls, project: Project) -> "ProjectModel":
        """Create ProjectModel from Project"""
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            status=enum_value(project.status),
            color=project.color,
            icon=project.icon,
            owner_id=project.owner_id,
            team_members=list(project.team_members),
            created_at=project.created_at,
            updated_at=project.updated_at,
            start_date=project.start_date,
            end_date=project.end_date,
            tags=list(project.tags),
            category=project.category,
            progress=project.progress,
            task_count=project.task_count,
            completed_task_count=project.completed_task_count,
            budget=project.budget,
            estimated_hours=project.estimated_hours,
            actual_hours=project.actual_hours,
            custom_fields=project.custom_fields,
            settings=project.settings,
            activity_log=project.activity_log,
        )

    def to_project(self) -> Project:
        """Convert ProjectModel to Project"""
        model = cast(Any, self)
        return Project(
            id=model.id,
            name=model.name,
            description=model.description,
            status=ProjectStatus(model.status),
            color=model.color,
            icon=model.icon,
            owner_id=model.owner_id,
            team_members=set(model.team_members or []),
            created_at=model.created_at,
            updated_at=model.updated_at,
            start_date=model.start_date,
            end_date=model.end_date,
            tags=set(model.tags or []),
            category=model.category,
            progress=model.progress or 0,
            task_count=model.task_count or 0,
            completed_task_count=model.completed_task_count or 0,
            budget=model.budget,
            estimated_hours=model.estimated_hours,
            actual_hours=model.actual_hours or 0.0,
            custom_fields=model.custom_fields or {},
            settings=model.settings or {},
            activity_log=model.activity_log or [],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for updates"""
        model = cast(Any, self)
        return {
            "name": model.name,
            "description": model.description,
            "status": model.status,
            "color": model.color,
            "icon": model.icon,
            "owner_id": model.owner_id,
            "team_members": model.team_members,
            "updated_at": model.updated_at,
            "start_date": model.start_date,
            "end_date": model.end_date,
            "tags": model.tags,
            "category": model.category,
            "progress": model.progress,
            "task_count": model.task_count,
            "completed_task_count": model.completed_task_count,
            "budget": model.budget,
            "estimated_hours": model.estimated_hours,
            "actual_hours": model.actual_hours,
            "custom_fields": model.custom_fields,
            "settings": model.settings,
            "activity_log": model.activity_log,
        }


class UserModel(Base):
    """SQLAlchemy model for User"""

    __tablename__ = "users"

    # Core fields
    id = Column(String, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    full_name = Column(String(100))

    # Authentication
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Authorization
    role = Column(String(50), nullable=False, default="developer")
    custom_permissions = Column(JSON, default=list)

    # Profile (stored as JSON)
    profile = Column(JSON, default=dict)

    # Temporal fields
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(DateTime)
    last_login = Column(DateTime)

    # Organization
    teams = Column(JSON, default=list)  # Project IDs

    # Activity and preferences
    activity_log = Column(JSON, default=list)
    settings = Column(JSON, default=dict)

    @classmethod
    def from_user(cls, user: User) -> "UserModel":
        """Create UserModel from User"""
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            password_hash=user.password_hash,
            is_active=user.is_active,
            is_verified=user.is_verified,
            role=enum_value(user.role),
            custom_permissions=[enum_value(perm) for perm in user.custom_permissions],
            profile=user.profile.model_dump(),
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            teams=list(user.teams),
            activity_log=user.activity_log,
            settings=user.settings,
        )

    def to_user(self) -> User:
        """Convert UserModel to User"""
        from taskforge.core.user import Permission, UserProfile

        model = cast(Any, self)

        # Convert custom permissions
        custom_permissions = set()
        for perm_str in model.custom_permissions or []:
            try:
                custom_permissions.add(Permission(perm_str))
            except ValueError:
                pass  # Skip invalid permissions

        # Convert profile
        profile = UserProfile(**(model.profile or {}))

        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            full_name=model.full_name,
            password_hash=model.password_hash,
            is_active=model.is_active,
            is_verified=model.is_verified,
            role=UserRole(model.role),
            custom_permissions=custom_permissions,
            profile=profile,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login=model.last_login,
            teams=set(model.teams or []),
            activity_log=model.activity_log or [],
            settings=model.settings or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for updates"""
        model = cast(Any, self)
        return {
            "username": model.username,
            "email": model.email,
            "full_name": model.full_name,
            "password_hash": model.password_hash,
            "is_active": model.is_active,
            "is_verified": model.is_verified,
            "role": model.role,
            "custom_permissions": model.custom_permissions,
            "profile": model.profile,
            "updated_at": model.updated_at,
            "last_login": model.last_login,
            "teams": model.teams,
            "activity_log": model.activity_log,
            "settings": model.settings,
        }
