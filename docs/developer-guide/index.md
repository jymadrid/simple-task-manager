# Developer Guide

*TODO: This guide is under construction. It will provide comprehensive documentation for developers working with TaskForge.*

## Architecture Overview

TaskForge is built with a modern, modular architecture:

### Core Components

- **Core Models**: Task, Project, User, and other business entities
- **Storage Layer**: Pluggable storage backends (JSON, PostgreSQL, etc.)
- **API Layer**: RESTful API built with FastAPI
- **CLI Interface**: Command-line interface built with Typer
- **Web Interface**: Dashboard and web-based management

### Project Structure

```
taskforge/
├── core/              # Business logic and models
├── storage/           # Storage backends
├── api/               # REST API endpoints
├── cli/               # Command-line interface
├── web/               # Web dashboard
├── utils/             # Utility functions
└── integrations/      # Third-party integrations
```

## Getting Started

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/taskforge-community/taskforge.git
   cd taskforge
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run tests**
   ```bash
   pytest
   ```

## Contributing Code

### Code Style

We use the following tools to maintain code quality:
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

Run all checks before committing:
```bash
pre-commit run --all-files
```

### Adding New Features

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write tests first**
   ```bash
   pytest tests/unit/test_new_feature.py
   ```

3. **Implement the feature**
   - Follow existing code patterns
   - Add proper docstrings
   - Include type hints

4. **Update documentation**
   - Update relevant docstrings
   - Add examples to user guide

### Storage Backend Development

To create a new storage backend:

1. **Implement the StorageProtocol**
   ```python
   from taskforge.storage.base import StorageProtocol

   class MyStorageBackend(StorageProtocol):
       async def create_task(self, task: Task) -> Task:
           # Implementation here
           pass
   ```

2. **Add configuration options**
   ```python
   from taskforge.utils.config import Config

   @config.field
   def my_storage_url(self) -> str:
       return "http://localhost:8080"
   ```

3. **Write comprehensive tests**
   ```python
   @pytest.mark.asyncio
   async def test_my_storage_backend():
       # Test implementation
       pass
   ```

## API Development

### Adding New Endpoints

1. **Define Pydantic models**
   ```python
   class TaskCreate(BaseModel):
       title: str
       description: Optional[str] = None
   ```

2. **Create route handlers**
   ```python
   @router.post("/tasks", response_model=TaskResponse)
   async def create_task(
       task: TaskCreate,
       current_user: User = Depends(get_current_user)
   ):
       # Implementation
       pass
   ```

3. **Add authentication and authorization**
   ```python
   @router.get("/tasks/{task_id}")
   async def get_task(
       task_id: str,
       current_user: User = Depends(get_current_user)
   ):
       # Check permissions
       pass
   ```

### API Testing

```python
@pytest.mark.asyncio
async def test_create_task_api(client: AsyncClient):
    response = await client.post("/api/v1/tasks", json={
        "title": "Test task",
        "description": "Test description"
    })
    assert response.status_code == 201
```

## CLI Development

### Adding New Commands

1. **Define command function**
   ```python
   @task_app.command("mycommand")
   def my_command(
       arg: str = typer.Argument(..., help="Argument description"),
       option: str = typer.Option("default", "--option", help="Option description")
   ):
       """Command description"""
       # Implementation
       pass
   ```

2. **Add help text and examples**
   ```python
   """My awesome command

   Examples:
       taskforge task mycommand "my argument" --option "value"
   """
   ```

## Testing

### Test Structure

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows

### Writing Tests

```python
# Unit test
def test_task_model():
    task = Task(title="Test task")
    assert task.title == "Test task"

# Integration test
@pytest.mark.asyncio
async def test_task_creation_flow(storage_backend):
    manager = TaskManager(storage_backend)
    task = await manager.create_task(Task(title="Test"))
    assert task.id is not None
```

## Performance

### Optimization Guidelines

1. **Use async/await** for I/O operations
2. **Implement caching** for frequently accessed data
3. **Use database indexes** for query optimization
4. **Profile** using built-in performance tools

### Monitoring

TaskForge includes built-in performance monitoring:
- Query performance tracking
- Memory usage monitoring
- Request latency measurement

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -e ".[all]"
CMD ["taskforge", "serve"]
```

### Production Configuration

- Use PostgreSQL for production
- Configure Redis for caching
- Set up proper logging
- Configure monitoring

---

*This developer guide is actively being expanded. Contributions are welcome!*