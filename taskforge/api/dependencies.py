import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from taskforge.core.manager import TaskManager
from taskforge.core.user import User
from taskforge.storage.json_storage import JSONStorage

# A temporary, simple dependency injector.
# In a real application, you might use a more robust system.
storage = JSONStorage()
task_manager = TaskManager(storage=storage)
_storage_initialized = False


async def get_storage() -> JSONStorage:
    """Initialize and return storage instance (demo usage)."""
    global _storage_initialized
    if not _storage_initialized:
        await storage.initialize()
        _storage_initialized = True
    return storage


async def get_task_manager() -> TaskManager:
    await get_storage()
    return task_manager


# This is a placeholder for a real authentication system.
# It currently fakes a user for development purposes.
async def get_current_user() -> User:
    """
    A temporary dependency to get a 'current' user.
    In a real application, this would involve token verification.
    """
    if os.getenv("TASKFORGE_DEMO_AUTH", "true").lower() != "true":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Demo authentication is disabled",
        )
    await get_storage()
    # Check if a default user exists, if not, create one.
    user = await storage.get_user_by_username("testuser")
    if not user:
        user = User.create_user(
            username="testuser", email="test@example.com", password="password"
        )
        user.id = "user-test-01"  # predictable ID
        await storage.create_user(user)
    return user
