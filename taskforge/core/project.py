"""
Project management model
"""

import math
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
    member_roles: Dict[str, str] = Field(default_factory=dict)  # user_id -> role mapping

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

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure owner is in team_members
        if self.owner_id not in self.team_members:
            self.team_members.add(self.owner_id)

    def add_member(self, user_id: str, role: Optional[str] = None) -> None:
        """Add a team member to the project"""
        self.team_members.add(user_id)
        if role:
            self.member_roles[user_id] = role
        self._log_activity("member_added", {"user_id": user_id, "role": role})

    def remove_member(self, user_id: str) -> None:
        """Remove a team member from the project"""
        if user_id == self.owner_id:
            raise ValueError("Cannot remove project owner")
        self.team_members.discard(user_id)
        self.member_roles.pop(user_id, None)
        self._log_activity("member_removed", {"user_id": user_id})

    def is_member(self, user_id: str) -> bool:
        """Check if user is a project member"""
        return user_id == self.owner_id or user_id in self.team_members

    def update_status(self, new_status: ProjectStatus, user_id: Optional[str] = None) -> None:
        """Update project status"""
        old_status = self.status
        self.status = new_status
        self._log_activity("status_changed", {"old_status": old_status.value, "new_status": new_status.value, "user_id": user_id})

    def update_progress(self, progress: int, user_id: Optional[str] = None) -> None:
        """Update project progress manually"""
        old_progress = self.progress
        self.progress = max(0, min(100, progress))
        self._log_activity("progress_updated", {"old_progress": old_progress, "new_progress": self.progress, "user_id": user_id})

    def add_task_count(self, count: int) -> None:
        """Add to task count"""
        self.task_count += count

    def complete_task_count(self, count: int) -> None:
        """Add to completed task count"""
        self.completed_task_count += count

    def get_completion_rate(self) -> float:
        """Get task completion rate"""
        if self.task_count == 0:
            return 0.0
        return self.completed_task_count / self.task_count

    def add_actual_hours(self, hours: float) -> None:
        """Add actual hours worked"""
        self.actual_hours += hours

    def get_time_utilization(self) -> float:
        """Get time utilization rate"""
        if not self.estimated_hours or self.estimated_hours == 0:
            return 0.0
        return self.actual_hours / self.estimated_hours

    def get_duration_days(self) -> Optional[int]:
        """Get project duration in days"""
        if not self.start_date or not self.end_date:
            return None
        delta = self.end_date - self.start_date
        return delta.days

    def is_active_period(self) -> bool:
        """Check if project is within active date range"""
        now = datetime.utcnow()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    def add_tag(self, tag: str) -> None:
        """Add a tag to the project"""
        self.tags.add(tag.lower().strip())
        self._log_activity("tag_added", {"tag": tag})

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the project"""
        self.tags.discard(tag.lower().strip())
        self._log_activity("tag_removed", {"tag": tag})

    def update_setting(self, key: str, value: Any) -> None:
        """Update a project setting"""
        self.settings[key] = value

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a project setting"""
        return self.settings.get(key, default)

    def calculate_health_score(self) -> float:
        """Calculate project health score (0.0 to 1.0)"""
        score = 0.0
        factors = 0

        # Factor 1: Task completion rate
        if self.task_count > 0:
            completion_rate = self.completed_task_count / self.task_count
            score += completion_rate
            factors += 1

        # Factor 2: Time utilization (not over budget)
        if self.estimated_hours and self.estimated_hours > 0:
            time_util = self.actual_hours / self.estimated_hours
            # Penalize if over budget
            if time_util <= 1.0:
                score += time_util
            else:
                score += max(0, 2.0 - time_util)  # Penalty for going over
            factors += 1

        # Factor 3: Schedule adherence
        if self.start_date and self.end_date:
            now = datetime.utcnow()
            total_duration = (self.end_date - self.start_date).total_seconds()
            elapsed = (now - self.start_date).total_seconds()

            if total_duration > 0:
                time_progress = min(1.0, max(0.0, elapsed / total_duration))
                task_progress = self.progress / 100.0

                # Good if task progress >= time progress
                if task_progress >= time_progress:
                    score += 1.0
                else:
                    score += task_progress / max(time_progress, 0.01)
                factors += 1

        return score / factors if factors > 0 else 0.5

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary"""
        data = self.model_dump()
        # Convert sets to lists for JSON serialization
        if "tags" in data and isinstance(data["tags"], set):
            data["tags"] = list(data["tags"])
        if "team_members" in data and isinstance(data["team_members"], set):
            data["team_members"] = list(data["team_members"])
        return data

    def is_archived(self) -> bool:
        """Check if project is archived"""
        return self.status == ProjectStatus.ARCHIVED

    def archive(self, user_id: Optional[str] = None) -> None:
        """Archive the project"""
        self.status = ProjectStatus.ARCHIVED
        self._log_activity("archived", {"user_id": user_id})

    def unarchive(self, user_id: Optional[str] = None) -> None:
        """Unarchive the project"""
        self.status = ProjectStatus.ACTIVE
        self._log_activity("unarchived", {"user_id": user_id})

    def get_members_by_role(self, role: str) -> List[str]:
        """Get members with a specific role"""
        return [user_id for user_id, user_role in self.member_roles.items() if user_role == role]

    def days_until_deadline(self) -> Optional[int]:
        """Get days until project deadline"""
        if not self.end_date:
            return None
        now = datetime.utcnow()
        delta = self.end_date - now
        # Use ceiling to round up partial days
        return math.ceil(delta.total_seconds() / 86400)

    def is_deadline_approaching(self, days_threshold: int = 7) -> bool:
        """Check if deadline is approaching"""
        days = self.days_until_deadline()
        if days is None:
            return False
        return 0 < days <= days_threshold

    def is_overdue(self) -> bool:
        """Check if project is overdue"""
        if not self.end_date:
            return False
        return datetime.utcnow() > self.end_date and self.status not in [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED, ProjectStatus.ARCHIVED]

    def get_statistics(self) -> Dict[str, Any]:
        """Get project statistics"""
        status_str = self.status.value if isinstance(self.status, ProjectStatus) else self.status
        return {
            "task_count": self.task_count,
            "completed_task_count": self.completed_task_count,
            "completion_rate": self.get_completion_rate(),
            "team_size": len(self.team_members),  # Owner is already in team_members
            "time_utilization": self.get_time_utilization(),
            "progress": self.progress,
            "status": status_str,
            "days_until_deadline": self.days_until_deadline(),
            "is_overdue": self.is_overdue(),
        }

    def _log_activity(self, action: str, data: Dict[str, Any]) -> None:
        """Log project activity"""
        entry = {
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }
        self.activity_log.append(entry)

    def __str__(self) -> str:
        status_str = self.status.value if isinstance(self.status, ProjectStatus) else self.status
        return f"Project({self.id[:8]}): {self.name} [{status_str}]"

    def __repr__(self) -> str:
        status_str = self.status.value if isinstance(self.status, ProjectStatus) else self.status
        return f"<Project id={self.id[:8]} name='{self.name}' status={status_str}>"

    def __eq__(self, other: object) -> bool:
        """Compare projects by ID"""
        if not isinstance(other, Project):
            return False
        return self.id == other.id
