"""
Project management model
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ProjectStatus(str, Enum):
    """Project status enumeration"""

    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class Project(BaseModel):
    """
    Project model for organizing tasks

    Projects provide a way to group related tasks and manage them collectively.
    They support team collaboration, progress tracking, and resource management.
    """

    # Core fields
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)

    # Status and metadata
    status: ProjectStatus = ProjectStatus.PLANNING
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")  # Hex color
    icon: Optional[str] = None

    # Ownership and team
    owner_id: str = Field(..., description="Project owner user ID")
    team_members: Set[str] = Field(default_factory=set)  # User IDs

    # Temporal fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Organization
    tags: Set[str] = Field(default_factory=set)
    category: Optional[str] = None

    # Progress tracking
    progress: int = Field(0, ge=0, le=100)
    task_count: int = 0
    completed_task_count: int = 0

    # Budget and resources (optional)
    budget: Optional[float] = None
    estimated_hours: Optional[float] = None
    actual_hours: float = 0.0

    # Custom fields and metadata
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)

    # Activity tracking
    activity_log: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            set: list,
        },
    )

    def add_member(self, user_id: str) -> None:
        """Add a team member to the project"""
        self.team_members.add(user_id)
        self._log_activity("member_added", {"user_id": user_id})

    def remove_member(self, user_id: str) -> None:
        """Remove a team member from the project"""
        self.team_members.discard(user_id)
        self._log_activity("member_removed", {"user_id": user_id})

    def update_progress(self, completed_tasks: int, total_tasks: int) -> None:
        """Update project progress based on task completion"""
        self.task_count = total_tasks
        self.completed_task_count = completed_tasks

        if total_tasks > 0:
            self.progress = int((completed_tasks / total_tasks) * 100)
        else:
            self.progress = 0

        # Auto-complete project if all tasks are done
        if completed_tasks == total_tasks and total_tasks > 0:
            if self.status == ProjectStatus.ACTIVE:
                self.status = ProjectStatus.COMPLETED
                self._log_activity(
                    "project_completed",
                    {
                        "total_tasks": total_tasks,
                        "completion_date": datetime.utcnow().isoformat(),
                    },
                )

    def is_member(self, user_id: str) -> bool:
        """Check if user is a project member"""
        return user_id == self.owner_id or user_id in self.team_members

    def _log_activity(self, action: str, data: Dict[str, Any]) -> None:
        """Log project activity"""
        entry = {
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }
        self.activity_log.append(entry)

    def __str__(self) -> str:
        return f"Project({self.id[:8]}): {self.name} [{self.status.value}]"
