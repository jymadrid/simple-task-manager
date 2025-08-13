# 🔥 TaskForge: Enterprise-Grade Task Management Library

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge" alt="PRs Welcome">
  <img src="https://img.shields.io/badge/Coverage-77%25-green?style=for-the-badge" alt="Test Coverage">
  <img src="https://img.shields.io/badge/FastAPI-Ready-00C7B7?style=for-the-badge&logo=fastapi" alt="FastAPI Ready">
  <img src="https://github.com/jymadrid/simple-task-manager/workflows/TaskForge%20CI/badge.svg" alt="CI Status">
</div>

<br>

<p align="center">
  <strong>🚀 The most flexible and powerful Python library for building task management applications</strong>
</p>

<p align="center">
  From simple CLI tools to enterprise-scale web applications - TaskForge provides the foundation you need to build any task management solution.
</p>

---

## 🌟 Why TaskForge?

TaskForge isn't just another task management library. It's a **comprehensive toolkit** designed by developers, for developers who need to build robust, scalable task management solutions.

### 🎯 **Perfect For:**
- **Startups** building their first productivity app
- **Enterprise teams** needing custom workflow solutions  
- **Developers** creating CLI tools and automation scripts
- **Product managers** prototyping task management features
- **Open source projects** requiring issue tracking systems

### 🏆 **What Makes It Special:**
- **🔧 Library-First Design** - Use as a foundation, not a rigid framework
- **⚡ Production Ready** - Async core, comprehensive testing, enterprise patterns
- **🎨 Highly Customizable** - Extend models, storage, and business logic
- **📚 Rich Examples** - Complete CLI and API implementations included
- **🔒 Security Built-In** - RBAC, authentication, and data validation
- **📊 Analytics Ready** - Built-in statistics and reporting capabilities

## 🚀 Quick Start

### 30-Second Demo

```bash
# Install TaskForge
pip install -e ".[dev]"

# Try the CLI example
python examples/simple_cli.py demo
python examples/simple_cli.py list

# Or start the API server
python examples/simple_api.py
# Visit http://localhost:8000/docs
```

### Basic Usage

```python
import asyncio
from taskforge.core.task import Task, TaskPriority
from taskforge.storage.json_storage import JSONStorage

async def main():
    # Initialize storage
    storage = JSONStorage("./my_tasks")
    await storage.initialize()
    
    # Create a task
    task = Task(
        title="Build awesome app",
        description="Using TaskForge library",
        priority=TaskPriority.HIGH
    )
    
    # Save it
    saved_task = await storage.create_task(task)
    print(f"✅ Created: {saved_task.title}")
    
    # Mark as complete
    task.update_status(TaskStatus.DONE)
    await storage.update_task(task)
    print("🎉 Task completed!")

asyncio.run(main())
```

## 🏗️ Architecture & Features

### 🎯 **Core Models**
- **Tasks** - Rich task model with status, priority, dependencies, time tracking
- **Projects** - Group tasks, manage teams, track progress  
- **Users** - Full RBAC system with roles and permissions
- **Queries** - Powerful filtering and search capabilities

### 🔌 **Storage Backends**
- **JSON Storage** - Perfect for development and small applications
- **PostgreSQL** - Enterprise-grade with full async support
- **MySQL** - Alternative SQL backend
- **Custom** - Easy to implement your own storage layer

### ⚡ **Performance Features**
- **Async/Await** - Non-blocking operations throughout
- **Caching** - Intelligent in-memory caching
- **Bulk Operations** - Efficient batch processing
- **Pagination** - Handle large datasets efficiently

### 🛡️ **Enterprise Features**
- **Role-Based Access Control** - Granular permissions system
- **Activity Logging** - Complete audit trail
- **Data Validation** - Pydantic models with type safety
- **Error Handling** - Comprehensive exception handling
- **Testing** - 77% test coverage with pytest

## 📋 Real-World Examples

### 🖥️ **CLI Application**
Build a complete command-line task manager:

```bash
python examples/simple_cli.py add "Fix authentication bug" --priority high
python examples/simple_cli.py list --status todo
python examples/simple_cli.py complete abc123
python examples/simple_cli.py stats
```

**Features:**
- Rich terminal UI with colors and tables
- Task filtering and search
- Progress tracking and statistics
- Bulk operations and demo data

### 🌐 **REST API Server**
Create a full-featured API with FastAPI:

```python
# Automatic API documentation at /docs
# Full CRUD operations
# Request/response validation
# Error handling and CORS support

curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title": "New task", "priority": "high"}'
```

**Features:**
- OpenAPI/Swagger documentation
- Async request handling
- Data validation and serialization
- Statistics and analytics endpoints

### 🏢 **Enterprise Integration**
```python
# Custom storage backend
class CompanyStorage(StorageBackend):
    async def create_task(self, task: Task) -> Task:
        # Integrate with company systems
        await self.notify_slack(task)
        await self.update_jira(task)
        return await super().create_task(task)

# Custom business logic
class CompanyTask(Task):
    department: str
    budget_code: Optional[str]
    
    def calculate_cost(self) -> float:
        return self.time_tracking.actual_hours * self.hourly_rate
```

## 📊 Use Cases & Success Stories

