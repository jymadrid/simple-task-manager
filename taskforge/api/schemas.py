from datetime import datetime
from typing import List, Optional, Set

from pydantic import BaseModel, EmailStr, Field

from taskforge.core.project import ProjectStatus
from taskforge.core.task import TaskPriority, TaskStatus, TaskType


# User Schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserPublic(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


# Project Schemas
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[ProjectStatus] = None


class ProjectPublic(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    status: ProjectStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Task Schemas
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    project_id: str
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    tags: Set[str] = set()


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    progress: Optional[int] = Field(None, ge=0, le=100)


class TaskPublic(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    task_type: TaskType
    project_id: Optional[str]
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    due_date: Optional[datetime]
    tags: Set[str]
    progress: int

    class Config:
        from_attributes = True
