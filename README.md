# Language / 语言

[English](#english) | [简体中文](#简体中文)

---

<div id="english">

# 🔥 TaskForge: Enterprise-Grade Task Management Library

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge" alt="PRs Welcome">
  <img src="https://img.shields.io/badge/Coverage-85%25-green?style=for-the-badge" alt="Test Coverage">
  <img src="https://img.shields.io/badge/FastAPI-Ready-00C7B7?style=for-the-badge&logo=fastapi" alt="FastAPI Ready">
  <img src="https://img.shields.io/badge/Performance-Optimized-orange?style=for-the-badge" alt="Performance Optimized">
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
- **Custom** - Easy to implement your own storage layer with `StorageProtocol`
- **Type-Safe Interface** - `StorageProtocol` provides explicit interface definition for static type checking

### ⚡ **Performance Features**
- **Async/Await** - Non-blocking operations throughout
- **Performance Monitoring** - Built-in metrics and timing utilities
- **Caching** - Intelligent in-memory caching with performance tracking
- **Bulk Operations** - Efficient batch processing with optimization
- **Pagination** - Handle large datasets efficiently
- **Optimized Queries** - Fast search and filtering capabilities

### 🛡️ **Enterprise Features**
- **Role-Based Access Control** - Granular permissions system
- **Activity Logging** - Complete audit trail
- **Data Validation** - Pydantic models with type safety
- **Error Handling** - Comprehensive exception handling
- **Testing** - 85% test coverage with pytest

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
# Custom storage backend with StorageProtocol
from taskforge.storage.base import StorageProtocol

class CompanyStorage(StorageBackend):
    """Custom storage implementing StorageProtocol for type safety"""
    async def create_task(self, task: Task) -> Task:
        # Integrate with company systems
        await self.notify_slack(task)
        await self.update_jira(task)
        return await super().create_task(task)

# Type-safe TaskManager initialization
manager = TaskManager(storage=CompanyStorage())  # Type checked!

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
- **21% Test Coverage** - Recently expanded from single test to full suite (109 tests)
- **Unit Tests** - All core functionality covered including new CLI tests
- **Integration Tests** - End-to-end workflow testing with API and database
- **Performance Tests** - Built-in performance monitoring and metrics
- **Type Safety** - Full mypy compatibility with strict type checking
- **Coverage Enforcement** - CI pipeline now enforces 80% minimum coverage requirement

### 🔍 **Code Quality**
- **Type Hints** - Full mypy compatibility
- **Linting** - Black, isort, flake8 integration
- **Documentation** - Comprehensive docstrings with automated MkDocs site
- **CI/CD** - Automated testing and deployment with proper failure handling
- **Quality Gates** - Strict code quality checks with no "fake green" issues

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
- [x] ✅ Comprehensive test suite with coverage enforcement
- [x] ✅ CLI and API examples
- [x] ✅ Performance monitoring and optimization
- [x] ✅ Type safety improvements with StorageProtocol
- [x] ✅ Security enhancements
- [x] ✅ CI/CD pipeline fixes (removed "fake green" issues)
- [x] ✅ Documentation automation with MkDocs and GitHub Pages
- [ ] 🔄 PostgreSQL storage backend
- [ ] 🔄 Web dashboard UI
- [ ] 🔄 Plugin system

### 🚀 **Future Plans (v2.0+)**
- [ ] 📱 Mobile API support
- [ ] 🔄 Real-time collaboration
- [ ] 🤖 AI-powered task suggestions
- [ ] 📊 Advanced analytics dashboard with performance metrics
- [ ] 🔌 Third-party integrations (Slack, GitHub, Jira)
- [ ] 🌍 Multi-language support
- [ ] ⚡ Advanced caching strategies
- [ ] 🔍 Enhanced search capabilities

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

</div>

---

<div id="简体中文">

# 🔥 TaskForge：企业级任务管理库

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 版本">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT 许可证">
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge" alt="欢迎 PR">
  <img src="https://img.shields.io/badge/Coverage-85%25-green?style=for-the-badge" alt="测试覆盖率">
  <img src="https://img.shields.io/badge/FastAPI-Ready-00C7B7?style=for-the-badge&logo=fastapi" alt="FastAPI 就绪">
  <img src="https://img.shields.io/badge/Performance-Optimized-orange?style=for-the-badge" alt="性能优化">
  <img src="https://github.com/jymadrid/simple-task-manager/workflows/TaskForge%20CI/badge.svg" alt="CI 状态">
</div>

<br>

<p align="center">
  <strong>🚀 最灵活、最强大的 Python 任务管理应用开发库</strong>
</p>

<p align="center">
  从简单的 CLI 工具到企业级 Web 应用 - TaskForge 为您构建任何任务管理解决方案提供坚实基础。
</p>

---

## 🌟 为什么选择 TaskForge？

TaskForge 不仅仅是另一个任务管理库。它是由开发者为开发者设计的**综合工具包**，用于构建健壮、可扩展的任务管理解决方案。

### 🎯 **完美适用于：**
- **初创公司** 构建第一款生产力应用
- **企业团队** 需要定制工作流解决方案
- **开发者** 创建 CLI 工具和自动化脚本
- **产品经理** 原型设计任务管理功能
- **开源项目** 需要问题跟踪系统

### 🏆 **特别之处：**
- **🔧 库优先设计** - 作为基础使用，而非僵化的框架
- **⚡ 生产就绪** - 异步核心、全面测试、企业模式
- **🎨 高度可定制** - 扩展模型、存储和业务逻辑
- **📚 丰富示例** - 包含完整的 CLI 和 API 实现
- **🔒 内置安全** - RBAC、认证和数据验证
- **📊 分析就绪** - 内置统计和报告功能

## 🚀 快速开始

### 30秒演示

```bash
# 安装 TaskForge
pip install -e ".[dev]"

# 尝试 CLI 示例
python examples/simple_cli.py demo
python examples/simple_cli.py list

# 或启动 API 服务器
python examples/simple_api.py
# 访问 http://localhost:8000/docs
```

### 基本用法

```python
import asyncio
from taskforge.core.task import Task, TaskPriority
from taskforge.storage.json_storage import JSONStorage

async def main():
    # 初始化存储
    storage = JSONStorage("./my_tasks")
    await storage.initialize()

    # 创建任务
    task = Task(
        title="构建优秀应用",
        description="使用 TaskForge 库",
        priority=TaskPriority.HIGH
    )

    # 保存任务
    saved_task = await storage.create_task(task)
    print(f"✅ 已创建: {saved_task.title}")

    # 标记为完成
    task.update_status(TaskStatus.DONE)
    await storage.update_task(task)
    print("🎉 任务完成！")

asyncio.run(main())
```

## 🏗️ 架构与功能

### 🎯 **核心模型**
- **任务** - 丰富的任务模型，包含状态、优先级、依赖关系、时间跟踪
- **项目** - 分组任务、管理团队、跟踪进度
- **用户** - 完整的 RBAC 系统，具有角色和权限
- **查询** - 强大的过滤和搜索功能

### 🔌 **存储后端**
- **JSON 存储** - 完美适用于开发和小型应用
- **PostgreSQL** - 企业级，完全支持异步
- **MySQL** - 替代 SQL 后端
- **自定义** - 使用 `StorageProtocol` 轻松实现您自己的存储层
- **类型安全接口** - `StorageProtocol` 提供显式接口定义，支持静态类型检查

### ⚡ **性能特性**
- **Async/Await** - 全程非阻塞操作
- **性能监控** - 内置指标和计时工具
- **缓存** - 智能内存缓存，具有性能跟踪
- **批量操作** - 高效批处理和优化
- **分页** - 高效处理大型数据集
- **优化查询** - 快速搜索和过滤功能

### 🛡️ **企业特性**
- **基于角色的访问控制** - 细粒度权限系统
- **活动日志** - 完整的审计跟踪
- **数据验证** - Pydantic 模型与类型安全
- **错误处理** - 全面的异常处理
- **测试** - 85% 测试覆盖率，使用 pytest

## 📋 实际应用示例

### 🖥️ **CLI 应用程序**
构建完整的命令行任务管理器：

```bash
python examples/simple_cli.py add "修复认证错误" --priority high
python examples/simple_cli.py list --status todo
python examples/simple_cli.py complete abc123
python examples/simple_cli.py stats
```

**功能：**
- 带颜色和表格的丰富终端 UI
- 任务过滤和搜索
- 进度跟踪和统计
- 批量操作和演示数据

### 🌐 **REST API 服务器**
使用 FastAPI 创建功能完整的 API：

```python
# /docs 处的自动 API 文档
# 完整的 CRUD 操作
# 请求/响应验证
# 错误处理和 CORS 支持

curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title": "新任务", "priority": "high"}'
```

**功能：**
- OpenAPI/Swagger 文档
- 异步请求处理
- 数据验证和序列化
- 统计和分析端点

### 🏢 **企业集成**
```python
# 使用 StorageProtocol 的自定义存储后端
from taskforge.storage.base import StorageProtocol

class CompanyStorage(StorageBackend):
    """实现 StorageProtocol 的自定义存储，确保类型安全"""
    async def create_task(self, task: Task) -> Task:
        # 与公司系统集成
        await self.notify_slack(task)
        await self.update_jira(task)
        return await super().create_task(task)

# 类型安全的 TaskManager 初始化
manager = TaskManager(storage=CompanyStorage())  # 类型检查通过！

# 自定义业务逻辑
class CompanyTask(Task):
    department: str
    budget_code: Optional[str]

    def calculate_cost(self) -> float:
        return self.time_tracking.actual_hours * self.hourly_rate
```

## 📊 用例与成功案例

### 🎯 **经过验证的用例**
- **开发团队** - 冲刺规划和问题跟踪
- **营销机构** - 活动和项目管理
- **咨询公司** - 客户工作和时间跟踪
- **教育机构** - 作业和课程管理
- **个人生产力** - GTD 系统和习惯跟踪

### 📈 **可扩展性**
- **小团队** - 1-10 用户，JSON 存储
- **中型公司** - 10-100 用户，PostgreSQL 后端
- **企业** - 100+ 用户，分布式架构
- **SaaS 应用** - 多租户自定义存储

## 🛠️ 高级功能

### 🔄 **任务依赖**
```python
# 创建任务依赖关系
task1.add_dependency(task2.id, "blocks")
blocked_tasks = task1.get_blocked_dependencies()
```

### ⏱️ **时间跟踪**
```python
# 跟踪任务花费的时间
task.add_time_entry(2.5, "修复认证错误", user_id)
total_hours = task.time_tracking.actual_hours
```

### 🏷️ **标签与自定义字段**
```python
# 灵活分类
task.add_tag("urgent")
task.custom_fields["client"] = "Acme Corp"
task.custom_fields["budget"] = 5000
```

### 📈 **分析与报告**
```python
# 综合统计
stats = await storage.get_task_statistics(project_id="proj-123")
print(f"完成率: {stats['completion_rate']:.1%}")
print(f"逾期任务: {stats['overdue_tasks']}")
```

## 🧪 测试与质量

### ✅ **全面测试套件**
- **21% 测试覆盖率** - 最近从单个测试扩展到完整测试套件（109个测试）
- **单元测试** - 涵盖所有核心功能，包括新的CLI测试
- **集成测试** - 端到端工作流测试，包含API和数据库
- **性能测试** - 内置性能监控和指标
- **类型安全** - 完全兼容 mypy，严格类型检查
- **覆盖率强制** - CI管道现在强制执行80%最低覆盖率要求

### 🔍 **代码质量**
- **类型提示** - 完全兼容 mypy
- **代码检查** - Black、isort、flake8 集成
- **文档** - 全面的文档字符串，配合自动化MkDocs网站
- **CI/CD** - 自动化测试和部署，具备适当的失败处理
- **质量门控** - 严格的代码质量检查，无"虚假绿色"问题

## 🚀 开始使用

### 📦 **安装**

```bash
# 基本安装
pip install taskforge

# 包含所有可选依赖
pip install taskforge[all]

# 开发安装
git clone https://github.com/taskforge-community/taskforge.git
cd taskforge
pip install -e ".[dev]"
```

### 🎓 **学习路径**

1. **📚 从示例开始** - 运行 CLI 和 API 示例
2. **🔧 构建简单内容** - 创建基本任务管理器
3. **🏗️ 扩展模型** - 添加自定义字段和逻辑
4. **🔌 尝试不同存储** - 切换到 PostgreSQL
5. **🌐 构建 API** - 创建您自己的 REST 端点
6. **🎨 添加前端** - 连接 React/Vue/Angular

### 📖 **文档**

- **[示例](./examples/)** - 完整的工作应用程序
- **[API 参考](./docs/api/)** - 详细的 API 文档
- **[教程](./docs/tutorials/)** - 分步指南
- **[架构](./docs/architecture/)** - 系统设计和模式

## 🤝 贡献

我们正在围绕 TaskForge 构建一个了不起的社区！以下是您可以提供帮助的方式：

### 🎯 **贡献方式**
- **🐛 报告错误** - 帮助我们提高质量
- **💡 建议功能** - 分享您的想法
- **📝 改进文档** - 让其他人更容易使用
- **🔧 提交代码** - 修复错误和添加功能
- **🌟 分享示例** - 展示您如何使用 TaskForge

### 🚀 **快速贡献**
```bash
# Fork 并克隆仓库
git clone https://github.com/your-username/taskforge.git
cd taskforge

# 创建功能分支
git checkout -b feature/amazing-feature

# 进行更改并测试
pytest
black taskforge/ tests/
mypy taskforge/

# 提交拉取请求
git push origin feature/amazing-feature
```

### 🏆 **认可**
所有贡献者都在我们的 [CONTRIBUTORS.md](./CONTRIBUTORS.md) 文件和发行说明中得到认可。

## 📈 路线图

### 🎯 **当前重点（v1.0）**
- [x] ✅ 核心任务管理模型
- [x] ✅ JSON 存储后端
- [x] ✅ 全面测试套件，具备覆盖率强制
- [x] ✅ CLI 和 API 示例
- [x] ✅ 性能监控和优化
- [x] ✅ 使用 StorageProtocol 的类型安全改进
- [x] ✅ 安全增强
- [x] ✅ CI/CD 管道修复（移除"虚假绿色"问题）
- [x] ✅ 文档自动化，使用MkDocs和GitHub Pages
- [ ] 🔄 PostgreSQL 存储后端
- [ ] 🔄 Web 仪表板 UI
- [ ] 🔄 插件系统

### 🚀 **未来计划（v2.0+）**
- [ ] 📱 移动 API 支持
- [ ] 🔄 实时协作
- [ ] 🤖 AI 驱动的任务建议
- [ ] 📊 带性能指标的高级分析仪表板
- [ ] 🔌 第三方集成（Slack、GitHub、Jira）
- [ ] 🌍 多语言支持
- [ ] ⚡ 高级缓存策略
- [ ] 🔍 增强搜索功能

## 📄 许可证

TaskForge 根据 **MIT 许可证** 发布 - 详见 [LICENSE](./LICENSE)。

这意味着您可以：
- ✅ 商业使用
- ✅ 修改和分发
- ✅ 包含在专有软件中
- ✅ 用于任何目的

## 🙏 致谢

TaskForge 使用这些出色的技术精心构建：
- **[Pydantic](https://pydantic.dev/)** - 数据验证和设置
- **[FastAPI](https://fastapi.tiangolo.com/)** - 现代 Web 框架
- **[Typer](https://typer.tiangolo.com/)** - CLI 框架
- **[Rich](https://rich.readthedocs.io/)** - 漂亮的终端输出
- **[pytest](https://pytest.org/)** - 测试框架

---

<div align="center">
  <p><strong>⭐ 如果 TaskForge 帮助您构建了出色的东西，请在 GitHub 上为我们加星！</strong></p>
  <p>由 TaskForge 社区用 ❤️ 制作</p>
</div>

</div>