"""
User management and authentication
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import bcrypt
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    """User roles with different permission levels"""

    ADMIN = "admin"
    MANAGER = "manager"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    GUEST = "guest"


class Permission(str, Enum):
    """Granular permissions"""

    # Task permissions
    TASK_CREATE = "task:create"
    CREATE_TASK = "task:create"  # Alias
    TASK_READ = "task:read"
    READ_TASK = "task:read"  # Alias
    TASK_UPDATE = "task:update"
    UPDATE_TASK = "task:update"  # Alias
    TASK_DELETE = "task:delete"
    DELETE_TASK = "task:delete"  # Alias
    TASK_ASSIGN = "task:assign"

    # Project permissions
    PROJECT_CREATE = "project:create"
    CREATE_PROJECT = "project:create"  # Alias
    PROJECT_READ = "project:read"
    READ_PROJECT = "project:read"  # Alias
    PROJECT_UPDATE = "project:update"
    UPDATE_PROJECT = "project:update"  # Alias
    PROJECT_DELETE = "project:delete"
    DELETE_PROJECT = "project:delete"  # Alias
    PROJECT_MANAGE_MEMBERS = "project:manage_members"

    # User permissions
    USER_CREATE = "user:create"
    CREATE_USER = "user:create"  # Alias
    USER_READ = "user:read"
    READ_USER = "user:read"  # Alias
    USER_UPDATE = "user:update"
    UPDATE_USER = "user:update"  # Alias
    USER_DELETE = "user:delete"
    DELETE_USER = "user:delete"  # Alias

    # System permissions
    SYSTEM_ADMIN = "system:admin"
    MANAGE_SYSTEM = "system:admin"  # Alias
    SYSTEM_CONFIG = "system:config"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: list(Permission),
    UserRole.MANAGER: [
        Permission.TASK_CREATE,
        Permission.TASK_READ,
        Permission.TASK_UPDATE,
        Permission.TASK_DELETE,
        Permission.TASK_ASSIGN,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,
        Permission.PROJECT_MANAGE_MEMBERS,
        Permission.USER_READ,
        Permission.USER_UPDATE,
    ],
    UserRole.DEVELOPER: [
        Permission.TASK_CREATE,
        Permission.TASK_READ,
        Permission.TASK_UPDATE,
        Permission.TASK_ASSIGN,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_READ,
        Permission.PROJECT_UPDATE,
        Permission.USER_READ,
    ],
    UserRole.VIEWER: [
        Permission.TASK_READ,
        Permission.PROJECT_READ,
        Permission.USER_READ,
    ],
    UserRole.GUEST: [
        Permission.TASK_READ,
        Permission.PROJECT_READ,
    ],
}


class UserProfile(BaseModel):
    """Extended user profile information"""

    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    theme: str = "default"
    social_links: Dict[str, str] = Field(default_factory=dict)
    notification_preferences: Dict[str, bool] = Field(
        default_factory=lambda: {
            "email_notifications": True,
            "push_notifications": True,
            "task_assignments": True,
            "project_updates": True,
            "due_date_reminders": True,
        }
    )

    def __init__(self, **data):
        # Extract social link fields
        social_fields = ["github", "twitter", "linkedin", "facebook"]
        social_links = {}
        for field in social_fields:
            if field in data:
                social_links[field] = data.pop(field)

        if "social_links" not in data:
            data["social_links"] = social_links
        else:
            data["social_links"].update(social_links)

        super().__init__(**data)

    def get_avatar_url(self, email: Optional[str] = None) -> str:
        """Get avatar URL, fallback to gravatar"""
        if self.avatar_url:
            return self.avatar_url

        if email:
            import hashlib

            email_hash = hashlib.md5(email.lower().encode(), usedforsecurity=False).hexdigest()
            return f"https://www.gravatar.com/avatar/{email_hash}?d=identicon"

        return "https://www.gravatar.com/avatar/?d=mp"


class User(BaseModel):
    """
    User model for authentication and authorization

    Supports role-based access control, profile management,
    and activity tracking.
    """

    # Core fields
    id: str = Field(default_factory=lambda: str(uuid4()))
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)

    # Authentication
    password_hash: str = Field(default="", exclude=True)  # Exclude from serialization
    is_active: bool = True
    is_verified: bool = False

    # Authorization
    role: UserRole = UserRole.DEVELOPER
    custom_permissions: Set[Permission] = Field(default_factory=set)

    # Profile
    profile: UserProfile = Field(default_factory=UserProfile)

    # Temporal fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    # Organization
    teams: Set[str] = Field(default_factory=set)  # Project IDs user is member of

    # Activity and preferences
    activity_log: List[Dict[str, Any]] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            set: list,
        },
    )

    @classmethod
    def create_user(
        cls,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.DEVELOPER,
    ) -> "User":
        """Create a new user with hashed password"""
        # Validate username length
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")

        # Validate password strength (minimum 4 characters)
        if len(password) < 4:
            raise ValueError("Password must be at least 4 characters long")

        # Validate email format (Pydantic will also validate)
        if "@" not in email or "." not in email:
            raise ValueError("Invalid email format")

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        return cls(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
        )

    def verify_password(self, password: str) -> bool:
        """Verify user password"""
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def update_password(self, new_password: str) -> None:
        """Update user password with new hash"""
        self.password_hash = bcrypt.hashpw(
            new_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        self._log_activity("password_updated")

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        if not self.is_active:
            return False

        # Check custom permissions first
        if permission in self.custom_permissions:
            return True

        # Check role-based permissions
        role_perms = ROLE_PERMISSIONS.get(self.role, [])
        return permission in role_perms

    def grant_permission(self, permission: Permission) -> None:
        """Grant additional permission to user"""
        self.custom_permissions.add(permission)
        self._log_activity("permission_granted", {"permission": permission.value})

    def revoke_permission(self, permission: Permission) -> None:
        """Revoke permission from user"""
        self.custom_permissions.discard(permission)
        self._log_activity("permission_revoked", {"permission": permission.value})

    def update_last_login(self) -> None:
        """Update last login timestamp"""
        self.last_login = datetime.now(timezone.utc)

    def join_team(self, project_id: str) -> None:
        """Add user to project team"""
        self.teams.add(project_id)
        self._log_activity("joined_team", {"project_id": project_id})

    def leave_team(self, project_id: str) -> None:
        """Remove user from project team"""
        self.teams.discard(project_id)
        self._log_activity("left_team", {"project_id": project_id})

    def add_permission(self, permission: Permission) -> None:
        """Add a custom permission (alias for grant_permission)"""
        self.grant_permission(permission)

    def remove_permission(self, permission: Permission) -> None:
        """Remove a custom permission (alias for revoke_permission)"""
        self.revoke_permission(permission)

    def log_activity(self, action: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Public method to log user activity"""
        self._log_activity(action, data)

    def deactivate(self) -> None:
        """Deactivate user account"""
        self.is_active = False
        self._log_activity("deactivated")

    def activate(self) -> None:
        """Activate user account"""
        self.is_active = True
        self._log_activity("activated")

    def update_setting(self, key: str, value: Any) -> None:
        """Update a user setting"""
        self.settings[key] = value

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a user setting"""
        return self.settings.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Return full user data as dictionary"""
        # Get all fields including password_hash
        data = self.model_dump(mode="python")
        # Manually add password_hash since it's excluded by default
        data["password_hash"] = self.password_hash
        return data

    def _log_activity(self, action: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log user activity"""
        entry = {
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {},
        }
        self.activity_log.append(entry)

    def to_public_dict(self) -> Dict[str, Any]:
        """Return user data safe for public consumption (excludes sensitive fields)"""
        data = self.model_dump(exclude={"password_hash", "activity_log", "email"})
        return data

    def __str__(self) -> str:
        return f"User({self.username}) - {self.full_name or 'No name'}"

    def __repr__(self) -> str:
        return f"<User id={self.id[:8]} username='{self.username}'>"

    def __eq__(self, other: object) -> bool:
        """Compare users by ID"""
        if not isinstance(other, User):
            return False
        return self.id == other.id
