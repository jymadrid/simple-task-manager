from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from taskforge.api.routers import projects, tasks, users

from .dependencies import get_storage, storage  # noqa: F401
from .websockets import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared resources during application startup."""
    await get_storage()
    yield


app = FastAPI(
    title="TaskForge API",
    description="A flexible and powerful API for task management.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "taskforge-api"}


@app.get("/", tags=["Health"])
async def read_root():
    """A simple health check endpoint."""
    return {"status": "ok"}


# Include routers
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])


@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Example of how to integrate broadcasting:
# In your task creation/update/delete endpoints, you would add:
# await manager.broadcast(f"Task updated: {task.title}")
# This part requires modifying existing routers, which is a more complex task.
# For now, this sets up the infrastructure.
