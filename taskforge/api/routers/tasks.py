from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List

from taskforge.api.schemas import TaskCreate, TaskUpdate, TaskPublic
from taskforge.core.task import Task
from taskforge.core.user import User
from taskforge.core.manager import TaskManager, TaskQuery
from taskforge.api.dependencies import get_task_manager, get_current_user

router = APIRouter()

@router.post("/", response_model=TaskPublic, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    manager: TaskManager = Depends(get_task_manager),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new task within a project.
    """
    project = await manager.get_project(task_in.project_id)
    if not project or not project.is_member(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to add tasks to this project")

    task = Task(
        title=task_in.title,
        description=task_in.description,
        project_id=task_in.project_id,
        priority=task_in.priority,
        due_date=task_in.due_date,
        tags=task_in.tags,
        created_by=current_user.id,
        assigned_to=current_user.id # Default assignment
    )
    created_task = await manager.create_task(task, current_user.id)
    return created_task

@router.get("/", response_model=List[TaskPublic])
async def list_tasks_in_project(
    project_id: str,
    manager: TaskManager = Depends(get_task_manager),
    current_user: User = Depends(get_current_user),
):
    """
    List all tasks for a specific project.
    """
    project = await manager.get_project(project_id)
    if not project or not project.is_member(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view tasks in this project")
        
    query = TaskQuery(project_id=project_id)
    tasks = await manager.search_tasks(query, current_user.id)
    return tasks

@router.get("/{task_id}", response_model=TaskPublic)
async def get_task(
    task_id: str,
    manager: TaskManager = Depends(get_task_manager),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific task by its ID.
    """
    task = await manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    project = await manager.get_project(task.project_id)
    if not project or not project.is_member(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
        
    return task

@router.patch("/{task_id}", response_model=TaskPublic)
async def update_task(
    task_id: str,
    task_in: TaskUpdate,
    manager: TaskManager = Depends(get_task_manager),
    current_user: User = Depends(get_current_user),
):
    """
    Update a task's details.
    """
    task = await manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    project = await manager.get_project(task.project_id)
    if not project or not project.is_member(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to update this task")
        
    update_data = task_in.dict(exclude_unset=True)
    updated_task = await manager.update_task(task_id, update_data, current_user.id)
    return updated_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    manager: TaskManager = Depends(get_task_manager),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a task.
    """
    task = await manager.get_task(task_id)
    if not task:
        return # Idempotent delete

    project = await manager.get_project(task.project_id)
    if not project or not project.is_member(current_user.id):
         raise HTTPException(status_code=403, detail="Not authorized to delete this task")

    await manager.delete_task(task_id, current_user.id)
    return
