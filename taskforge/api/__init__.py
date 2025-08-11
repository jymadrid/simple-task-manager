"""
FastAPI-based REST API
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from taskforge.core.manager import TaskManager, TaskQuery
from taskforge.core.task import Task, TaskStatus, TaskPriority, TaskType
from taskforge.core.project import Project, ProjectStatus
from taskforge.core.user import User, UserRole
from taskforge.storage.json_storage import JsonStorage
from taskforge.utils.auth import AuthManager
from taskforge.utils.config import Config

# Pydantic models for API
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    task_type: TaskType = TaskType.OTHER
    due_date: Optional[datetime] = None
    project_id: Optional[str] = None
    tags: List[str] = []
    assigned_to: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    progress: Optional[int] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.DEVELOPER

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# Initialize FastAPI app
app = FastAPI(
    title="TaskForge API",
    description="A comprehensive task management platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
manager: Optional[TaskManager] = None
auth_manager: Optional[AuthManager] = None
security = HTTPBearer()

def get_manager() -> TaskManager:
    """Get or create task manager instance"""
    global manager
    if manager is None:
        config = Config.load()
        storage = JsonStorage(config.data_directory)
        manager = TaskManager(storage)
    return manager

def get_auth_manager() -> AuthManager:
    """Get or create auth manager instance"""
    global auth_manager
    if auth_manager is None:
        auth_manager = AuthManager()
    return auth_manager

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    auth_mgr = get_auth_manager()
    user_id = await auth_mgr.verify_token_async(credentials.credentials)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    mgr = get_manager()
    user = await mgr.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Authentication endpoints
@app.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    mgr = get_manager()
    auth_mgr = get_auth_manager()
    
    try:
        # Create user
        user = User.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role
        )
        
        # Save user (assuming storage supports it)
        created_user = await mgr.storage.create_user(user)
        
        # Generate token
        token = await auth_mgr.create_token(created_user.id)
        
        return TokenResponse(
            access_token=token,
            expires_in=3600  # 1 hour
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/auth/login", response_model=TokenResponse)
async def login(username: str, password: str):
    """Authenticate user and return token"""
    mgr = get_manager()
    auth_mgr = get_auth_manager()
    
    # Find user by username
    user = await mgr.storage.get_user_by_username(username)
    if not user or not user.verify_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Update last login
    user.update_last_login()
    await mgr.storage.update_user(user)
    
    # Generate token
    token = await auth_mgr.create_token(user.id)
    
    return TokenResponse(
        access_token=token,
        expires_in=3600
    )

# Task endpoints
@app.post("/tasks", response_model=Task)
async def create_task(task_data: TaskCreate, current_user: User = Depends(get_current_user)):
    """Create a new task"""
    mgr = get_manager()
    
    task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        task_type=task_data.task_type,
        due_date=task_data.due_date,
        project_id=task_data.project_id,
        tags=set(task_data.tags),
        assigned_to=task_data.assigned_to or current_user.id
    )
    
    try:
        created_task = await mgr.create_task(task, current_user.id)
        return created_task
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/tasks", response_model=List[Task])
async def list_tasks(
    status: Optional[List[TaskStatus]] = Query(None),
    priority: Optional[List[TaskPriority]] = Query(None),
    project_id: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """List tasks with filtering options"""
    mgr = get_manager()
    
    query = TaskQuery(
        status=status,
        priority=priority,
        project_id=project_id,
        assigned_to=assigned_to,
        search_text=search,
        limit=limit,
        offset=offset
    )
    
    try:
        tasks = await mgr.search_tasks(query, current_user.id)
        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific task"""
    mgr = get_manager()
    
    task = await mgr.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task

@app.patch("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: str, 
    task_update: TaskUpdate, 
    current_user: User = Depends(get_current_user)
):
    """Update a task"""
    mgr = get_manager()
    
    # Convert to dict, excluding None values
    updates = task_update.dict(exclude_unset=True)
    
    # Convert tags list to set if provided
    if 'tags' in updates:
        updates['tags'] = set(updates['tags'])
    
    try:
        updated_task = await mgr.update_task(task_id, updates, current_user.id)
        return updated_task
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str, current_user: User = Depends(get_current_user)):
    """Delete a task"""
    mgr = get_manager()
    
    try:
        success = await mgr.delete_task(task_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        return {"message": "Task deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Project endpoints
@app.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate, current_user: User = Depends(get_current_user)):
    """Create a new project"""
    mgr = get_manager()
    
    project = Project(
        name=project_data.name,
        description=project_data.description,
        start_date=project_data.start_date,
        end_date=project_data.end_date,
        owner_id=current_user.id
    )
    
    try:
        created_project = await mgr.create_project(project, current_user.id)
        return created_project
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/projects", response_model=List[Project])
async def list_projects(current_user: User = Depends(get_current_user)):
    """List user's projects"""
    mgr = get_manager()
    
    try:
        # Get projects where user is owner or member
        projects = await mgr.storage.get_user_projects(current_user.id)
        return projects
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific project"""
    mgr = get_manager()
    
    project = await mgr.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has access
    if not project.is_member(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return project

# Statistics endpoints
@app.get("/stats/tasks")
async def get_task_statistics(
    project_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get task statistics"""
    mgr = get_manager()
    
    try:
        stats = await mgr.get_task_statistics(project_id, current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/stats/productivity")
async def get_productivity_metrics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user)
):
    """Get user productivity metrics"""
    mgr = get_manager()
    
    try:
        metrics = await mgr.get_productivity_metrics(current_user.id, days)
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Dashboard endpoint
@app.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user)):
    """Get dashboard data"""
    mgr = get_manager()
    
    try:
        # Get various dashboard data
        overdue_tasks = await mgr.get_overdue_tasks(current_user.id)
        upcoming_tasks = await mgr.get_upcoming_tasks(7, current_user.id)
        stats = await mgr.get_task_statistics(user_id=current_user.id)
        productivity = await mgr.get_productivity_metrics(current_user.id, 30)
        
        return {
            "user": current_user.to_public_dict(),
            "overdue_tasks": len(overdue_tasks),
            "upcoming_tasks": len(upcoming_tasks),
            "statistics": stats,
            "productivity": productivity,
            "recent_overdue": [task.dict() for task in overdue_tasks[:5]],
            "recent_upcoming": [task.dict() for task in upcoming_tasks[:5]]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# WebSocket endpoint for real-time updates (placeholder)
@app.websocket("/ws")
async def websocket_endpoint(websocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Handle real-time updates here
            await websocket.send_text(f"Echo: {data}")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(PermissionError)
async def permission_error_handler(request, exc):
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc)}
    )

def create_app() -> FastAPI:
    """Factory function to create FastAPI app"""
    return app

def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Run the API server"""
    uvicorn.run(
        "taskforge.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    run_server(reload=True)