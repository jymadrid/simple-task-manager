from fastapi import FastAPI

from taskforge.api.routers import projects, tasks, users

from .dependencies import storage  # Import storage to initialize it

app = FastAPI(
    title="TaskForge API",
    description="A flexible and powerful API for task management.",
    version="0.1.0",
)


@app.on_event("startup")
async def startup_event():
    """Initialize the database on startup."""
    await storage.initialize()


@app.get("/", tags=["Health"])
async def read_root():
    """A simple health check endpoint."""
    return {"status": "ok"}


# Include routers
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