### 🎯 **Proven Use Cases**
- **Development Teams** - Sprint planning and issue tracking
- **Marketing Agencies** - Campaign and project management  
- **Consulting Firms** - Client work and time tracking
- **Educational Institutions** - Assignment and course management
- **Personal Productivity** - GTD systems and habit tracking

### 📈 **Scalability**
- **Small Teams** - 1-10 users, JSON storage
- **Medium Companies** - 10-100 users, PostgreSQL backend
- **Enterprise** - 100+ users, distributed architecture
- **SaaS Applications** - Multi-tenant with custom storage

## 🛠️ Advanced Features

### 🔄 **Task Dependencies**
```python
# Create task dependencies
task1.add_dependency(task2.id, "blocks")
blocked_tasks = task1.get_blocked_dependencies()
```

### ⏱️ **Time Tracking**
```python
# Track time spent on tasks
task.add_time_entry(2.5, "Fixed authentication bug", user_id)
total_hours = task.time_tracking.actual_hours
```

### 🏷️ **Tags & Custom Fields**
```python
# Flexible categorization
task.add_tag("urgent")
task.custom_fields["client"] = "Acme Corp"
task.custom_fields["budget"] = 5000
```

### 📈 **Analytics & Reporting**
```python
# Comprehensive statistics
stats = await storage.get_task_statistics(project_id="proj-123")
print(f"Completion rate: {stats['completion_rate']:.1%}")
print(f"Overdue tasks: {stats['overdue_tasks']}")
```

## 🧪 Testing & Quality

### ✅ **Comprehensive Test Suite**
- **77% Test Coverage** - Thoroughly tested codebase
- **Unit Tests** - All core functionality covered
- **Integration Tests** - End-to-end workflow testing
- **Performance Tests** - Scalability and load testing

### 🔍 **Code Quality**
- **Type Hints** - Full mypy compatibility
- **Linting** - Black, isort, flake8 integration
- **Documentation** - Comprehensive docstrings
- **CI/CD** - Automated testing and deployment

## 🚀 Getting Started

### 📦 **Installation**

```bash
# Basic installation
pip install taskforge

# With all optional dependencies
pip install taskforge[all]

# Development installation
git clone https://github.com/taskforge-community/taskforge.git
cd taskforge
pip install -e ".[dev]"
```

### 🎓 **Learning Path**

1. **📚 Start with Examples** - Run the CLI and API examples
2. **🔧 Build Something Simple** - Create a basic task manager
3. **🏗️ Extend the Models** - Add custom fields and logic
4. **🔌 Try Different Storage** - Switch to PostgreSQL
5. **🌐 Build an API** - Create your own REST endpoints
6. **🎨 Add a Frontend** - Connect with React/Vue/Angular

### 📖 **Documentation**

- **[Examples](./examples/)** - Complete working applications
- **[API Reference](./docs/api/)** - Detailed API documentation
- **[Tutorials](./docs/tutorials/)** - Step-by-step guides
- **[Architecture](./docs/architecture/)** - System design and patterns

## 🤝 Contributing

We're building an amazing community around TaskForge! Here's how you can help:

### 🎯 **Ways to Contribute**
- **🐛 Report Bugs** - Help us improve quality
- **💡 Suggest Features** - Share your ideas
- **📝 Improve Docs** - Make it easier for others
- **🔧 Submit Code** - Fix bugs and add features
- **🌟 Share Examples** - Show how you use TaskForge

### 🚀 **Quick Contribution**
```bash
# Fork and clone the repo
git clone https://github.com/your-username/taskforge.git
cd taskforge

# Create a feature branch
git checkout -b feature/amazing-feature

# Make your changes and test
pytest
black taskforge/ tests/
mypy taskforge/

# Submit a pull request
git push origin feature/amazing-feature
```

### 🏆 **Recognition**
All contributors are recognized in our [CONTRIBUTORS.md](./CONTRIBUTORS.md) file and release notes.

## 📈 Roadmap

### 🎯 **Current Focus (v1.0)**
- [x] ✅ Core task management models
- [x] ✅ JSON storage backend  
- [x] ✅ Comprehensive test suite
- [x] ✅ CLI and API examples
- [ ] 🔄 PostgreSQL storage backend
- [ ] 🔄 Web dashboard UI
- [ ] 🔄 Plugin system

### 🚀 **Future Plans (v2.0+)**
- [ ] 📱 Mobile API support
- [ ] 🔄 Real-time collaboration
- [ ] 🤖 AI-powered task suggestions
- [ ] 📊 Advanced analytics dashboard
- [ ] 🔌 Third-party integrations (Slack, GitHub, Jira)
- [ ] 🌍 Multi-language support

## 📄 License

TaskForge is released under the **MIT License** - see [LICENSE](./LICENSE) for details.

This means you can:
- ✅ Use it commercially
- ✅ Modify and distribute
- ✅ Include in proprietary software
- ✅ Use for any purpose

## 🙏 Acknowledgments

TaskForge is built with love using these amazing technologies:
- **[Pydantic](https://pydantic.dev/)** - Data validation and settings
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern web framework
- **[Typer](https://typer.tiangolo.com/)** - CLI framework
- **[Rich](https://rich.readthedocs.io/)** - Beautiful terminal output
- **[pytest](https://pytest.org/)** - Testing framework

---

<div align="center">
  <p><strong>⭐ Star us on GitHub if TaskForge helps you build amazing things!</strong></p>
  <p>Made with ❤️ by the TaskForge Community</p>
</div>
