# AGENTS.md - TaskForge Development Guide

This guide provides essential information for agentic coding agents working with the TaskForge codebase.

## Project Overview

TaskForge is an enterprise-grade task management library built with Python 3.9+. It features:
- Async-first architecture with FastAPI
- Comprehensive data models (Task, Project, User)
- Multiple storage backends (JSON, PostgreSQL, optimized storage)
- CLI interface and REST API
- Plugin system and integrations
- Analytics and reporting capabilities

## Development Commands

### Environment Setup
```bash
# Install in development mode
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

### Code Quality & Formatting
```bash
# Format code
black taskforge/ tests/

# Sort imports
isort taskforge/ tests/

# Lint code
flake8 taskforge/ tests/

# Type checking
mypy taskforge/

# Security linting
bandit -r taskforge/
```

### Testing
```bash
# Run all tests with coverage
pytest --cov=taskforge --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_task.py -v

# Run tests by marker
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests

# Run tests with specific pattern
pytest -k "test_task_creation" -v

# Coverage report
coverage html
```

### Building & Distribution
```bash
# Build package
python -m build

# Install from local build
pip install dist/taskforge-*.whl
```

## Code Style Guidelines

### General Style
- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces
- **Docstrings**: Google style with type hints
- **Encoding**: UTF-8
- **Python version**: 3.9+ compatible

### Import Organization
```python
# Standard library imports
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

# Third-party imports
import pytest
from fastapi import FastAPI
from pydantic import BaseModel

# Local imports
from taskforge.core.task import Task, TaskStatus
from taskforge.utils.auth import AuthManager
```

### Type Hints
- Always use type hints for function signatures
- Use `Optional[T]` for nullable types
- Use Union types for multiple possible types
- Use `Protocol` for duck typing interfaces
- Use `Literal` for string constants

```python
from typing import Any, Dict, List, Optional, Union, Literal
from dataclasses import dataclass

def create_task(
    title: str,
    description: Optional[str] = None,
    priority: TaskPriority = TaskPriority.MEDIUM,
) -> Task:
    """Create a new task with optional description and priority."""
    pass
```

### Naming Conventions
- **Classes**: PascalCase (`TaskManager`, `BaseStorage`)
- **Functions/Methods**: snake_case (`create_task`, `get_user_by_id`)
- **Variables**: snake_case (`user_id`, `task_list`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_TASKS_PER_USER`, `DEFAULT_PRIORITY`)
- **Private methods**: underscore prefix (`_validate_data`, `_internal_method`)
- **Modules/Files**: snake_case (`task_manager.py`, `user_auth.py`)

### Error Handling
```python
# Use specific exceptions
from taskforge.exceptions import TaskNotFoundError, ValidationError

try:
    task = await storage.get_task(task_id)
except TaskNotFoundError:
    logger.error(f"Task {task_id} not found")
    raise
except Exception as e:
    logger.error(f"Unexpected error retrieving task {task_id}: {e}")
    raise

# Custom exceptions
class TaskNotFoundError(Exception):
    """Raised when a task cannot be found."""
    pass
```

### Data Models
```python
# Use Pydantic for data validation
from pydantic import BaseModel, Field, field_validator

class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: TaskPriority = TaskPriority.MEDIUM
    
    @field_validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
```

### Async/Await Patterns
```python
# Always use async for I/O operations
async def get_user_tasks(user_id: str) -> List[Task]:
    """Get all tasks for a user."""
    async with storage.get_session() as session:
        return await session.query(Task).filter(Task.user_id == user_id).all()

# Use asyncio.gather for concurrent operations
async def get_project_data(project_id: str):
    tasks, users, metadata = await asyncio.gather(
        get_project_tasks(project_id),
        get_project_users(project_id),
        get_project_metadata(project_id)
    )
    return tasks, users, metadata
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

async def create_task(task_data: CreateTaskRequest) -> Task:
    """Create a new task."""
    logger.info(f"Creating task: {task_data.title}")
    try:
        task = await task_service.create(task_data)
        logger.info(f"Task created successfully: {task.id}")
        return task
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise
```

## Testing Guidelines

### Test Structure
```python
import pytest
from taskforge.core.task import Task, TaskPriority

class TestTask:
    """Test cases for Task model."""
    
    def test_task_creation(self):
        """Test basic task creation."""
        task = Task(title="Test Task", priority=TaskPriority.HIGH)
        assert task.title == "Test Task"
        assert task.priority == TaskPriority.HIGH
    
    @pytest.mark.asyncio
    async def test_async_task_operations(self):
        """Test async task operations."""
        task = await create_async_task("Async Task")
        assert task.id is not None
```

### Test Fixtures
```python
# tests/conftest.py
import pytest
from taskforge.core.task import Task

@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        title="Test Task",
        description="A test task",
        priority=TaskPriority.MEDIUM
    )

@pytest.fixture
async def async_task_manager():
    """Create an async task manager instance."""
    manager = TaskManager(storage=test_storage)
    await manager.initialize()
    yield manager
    await manager.cleanup()
```

## File Organization

```
taskforge/
├── core/           # Core models (Task, Project, User)
├── storage/        # Storage backends and models
├── api/           # REST API endpoints and schemas
├── cli/           # Command-line interface
├── utils/         # Utilities (auth, cache, search)
├── web/           # Web interfaces and dashboards
└── plugins/       # Plugin system
```

## Common Patterns

### Service Layer Pattern
```python
class TaskService:
    """Service layer for task operations."""
    
    def __init__(self, storage: StorageProtocol, cache: CacheManager):
        self.storage = storage
        self.cache = cache
    
    async def create_task(self, data: CreateTaskRequest) -> Task:
        """Create a new task with validation."""
        # Validate input
        validated_data = self._validate_task_data(data)
        
        # Create task
        task = Task(**validated_data.dict())
        
        # Store and cache
        await self.storage.create_task(task)
        await self.cache.set(f"task:{task.id}", task)
        
        return task
```

### Configuration Management
```python
from taskforge.utils.config import Settings

settings = Settings()

# Usage
database_url = settings.database_url
debug_mode = settings.debug
```

## CI/CD Requirements

- Maintain test coverage above 66%
- All code must pass Black, isort, flake8, and mypy
- Security scans must pass (bandit)
- Pre-commit hooks are mandatory
- Documentation must be updated for API changes

## Security Considerations

- Never commit secrets or API keys
- Use environment variables for configuration
- Implement proper authentication and authorization
- Validate all user inputs
- Use parameterized queries to prevent SQL injection
- Implement rate limiting for API endpoints

## Performance Guidelines

- Use async/await for I/O operations
- Implement proper caching strategies
- Use database indexes for frequently queried fields
- Implement pagination for large result sets
- Monitor and optimize slow queries
- Use connection pooling for database connections