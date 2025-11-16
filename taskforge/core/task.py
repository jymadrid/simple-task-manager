"""
Core task model with advanced features
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(str, Enum):
    """Task status enumeration"""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TaskPriority(str, Enum):
    """Task priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class TaskType(str, Enum):
    """Task types for categorization"""

    FEATURE = "feature"
    BUG = "bug"
    IMPROVEMENT = "improvement"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    MAINTENANCE = "maintenance"
    MEETING = "meeting"
    OTHER = "other"


@dataclass
class TimeTracking:
    """Time tracking for tasks"""

    estimated_hours: Optional[float] = None
    actual_hours: float = 0.0
    time_entries: List[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.time_entries is None:
            self.time_entries = []


class TaskRecurrence(BaseModel):
    """Recurrence pattern for recurring tasks"""

    pattern: str = Field(..., description="Cron-like pattern")
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = None
    created_count: int = 0


class TaskDependency(BaseModel):
    """Task dependency relationship"""

    task_id: str
    dependency_type: str = "blocks"  # blocks, subtask, related
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Task(BaseModel):
    """
    Advanced task model with comprehensive features

    This model supports:
    - Rich metadata and categorization
    - Time tracking and estimates
    - Dependencies and subtasks
    - Recurring tasks
    - Custom fields and tags
    - Activity history
    """

    # Core fields
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)

    # Status and priority
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    task_type: TaskType = TaskType.OTHER

    # Ownership and assignment
    created_by: Optional[str] = None
    assigned_to: Optional[str] = None
    project_id: Optional[str] = None

    # Temporal fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Categorization
    tags: Set[str] = Field(default_factory=set)
    labels: List[str] = Field(default_factory=list)
    category: Optional[str] = None

    # Advanced features
    dependencies: List[TaskDependency] = Field(default_factory=list)
    subtasks: List[str] = Field(default_factory=list)  # Task IDs
    parent_task: Optional[str] = None

    # Time tracking
    time_tracking: TimeTracking = Field(default_factory=TimeTracking)

    # Recurrence
    recurrence: Optional[TaskRecurrence] = None

    # Custom fields
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    # Activity and history
    activity_log: List[Dict[str, Any]] = Field(default_factory=list)

    # Progress tracking
    progress: int = Field(0, ge=0, le=100)
    completion_criteria: List[str] = Field(default_factory=list)

    # External integration
    external_links: Dict[str, str] = Field(default_factory=dict)
    integration_data: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            set: list,
        },
    )

    @field_validator("updated_at", mode="before")
    @classmethod
    def set_updated_at(cls, v: Optional[datetime]) -> datetime:
        return datetime.now(timezone.utc)

    @field_validator("progress")
    @classmethod
    def validate_progress(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError("Progress must be between 0 and 100")
        return v

    def add_tag(self, tag: str) -> None:
        """Add a tag to the task"""
        self.tags.add(tag.lower().strip())
        self._log_activity("tag_added", {"tag": tag})

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the task"""
        self.tags.discard(tag.lower().strip())
        self._log_activity("tag_removed", {"tag": tag})

    def add_dependency(self, task_id: str, dependency_type: str = "blocks") -> None:
        """Add a task dependency"""
        dependency = TaskDependency(task_id=task_id, dependency_type=dependency_type)
        self.dependencies.append(dependency)
        self._log_activity(
            "dependency_added", {"task_id": task_id, "type": dependency_type}
        )

    def remove_dependency(self, task_id: str) -> None:
        """Remove a task dependency"""
        self.dependencies = [d for d in self.dependencies if d.task_id != task_id]
        self._log_activity("dependency_removed", {"task_id": task_id})

    def update_status(
        self, new_status: TaskStatus, user_id: Optional[str] = None
    ) -> None:
        """Update task status with activity logging"""
        old_status = self.status
        self.status = new_status

        if new_status == TaskStatus.DONE:
            self.completed_at = datetime.now(timezone.utc)
            self.progress = 100
        elif old_status == TaskStatus.DONE:
            self.completed_at = None

        self._log_activity(
            "status_changed",
            {
                "old_status": old_status.value,
                "new_status": new_status.value,
                "user_id": user_id,
            },
        )

    def update_progress(self, progress: int, user_id: Optional[str] = None) -> None:
        """Update task progress"""
        old_progress = self.progress
        self.progress = max(0, min(100, progress))

        if self.progress == 100 and self.status != TaskStatus.DONE:
            self.update_status(TaskStatus.DONE, user_id)
        elif self.progress < 100 and self.status == TaskStatus.DONE:
            self.update_status(TaskStatus.IN_PROGRESS, user_id)

        self._log_activity(
            "progress_updated",
            {
                "old_progress": old_progress,
                "new_progress": self.progress,
                "user_id": user_id,
            },
        )

    def add_time_entry(
        self, hours: float, description: str = "", user_id: Optional[str] = None
    ) -> None:
        """Add time tracking entry"""
        entry = {
            "hours": hours,
            "description": description,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.time_tracking.time_entries.append(entry)
        self.time_tracking.actual_hours += hours
        self._log_activity("time_logged", {"hours": hours, "user_id": user_id})

    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if not self.due_date or self.status in [TaskStatus.DONE, TaskStatus.CANCELLED]:
            return False
        return datetime.now(timezone.utc) > self.due_date

    def days_until_due(self) -> Optional[int]:
        """Get days until due date"""
        if not self.due_date:
            return None
        delta = self.due_date - datetime.utcnow()
        return delta.days

    def get_blocked_dependencies(self) -> List[str]:
        """Get list of tasks that are blocking this task"""
        return [d.task_id for d in self.dependencies if d.dependency_type == "blocks"]

    def _log_activity(self, action: str, data: Dict[str, Any]) -> None:
        """Log activity for audit trail"""
        entry = {
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        self.activity_log.append(entry)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return self.model_dump()

    def __str__(self) -> str:
        return f"Task({self.id[:8]}): {self.title} [{self.status.value}]"

    def __repr__(self) -> str:
        return (
            f"<Task id={self.id[:8]} title='{self.title}' status={self.status.value}>"
        )
