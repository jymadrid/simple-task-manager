from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from taskforge.core.manager import TaskManager
from taskforge.core.user import User
from taskforge.storage.json_storage import JSONStorage

# A temporary, simple dependency injector.
# In a real application, you might use a more robust system.
storage = JSONStorage()
task_manager = TaskManager(storage=storage)


async def get_task_manager() -> TaskManager:
    return task_manager


# This is a placeholder for a real authentication system.
# It currently fakes a user for development purposes.
async def get_current_user() -> User:
    """
    A temporary dependency to get a 'current' user.
    In a real application, this would involve token verification.
    """
    # Check if a default user exists, if not, create one.
    user = await storage.get_user_by_username("testuser")
    if not user:
        user = User.create_user(
            username="testuser", email="test@example.com", password="password"
        )
        user.id = "user-test-01"  # predictable ID
        await storage.create_user(user)
    return user
