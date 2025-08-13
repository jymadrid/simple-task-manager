from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from taskforge.api.schemas import ProjectCreate, ProjectUpdate, ProjectPublic
from taskforge.core.project import Project
from taskforge.core.user import User
from taskforge.core.manager import TaskManager
# This dependency will be created in the next steps
from taskforge.api.dependencies import get_task_manager, get_current_user

router = APIRouter()

@router.post("/", response_model=ProjectPublic, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    manager: TaskManager = Depends(get_task_manager),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new project. The current user will be set as the owner.
    """
    project = Project(
        name=project_in.name,
        description=project_in.description,
        owner_id=current_user.id,
    )
    # The manager needs a create_project method that handles permissions.
    # For now, we assume it exists and works.
    created_project = await manager.create_project(project, current_user.id)
    return created_project

@router.get("/", response_model=List[ProjectPublic])
async def list_user_projects(
    manager: TaskManager = Depends(get_task_manager),
    current_user: User = Depends(get_current_user),
):
    """
    List all projects for the current user (where they are an owner or member).
    """
    projects = await manager.storage.get_user_projects(current_user.id)
    return projects

@router.get("/{project_id}", response_model=ProjectPublic)
async def get_project(
    project_id: str,
    manager: TaskManager = Depends(get_task_manager),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific project by its ID.
    """
    project = await manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.is_member(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
        
    return project

@router.patch("/{project_id}", response_model=ProjectPublic)
async def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    manager: TaskManager = Depends(get_task_manager),
    current_user: User = Depends(get_current_user),
):
    """
    Update a project's details.
    """
    project = await manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the project owner can update it")

    update_data = project_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    updated_project = await manager.storage.update_project(project)
    return updated_project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    manager: TaskManager = Depends(get_task_manager),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a project.
    """
    project = await manager.get_project(project_id)
    if project and project.owner_id == current_user.id:
        await manager.storage.delete_project(project_id)
    elif project:
        raise HTTPException(status_code=403, detail="Only the project owner can delete it")
    
    return
