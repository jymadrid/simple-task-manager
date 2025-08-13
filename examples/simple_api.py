#!/usr/bin/env python3
"""
Simple REST API Example for TaskForge

This example demonstrates how to build a REST API using TaskForge as a backend library.
It provides a complete CRUD API for tasks with proper error handling and documentation.

Usage:
    python examples/simple_api.py

Then visit:
    http://localhost:8000/docs - Interactive API documentation
    http://localhost:8000/redoc - Alternative API documentation

API Endpoints:
    GET /tasks - List all tasks
    POST /tasks - Create a new task
    GET /tasks/{task_id} - Get a specific task
    PUT /tasks/{task_id} - Update a task
    DELETE /tasks/{task_id} - Delete a task
    GET /stats - Get task statistics
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add the parent directory to the path so we can import taskforge
sys.path.insert(0, str(Path(__file__).parent.parent))

from taskforge.core.queries import TaskQuery
from taskforge.core.task import Task, TaskPriority, TaskStatus
from taskforge.core.user import User
from taskforge.storage.json_storage import JSONStorage


# Pydantic models for API
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: Optional[datetime]
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    progress: int

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    overdue_tasks: int
    completion_rate: float
    priority_distribution: dict
    status_distribution: dict


# Initialize FastAPI app
app = FastAPI(
    title="TaskForge Simple API",
    description="A simple REST API built with TaskForge library for task management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage instance
storage: Optional[JSONStorage] = None
current_user_id = "api-user"


async def get_storage() -> JSONStorage:
    """Get or create storage instance"""
    global storage
    if storage is None:
        storage = JSONStorage("./data")
        await storage.initialize()

        # Create default user if needed
        user = await storage.get_user(current_user_id)
        if not user:
            default_user = User.create_user(
                username="apiuser",
                email="api@example.com",
                password="password",
                full_name="API User",
            )
            default_user.id = current_user_id
            await storage.create_user(default_user)

    return storage


@app.on_event("startup")
async def startup_event():
    """Initialize storage on startup"""
    await get_storage()


@app.get("/", tags=["Root"])
async def root():
    """Welcome message and API information"""
    return {
        "message": "Welcome to TaskForge Simple API!",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {"tasks": "/tasks", "statistics": "/stats"},
    }


@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"])
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    priority: Optional[TaskPriority] = Query(
        None, description="Filter by task priority"
    ),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of tasks to return"
    ),
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
):
    """
    Get a list of all tasks with optional filtering.

    - **status**: Filter tasks by status (todo, in_progress, done, etc.)
    - **priority**: Filter tasks by priority (low, medium, high, critical)
    - **limit**: Maximum number of tasks to return (1-1000)
    - **offset**: Number of tasks to skip for pagination
    """
    storage = await get_storage()

    query = TaskQuery(
        status=[status] if status else None,
        priority=[priority] if priority else None,
        limit=limit,
        offset=offset,
    )

    tasks = await storage.search_tasks(query, current_user_id)
    return [TaskResponse.from_orm(task) for task in tasks]


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
)
async def create_task(task_data: TaskCreate):
    """
    Create a new task.

    - **title**: Task title (required)
    - **description**: Task description (optional)
    - **priority**: Task priority (low, medium, high, critical)
    - **due_date**: Due date for the task (optional)
    """
    storage = await get_storage()

    task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        due_date=task_data.due_date,
        created_by=current_user_id,
        assigned_to=current_user_id,
    )

    created_task = await storage.create_task(task)
    return TaskResponse.from_orm(created_task)


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def get_task(task_id: str):
    """
    Get a specific task by ID.

    - **task_id**: The unique identifier of the task
    """
    storage = await get_storage()

    task = await storage.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )

    return TaskResponse.from_orm(task)


@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def update_task(task_id: str, task_data: TaskUpdate):
    """
    Update a specific task.

    - **task_id**: The unique identifier of the task
    - **title**: New task title (optional)
    - **description**: New task description (optional)
    - **priority**: New task priority (optional)
    - **status**: New task status (optional)
    - **due_date**: New due date (optional)
    """
    storage = await get_storage()

    task = await storage.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )

    # Update fields if provided
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.priority is not None:
        task.priority = task_data.priority
    if task_data.status is not None:
        task.update_status(task_data.status, current_user_id)
    if task_data.due_date is not None:
        task.due_date = task_data.due_date

    updated_task = await storage.update_task(task)
    return TaskResponse.from_orm(updated_task)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tasks"])
async def delete_task(task_id: str):
    """
    Delete a specific task.

    - **task_id**: The unique identifier of the task to delete
    """
    storage = await get_storage()

    task = await storage.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )

    deleted = await storage.delete_task(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task",
        )


@app.post("/tasks/{task_id}/complete", response_model=TaskResponse, tags=["Tasks"])
async def complete_task(task_id: str):
    """
    Mark a task as completed.

    - **task_id**: The unique identifier of the task to complete
    """
    storage = await get_storage()

    task = await storage.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )

    if task.status == TaskStatus.DONE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Task is already completed"
        )

    task.update_status(TaskStatus.DONE, current_user_id)
    updated_task = await storage.update_task(task)
    return TaskResponse.from_orm(updated_task)


@app.get("/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_statistics():
    """
    Get task statistics including counts, completion rates, and distributions.
    """
    storage = await get_storage()

    stats = await storage.get_task_statistics(user_id=current_user_id)
    return StatsResponse(**stats)


@app.post("/demo", tags=["Demo"])
async def create_demo_data():
    """
    Create demo tasks for testing the API.
    """
    storage = await get_storage()

    demo_tasks = [
        TaskCreate(
            title="Fix authentication bug",
            description="Users can't log in with special characters in password",
            priority=TaskPriority.HIGH,
        ),
        TaskCreate(
            title="Update API documentation",
            description="Add examples for all new endpoints",
            priority=TaskPriority.MEDIUM,
        ),
        TaskCreate(
            title="Implement rate limiting",
            description="Add rate limiting to prevent API abuse",
            priority=TaskPriority.HIGH,
        ),
        TaskCreate(
            title="Add user avatars",
            description="Allow users to upload profile pictures",
            priority=TaskPriority.LOW,
        ),
        TaskCreate(
            title="Write integration tests",
            description="Add comprehensive API integration tests",
            priority=TaskPriority.MEDIUM,
        ),
    ]

    created_tasks = []
    for task_data in demo_tasks:
        task = Task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            created_by=current_user_id,
            assigned_to=current_user_id,
        )
        created_task = await storage.create_task(task)
        created_tasks.append(TaskResponse.from_orm(created_task))

    return {
        "message": f"Created {len(created_tasks)} demo tasks",
        "tasks": created_tasks,
    }


if __name__ == "__main__":
    print("🚀 Starting TaskForge Simple API...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("📚 Alternative Docs: http://localhost:8000/redoc")
    print("🔗 API Root: http://localhost:8000/")

    uvicorn.run(
        "simple_api:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
