"""
Authentication and authorization utilities
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, cast

import jwt
from passlib.context import CryptContext  # type: ignore[import-untyped]

from taskforge.core.user import User
from taskforge.utils.config import Config
from taskforge.utils.values import enum_value


class AuthManager:
    """Authentication and authorization manager"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.load()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = self.config.security.secret_key
        self.algorithm = self.config.security.algorithm
        self.access_token_expire_minutes = (
            self.config.security.access_token_expire_minutes
        )

    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return cast(str, self.pwd_context.hash(password))

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return cast(bool, self.pwd_context.verify(plain_password, hashed_password))

    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if isinstance(payload, dict):
                return cast(Dict[str, Any], payload)
            return None
        except jwt.PyJWTError:
            return None

    async def create_token(self, user_id: str) -> str:
        """Create token for user"""
        token_data = {"sub": user_id}
        return self.create_access_token(token_data)

    async def verify_token_async(self, token: str) -> Optional[str]:
        """Verify token and return user ID"""
        payload = self.verify_token(token)
        if payload:
            subject = payload.get("sub")
            return subject if isinstance(subject, str) else None
        return None

    def authenticate_user(self, user: User, password: str) -> bool:
        """Authenticate a user with password"""
        if not user or not user.is_active:
            return False
        return self.verify_password(password, user.password_hash)

    def can_access_resource(self, user: User, resource_type: str, action: str) -> bool:
        """Check if user can access a resource"""
        # Simple role-based access control
        permission_map = {
            "admin": ["create", "read", "update", "delete"],
            "manager": ["create", "read", "update"],
            "developer": ["create", "read", "update"],
            "viewer": ["read"],
            "guest": ["read"],
        }

        allowed_actions = permission_map.get(enum_value(user.role), [])
        return action in allowed_actions
