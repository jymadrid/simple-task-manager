"""
User management and authentication
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Set
from uuid import uuid4
from pydantic import BaseModel, Field, EmailStr, ConfigDict
import bcrypt


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
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"
    TASK_ASSIGN = "task:assign"
    
    # Project permissions
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    PROJECT_MANAGE_MEMBERS = "project:manage_members"
    
    # User permissions
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIG = "system:config"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: list(Permission),
    UserRole.MANAGER: [
        Permission.TASK_CREATE, Permission.TASK_READ, Permission.TASK_UPDATE, 
        Permission.TASK_DELETE, Permission.TASK_ASSIGN,
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE, Permission.PROJECT_MANAGE_MEMBERS,
        Permission.USER_READ, Permission.USER_UPDATE,
    ],
    UserRole.DEVELOPER: [
        Permission.TASK_CREATE, Permission.TASK_READ, Permission.TASK_UPDATE,
        Permission.TASK_ASSIGN,
        Permission.PROJECT_READ, Permission.PROJECT_UPDATE,
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
    ]
}


class UserProfile(BaseModel):
    """Extended user profile information"""
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    theme: str = "default"
    notification_preferences: Dict[str, bool] = Field(default_factory=lambda: {
        "email_notifications": True,
        "push_notifications": True,
        "task_assignments": True,
        "project_updates": True,
        "due_date_reminders": True,
    })


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
    password_hash: str = Field(..., exclude=True)  # Exclude from serialization
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
        }
    )

    @classmethod
    def create_user(cls, username: str, email: str, password: str, 
                   full_name: Optional[str] = None, role: UserRole = UserRole.DEVELOPER) -> 'User':
        """Create a new user with hashed password"""
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        return cls(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role
        )

    def verify_password(self, password: str) -> bool:
        """Verify user password"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def update_password(self, new_password: str) -> None:
        """Update user password with new hash"""
        self.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
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
        self.last_login = datetime.utcnow()

    def join_team(self, project_id: str) -> None:
        """Add user to project team"""
        self.teams.add(project_id)
        self._log_activity("joined_team", {"project_id": project_id})

    def leave_team(self, project_id: str) -> None:
        """Remove user from project team"""
        self.teams.discard(project_id)
        self._log_activity("left_team", {"project_id": project_id})

    def _log_activity(self, action: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log user activity"""
        entry = {
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        self.activity_log.append(entry)

    def to_public_dict(self) -> Dict[str, Any]:
        """Return user data safe for public consumption (excludes sensitive fields)"""
        data = self.model_dump(exclude={'password_hash', 'activity_log'})
        return data

    def __str__(self) -> str:
        return f"User({self.username}) - {self.full_name or 'No name'}"