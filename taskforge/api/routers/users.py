from fastapi import APIRouter, Depends, HTTPException
from typing import List
from taskforge.api.schemas import UserCreate, UserPublic
from taskforge.core.user import User
from taskforge.core.manager import TaskManager
from taskforge.api.dependencies import get_task_manager

router = APIRouter()

@router.post("/", response_model=UserPublic, status_code=201)
async def create_user(
    user_in: UserCreate,
    manager: TaskManager = Depends(get_task_manager),
):
    """
    Create a new user.
    """
    # This is a simplified user creation. A real application would handle
    # password hashing and other security concerns more robustly.
    try:
        user = User.create_user(
            username=user_in.username,
            email=user_in.email,
            password=user_in.password,
            full_name=user_in.full_name,
        )
        created_user = await manager.storage.create_user(user)
        return created_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}", response_model=UserPublic)
async def read_user(
    user_id: str,
    manager: TaskManager = Depends(get_task_manager),
):
    """
    Get a specific user by ID.
    """
    user = await manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
