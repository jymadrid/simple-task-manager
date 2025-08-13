# TaskForge Examples

This directory contains practical examples demonstrating how to use TaskForge as a library to build various types of applications.

## 🚀 Quick Start

### Prerequisites

```bash
# Install TaskForge with all dependencies
pip install -e ".[dev,web]"
```

## 📋 Available Examples

### 1. Simple CLI (`simple_cli.py`)

A complete command-line task manager built with TaskForge and Click.

**Features:**
- Add, list, complete, and delete tasks
- Filter tasks by status and priority
- Rich terminal UI with colors and tables
- Task statistics and progress tracking
- Demo data generation

**Usage:**
```bash
# Run the CLI
python examples/simple_cli.py --help

# Add a task
python examples/simple_cli.py add "Fix authentication bug" --priority high

# List all tasks
python examples/simple_cli.py list

# List only completed tasks
python examples/simple_cli.py list --status done

# Complete a task (use partial ID)
python examples/simple_cli.py complete abc123

# Show statistics
python examples/simple_cli.py stats

# Create demo data
python examples/simple_cli.py demo
```

**Screenshot:**
```
📋 Your Tasks (5 total)
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ ID         ┃ Title                                    ┃ Status       ┃ Priority   ┃ Created      ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│ abc123...  │ Fix authentication bug                   │ todo         │ high       │ 01/15 14:30  │
│ def456...  │ Update documentation                     │ in_progress  │ medium     │ 01/15 14:31  │
│ ghi789...  │ Implement dark mode                      │ done         │ low        │ 01/15 14:32  │
└────────────┴──────────────────────────────────────────┴──────────────┴────────────┴──────────────┘
```

### 2. REST API (`simple_api.py`)

A complete REST API server built with TaskForge and FastAPI.

**Features:**
- Full CRUD operations for tasks
- Automatic API documentation
- Request/response validation
- Error handling
- CORS support
- Task statistics endpoint

**Usage:**
```bash
# Start the API server
python examples/simple_api.py

# The server will start on http://localhost:8000
# Visit http://localhost:8000/docs for interactive documentation
```

**API Endpoints:**
- `GET /` - API information
- `GET /tasks` - List tasks with filtering
- `POST /tasks` - Create a new task
- `GET /tasks/{id}` - Get specific task
- `PUT /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task
- `POST /tasks/{id}/complete` - Mark task as complete
- `GET /stats` - Get task statistics
- `POST /demo` - Create demo data

**Example API Usage:**
```bash
# Create a task
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix bug in user authentication",
    "description": "Users cannot login with special characters",
    "priority": "high"
  }'

# List all tasks
curl "http://localhost:8000/tasks"

# Get task statistics
curl "http://localhost:8000/stats"

# Create demo data
curl -X POST "http://localhost:8000/demo"
```

## 🏗️ Building Your Own Application

These examples demonstrate the core patterns for using TaskForge:

### 1. Initialize Storage
```python
from taskforge.storage.json_storage import JSONStorage

storage = JSONStorage("./data")
await storage.initialize()
```

### 2. Create and Manage Tasks
```python
from taskforge.core.task import Task, TaskPriority, TaskStatus

# Create a task
task = Task(
    title="My Task",
    description="Task description",
    priority=TaskPriority.HIGH
)

# Save to storage
created_task = await storage.create_task(task)

# Update task status
task.update_status(TaskStatus.DONE, user_id="user123")
await storage.update_task(task)
```

### 3. Query and Filter Tasks
```python
from taskforge.core.queries import TaskQuery

# Create a query
query = TaskQuery(
    status=[TaskStatus.TODO, TaskStatus.IN_PROGRESS],
    priority=[TaskPriority.HIGH],
    limit=50
)

# Search tasks
tasks = await storage.search_tasks(query, user_id="user123")
```

### 4. Get Statistics
```python
# Get comprehensive statistics
stats = await storage.get_task_statistics(user_id="user123")
print(f"Completion rate: {stats['completion_rate']:.1%}")
```

## 🎯 Use Cases

TaskForge is perfect for building:

- **Personal productivity tools** - CLI apps, desktop apps
- **Team collaboration platforms** - Web apps with real-time updates
- **Project management systems** - Enterprise solutions
- **Integration tools** - Sync with external services
- **Automation workflows** - Task scheduling and processing
- **Analytics dashboards** - Progress tracking and reporting

## 🔧 Customization

### Custom Storage Backend
```python
from taskforge.storage.base import StorageBackend

class MyCustomStorage(StorageBackend):
    async def create_task(self, task: Task) -> Task:
        # Your custom implementation
        pass
```

### Custom Task Fields
```python
from taskforge.core.task import Task

class MyTask(Task):
    custom_field: str = "default_value"
    
    def my_custom_method(self):
        # Your custom logic
        pass
```

### Integration with External Services
```python
# Example: Slack notifications
async def notify_task_completed(task: Task):
    slack_client.send_message(
        f"Task completed: {task.title}"
    )

# Hook into task updates
task.update_status(TaskStatus.DONE, user_id)
await notify_task_completed(task)
```

## 📚 Next Steps

1. **Explore the core library** - Check out `taskforge/core/` for all available models
2. **Try different storage backends** - PostgreSQL, MySQL support available
3. **Add authentication** - Implement user management and permissions
4. **Build a web UI** - Use the API with React, Vue, or any frontend framework
5. **Add integrations** - Connect with Slack, GitHub, Jira, etc.

## 🤝 Contributing

Found a bug or want to add a new example? Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Add your example with documentation
4. Submit a pull request

## 📄 License

These examples are part of the TaskForge project and are licensed under the MIT License.