# Contributing to TaskForge 🚀

Thank you for your interest in contributing to TaskForge! We're excited to work with you to build the best task management platform for developers and teams.

## Table of Contents

- [Getting Started](#getting-started)
- [Ways to Contribute](#ways-to-contribute)
- [Development Setup](#development-setup)
- [Code Guidelines](#code-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Community](#community)
- [Recognition](#recognition)

## Getting Started

### Quick Links
- **Bug Reports**: [GitHub Issues](https://github.com/taskforge-community/taskforge/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/taskforge-community/taskforge/discussions)
- **Documentation**: [docs.taskforge.dev](https://docs.taskforge.dev)
- **Community Chat**: [Discord Server](https://discord.gg/taskforge)

### First Time Contributors
- Look for issues labeled [`good first issue`](https://github.com/taskforge-community/taskforge/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
- Check out our [beginner's guide](docs/contributing/beginners-guide.md)
- Join our [Discord community](https://discord.gg/taskforge) for help

## Ways to Contribute

### 🐛 Bug Reports
Help us improve TaskForge by reporting bugs:

1. **Search existing issues** to avoid duplicates
2. **Use the bug report template** when creating new issues
3. **Include detailed reproduction steps**
4. **Add system information** (OS, Python version, TaskForge version)
5. **Provide logs or screenshots** when helpful

### 💡 Feature Requests
We welcome ideas for new features:

1. **Check our [roadmap](ROADMAP.md)** to see planned features
2. **Start a discussion** in GitHub Discussions for major features
3. **Use the feature request template** for formal requests
4. **Explain the use case** and expected benefits

### 📝 Documentation
Documentation is crucial for user adoption:

- **API Documentation**: Improve docstrings and examples
- **User Guides**: Create tutorials and how-to guides
- **Developer Docs**: Technical architecture and contribution guides
- **Translations**: Help translate documentation to other languages

### 🔧 Code Contributions
Direct contributions to the codebase:

- **Bug Fixes**: Resolve reported issues
- **Feature Implementation**: Build new functionality
- **Performance Improvements**: Optimize existing code
- **Refactoring**: Improve code quality and maintainability

### 🔌 Plugin Development
Extend TaskForge with plugins:

- **Integration Plugins**: Connect to external services
- **Notification Plugins**: Custom alert mechanisms
- **Storage Plugins**: Alternative data backends
- **UI Plugins**: Custom dashboard components

## Development Setup

### Prerequisites
- Python 3.8+ (we recommend using pyenv)
- Git
- Docker (optional, for full stack development)
- PostgreSQL (optional, for database testing)

### Local Development

```bash
# Clone the repository
git clone https://github.com/taskforge-community/taskforge.git
cd taskforge

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests to ensure everything works
pytest

# Start development server
taskforge serve --reload
```

### Docker Development

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Run tests in container
docker-compose -f docker-compose.dev.yml exec api pytest

# Access development database
docker-compose -f docker-compose.dev.yml exec postgres psql -U taskforge
```

### Environment Variables

Create a `.env` file for local development:

```bash
# Database
DATABASE_URL=postgresql://taskforge:password@localhost:5432/taskforge_dev
TEST_DATABASE_URL=postgresql://taskforge:password@localhost:5432/taskforge_test

# Security
SECRET_KEY=your-development-secret-key
ALGORITHM=HS256

# External Services (optional)
SLACK_BOT_TOKEN=xoxb-your-slack-token
GITHUB_TOKEN=ghp_your-github-token

# Development
DEBUG=true
LOG_LEVEL=DEBUG
```

## Code Guidelines

### Python Code Style
We follow Python community standards:

```bash
# Format code
black taskforge/ tests/
isort taskforge/ tests/

# Check linting
flake8 taskforge/ tests/
mypy taskforge/

# All checks (run before committing)
pre-commit run --all-files
```

### Code Quality Standards

#### Function Documentation
```python
async def create_task(
    self, 
    task: Task, 
    user_id: str, 
    project_id: Optional[str] = None
) -> Task:
    """Create a new task in the system.
    
    Args:
        task: Task object with title, description, and metadata
        user_id: ID of the user creating the task
        project_id: Optional project ID to associate the task with
        
    Returns:
        Created task with assigned ID and timestamps
        
    Raises:
        ValueError: If task data is invalid
        PermissionError: If user lacks create permissions
    """
```

#### Error Handling
```python
# Good: Specific error handling
try:
    task = await self.storage.get_task(task_id)
except TaskNotFoundError:
    logger.warning(f"Task {task_id} not found for user {user_id}")
    raise HTTPException(status_code=404, detail="Task not found")
except StorageError as e:
    logger.error(f"Storage error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

#### Async/Await Best Practices
```python
# Good: Proper async context management
async def process_batch_tasks(self, tasks: List[Task]) -> List[Task]:
    async with self.storage.transaction():
        results = []
        for task in tasks:
            result = await self.storage.save_task(task)
            results.append(result)
        return results
```

### API Design Guidelines

#### REST API Conventions
- Use proper HTTP methods (GET, POST, PUT, DELETE)
- Follow RESTful URL patterns (`/api/v1/tasks/{id}`)
- Use consistent response formats
- Include proper status codes and error messages

#### Request/Response Models
```python
class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)

class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime
```

## Testing

### Test Structure
```
tests/
├── unit/           # Fast, isolated unit tests
├── integration/    # API and database integration tests
├── e2e/           # End-to-end workflow tests
├── fixtures/      # Test data and fixtures
└── conftest.py    # Pytest configuration
```

### Writing Tests

#### Unit Tests
```python
# tests/unit/test_task.py
import pytest
from taskforge.core.task import Task, TaskPriority, TaskStatus

def test_task_creation():
    task = Task(
        title="Test task",
        description="Test description",
        priority=TaskPriority.HIGH
    )
    
    assert task.title == "Test task"
    assert task.priority == TaskPriority.HIGH
    assert task.status == TaskStatus.TODO

@pytest.mark.asyncio
async def test_task_completion(task_manager, sample_task):
    # Given
    created_task = await task_manager.create_task(sample_task, "user123")
    
    # When
    completed_task = await task_manager.complete_task(created_task.id, "user123")
    
    # Then
    assert completed_task.status == TaskStatus.COMPLETED
    assert completed_task.completed_at is not None
```

#### Integration Tests
```python
# tests/integration/test_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_task_api(client: AsyncClient, auth_headers):
    task_data = {
        "title": "Test API task",
        "description": "Testing task creation via API",
        "priority": "high"
    }
    
    response = await client.post(
        "/api/v1/tasks",
        json=task_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    task = response.json()
    assert task["title"] == "Test API task"
    assert task["priority"] == "high"
```

### Test Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=taskforge --cov-report=html

# Run specific test types
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest -m "not slow"        # Skip slow tests

# Run tests in parallel
pytest -n auto

# Run with verbose output
pytest -v

# Run specific test
pytest tests/unit/test_task.py::test_task_creation
```

## Documentation

### API Documentation
API docs are auto-generated from FastAPI. To contribute:

1. **Update docstrings** in API route functions
2. **Add example requests/responses** using Pydantic models
3. **Include error scenarios** in docstrings

### User Documentation
Located in `docs/` directory:

```
docs/
├── user-guide/         # End-user documentation
├── developer-guide/    # Development and API docs
├── tutorials/          # Step-by-step guides
├── examples/          # Code examples and use cases
└── deployment/        # Installation and deployment
```

### Writing Documentation

#### User Guides
Focus on practical, step-by-step instructions:

```markdown
# Creating Your First Project

This guide walks you through creating and managing your first project in TaskForge.

## Prerequisites
- TaskForge installed and configured
- Basic familiarity with command line

## Step 1: Create a Project
```bash
taskforge project create "My Web App" --description "Personal portfolio website"
```

## Step 2: Add Tasks
```bash
taskforge task add "Design homepage layout" --project "My Web App" --priority high
taskforge task add "Set up development environment" --project "My Web App"
```
```

#### Code Examples
Include practical, runnable examples:

```python
# examples/basic_usage.py
"""Basic TaskForge usage examples."""

import asyncio
from taskforge import TaskManager
from taskforge.storage import JsonStorage

async def basic_task_management():
    """Demonstrate basic task operations."""
    storage = JsonStorage("./data")
    await storage.initialize()
    manager = TaskManager(storage)
    
    # Create a project
    project = await manager.create_project(
        "Demo Project",
        description="Learning TaskForge",
        user_id="demo_user"
    )
    
    # Add tasks
    tasks = [
        "Plan project structure",
        "Set up development environment", 
        "Write documentation",
        "Deploy to production"
    ]
    
    for i, task_title in enumerate(tasks):
        await manager.create_task(
            Task(title=task_title, project_id=project.id),
            user_id="demo_user"
        )
    
    # List all tasks
    user_tasks = await manager.get_user_tasks("demo_user")
    print(f"Created {len(user_tasks)} tasks")

if __name__ == "__main__":
    asyncio.run(basic_task_management())
```

## Pull Request Process

### Before Submitting

1. **Fork the repository** and create a feature branch
2. **Write clear commit messages** following [conventional commits](https://conventionalcommits.org/)
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Run the full test suite** and ensure it passes
6. **Check code quality** with pre-commit hooks

### PR Guidelines

#### Title and Description
Use clear, descriptive titles:

```
Good: "Add task filtering by tags and priority"
Bad:  "Fix stuff"

Good: "Fix memory leak in background task scheduler" 
Bad:  "Bug fix"
```

Include in description:
- **What**: What changes were made
- **Why**: Why the changes were needed
- **How**: How the changes work
- **Testing**: How the changes were tested

#### PR Template
```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] New tests added for functionality
- [ ] All existing tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows the project's style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Changes are backwards compatible
```

### Review Process

1. **Automated checks** must pass (tests, linting, type checking)
2. **Code review** by at least one maintainer
3. **Documentation review** if docs were changed
4. **Manual testing** for significant features
5. **Final approval** and merge by maintainer

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord**: Real-time chat and collaboration
- **Email**: maintainers@taskforge.dev for sensitive issues

### Community Events

- **Monthly Community Calls**: First Wednesday of each month
- **Contributor Workshops**: Quarterly technical sessions
- **Hackathons**: Annual TaskForge extension hackathons
- **User Conferences**: Annual user and developer conference

### Getting Help

#### For Users
- **Documentation**: Start with our [user guide](docs/user-guide/)
- **Examples**: Check [example projects](examples/)
- **Community Forum**: Ask questions in [Discussions](https://github.com/taskforge-community/taskforge/discussions)
- **Discord**: Join our community chat

#### For Developers
- **Developer Guide**: See [developer documentation](docs/developer-guide/)
- **Architecture Docs**: Understand the [system design](docs/architecture/)
- **API Reference**: Complete [API documentation](docs/api/)
- **Discord**: Developer-specific channels available

## Recognition

We value all contributions and want to recognize our community members:

### Contribution Types
- **Code Contributors**: Featured in release notes and repository
- **Documentation Contributors**: Acknowledged in doc pages
- **Community Leaders**: Special recognition and privileges
- **Bug Reporters**: Credits in fix announcements
- **Feature Requesters**: Recognition when features are implemented

### Annual Recognition
- **Outstanding Contributor Award**: Top contributor each year
- **Community Champion**: Best community support and mentorship
- **Innovation Award**: Most creative feature or plugin
- **Documentation Excellence**: Best documentation contributions

### Swag and Benefits
- **Contributor T-shirts**: For significant code contributions
- **Conference Tickets**: Speaking opportunities at events
- **Early Access**: Beta features and preview releases
- **Direct Access**: Priority support and maintainer contact

## Questions?

Don't hesitate to reach out if you have questions:

- **General Questions**: [GitHub Discussions](https://github.com/taskforge-community/taskforge/discussions)
- **Technical Issues**: [GitHub Issues](https://github.com/taskforge-community/taskforge/issues)
- **Security Issues**: maintainers@taskforge.dev (private)
- **Community Chat**: [Discord Server](https://discord.gg/taskforge)

Thank you for contributing to TaskForge! 🚀

---

*This contributing guide is a living document. If you find ways to improve it, please submit a pull request!*