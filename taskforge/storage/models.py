"""
SQLAlchemy models for database storage
"""

from datetime import datetime
from typing import Dict, Any, List, Set
import json
from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from taskforge.core.task import Task, TaskStatus, TaskPriority, TaskType
from taskforge.core.project import Project, ProjectStatus
from taskforge.core.user import User, UserRole

Base = declarative_base()


class TaskModel(Base):
    """SQLAlchemy model for Task"""
    __tablename__ = 'tasks'
    
    # Core fields
    id = Column(String, primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    
    # Status and priority
    status = Column(String(50), nullable=False, default='todo')
    priority = Column(String(50), nullable=False, default='medium')
    task_type = Column(String(50), nullable=False, default='other')
    
    # Ownership and assignment
    created_by = Column(String)
    assigned_to = Column(String)
    project_id = Column(String)
    
    # Temporal fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
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
    def from_task(cls, task: Task) -> 'TaskModel':
        """Create TaskModel from Task"""
        return cls(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            task_type=task.task_type.value,
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
            dependencies=[dep.dict() for dep in task.dependencies],
            subtasks=task.subtasks,
            parent_task=task.parent_task,
            time_tracking=task.time_tracking.__dict__,
            recurrence=task.recurrence.dict() if task.recurrence else None,
            custom_fields=task.custom_fields,
            activity_log=task.activity_log,
            progress=task.progress,
            completion_criteria=task.completion_criteria,
            external_links=task.external_links,
            integration_data=task.integration_data
        )
    
    def to_task(self) -> Task:
        """Convert TaskModel to Task"""
        from taskforge.core.task import TaskDependency, TimeTracking, TaskRecurrence
        
        # Convert dependencies
        dependencies = []
        for dep_data in (self.dependencies or []):
            dependencies.append(TaskDependency(**dep_data))
        
        # Convert time tracking
        time_tracking = TimeTracking(**(self.time_tracking or {}))
        
        # Convert recurrence
        recurrence = None
        if self.recurrence:
            recurrence = TaskRecurrence(**self.recurrence)
        
        return Task(
            id=self.id,
            title=self.title,
            description=self.description,
            status=TaskStatus(self.status),
            priority=TaskPriority(self.priority),
            task_type=TaskType(self.task_type),
            created_by=self.created_by,
            assigned_to=self.assigned_to,
            project_id=self.project_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            due_date=self.due_date,
            start_date=self.start_date,
            completed_at=self.completed_at,
            tags=set(self.tags or []),
            labels=self.labels or [],
            category=self.category,
            dependencies=dependencies,
            subtasks=self.subtasks or [],
            parent_task=self.parent_task,
            time_tracking=time_tracking,
            recurrence=recurrence,
            custom_fields=self.custom_fields or {},
            activity_log=self.activity_log or [],
            progress=self.progress or 0,
            completion_criteria=self.completion_criteria or [],
            external_links=self.external_links or {},
            integration_data=self.integration_data or {}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for updates"""
        return {
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'task_type': self.task_type,
            'created_by': self.created_by,
            'assigned_to': self.assigned_to,
            'project_id': self.project_id,
            'updated_at': self.updated_at,
            'due_date': self.due_date,
            'start_date': self.start_date,
            'completed_at': self.completed_at,
            'tags': self.tags,
            'labels': self.labels,
            'category': self.category,
            'dependencies': self.dependencies,
            'subtasks': self.subtasks,
            'parent_task': self.parent_task,
            'time_tracking': self.time_tracking,
            'recurrence': self.recurrence,
            'custom_fields': self.custom_fields,
            'activity_log': self.activity_log,
            'progress': self.progress,
            'completion_criteria': self.completion_criteria,
            'external_links': self.external_links,
            'integration_data': self.integration_data
        }


class ProjectModel(Base):
    """SQLAlchemy model for Project"""
    __tablename__ = 'projects'
    
    # Core fields
    id = Column(String, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Status and metadata
    status = Column(String(50), nullable=False, default='planning')
    color = Column(String(7))  # Hex color
    icon = Column(String(50))
    
    # Ownership and team
    owner_id = Column(String, nullable=False)
    team_members = Column(JSON, default=list)  # List of user IDs
    
    # Temporal fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
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
    def from_project(cls, project: Project) -> 'ProjectModel':
        """Create ProjectModel from Project"""
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status.value,
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
            activity_log=project.activity_log
        )
    
    def to_project(self) -> Project:
        """Convert ProjectModel to Project"""
        return Project(
            id=self.id,
            name=self.name,
            description=self.description,
            status=ProjectStatus(self.status),
            color=self.color,
            icon=self.icon,
            owner_id=self.owner_id,
            team_members=set(self.team_members or []),
            created_at=self.created_at,
            updated_at=self.updated_at,
            start_date=self.start_date,
            end_date=self.end_date,
            tags=set(self.tags or []),
            category=self.category,
            progress=self.progress or 0,
            task_count=self.task_count or 0,
            completed_task_count=self.completed_task_count or 0,
            budget=self.budget,
            estimated_hours=self.estimated_hours,
            actual_hours=self.actual_hours or 0.0,
            custom_fields=self.custom_fields or {},
            settings=self.settings or {},
            activity_log=self.activity_log or []
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for updates"""
        return {
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'color': self.color,
            'icon': self.icon,
            'owner_id': self.owner_id,
            'team_members': self.team_members,
            'updated_at': self.updated_at,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'tags': self.tags,
            'category': self.category,
            'progress': self.progress,
            'task_count': self.task_count,
            'completed_task_count': self.completed_task_count,
            'budget': self.budget,
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'custom_fields': self.custom_fields,
            'settings': self.settings,
            'activity_log': self.activity_log
        }


class UserModel(Base):
    """SQLAlchemy model for User"""
    __tablename__ = 'users'
    
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
    role = Column(String(50), nullable=False, default='developer')
    custom_permissions = Column(JSON, default=list)
    
    # Profile (stored as JSON)
    profile = Column(JSON, default=dict)
    
    # Temporal fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime)
    last_login = Column(DateTime)
    
    # Organization
    teams = Column(JSON, default=list)  # Project IDs
    
    # Activity and preferences
    activity_log = Column(JSON, default=list)
    settings = Column(JSON, default=dict)
    
    @classmethod
    def from_user(cls, user: User) -> 'UserModel':
        """Create UserModel from User"""
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            password_hash=user.password_hash,
            is_active=user.is_active,
            is_verified=user.is_verified,
            role=user.role.value,
            custom_permissions=[perm.value for perm in user.custom_permissions],
            profile=user.profile.dict(),
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            teams=list(user.teams),
            activity_log=user.activity_log,
            settings=user.settings
        )
    
    def to_user(self) -> User:
        """Convert UserModel to User"""
        from taskforge.core.user import Permission, UserProfile
        
        # Convert custom permissions
        custom_permissions = set()
        for perm_str in (self.custom_permissions or []):
            try:
                custom_permissions.add(Permission(perm_str))
            except ValueError:
                pass  # Skip invalid permissions
        
        # Convert profile
        profile = UserProfile(**(self.profile or {}))
        
        return User(
            id=self.id,
            username=self.username,
            email=self.email,
            full_name=self.full_name,
            password_hash=self.password_hash,
            is_active=self.is_active,
            is_verified=self.is_verified,
            role=UserRole(self.role),
            custom_permissions=custom_permissions,
            profile=profile,
            created_at=self.created_at,
            updated_at=self.updated_at,
            last_login=self.last_login,
            teams=set(self.teams or []),
            activity_log=self.activity_log or [],
            settings=self.settings or {}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for updates"""
        return {
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'password_hash': self.password_hash,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'role': self.role,
            'custom_permissions': self.custom_permissions,
            'profile': self.profile,
            'updated_at': self.updated_at,
            'last_login': self.last_login,
            'teams': self.teams,
            'activity_log': self.activity_log,
            'settings': self.settings
        }