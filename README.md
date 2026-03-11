# TaskForge

<div align="center">
  <strong>Enterprise‑grade Task Management Platform (Demo)</strong>
  <br />
  <sub>Async‑first · Clean Service Layer · Pluggable Storage</sub>
  <br /><br />
  <a href="#english"><img src="https://img.shields.io/badge/English-View-2F80ED?style=for-the-badge" alt="English"></a>
  <a href="#zh-cn"><img src="https://img.shields.io/badge/%E4%B8%AD%E6%96%87-%E6%9F%A5%E7%9C%8B-27AE60?style=for-the-badge" alt="中文"></a>
</div>

---

<a id="english"></a>

## English

### Overview
TaskForge is a Python task management library and API designed for teams who want a clear domain model, a service layer you can reason about, and an async‑first architecture. This repository is currently a **demo/prototype**. The API and CLI are runnable, but **authentication and production hardening are not complete**.

### Highlights
- Core models: Task, Project, User
- TaskManager service layer
- JSON file storage backend
- REST API with FastAPI
- CLI with Typer + Rich
- Search and analytics utilities (experimental)

### Status
- Demo authentication: enabled by default
- Default storage: JSON files
- PostgreSQL/MySQL: planned, not production‑ready

### Quick Start
```bash
pip install -e ".[dev]"

# CLI (demo)
taskforge --help

# API (demo)
uvicorn taskforge.api.main:app --reload
# Visit http://127.0.0.1:8000/docs
```

### Demo Authentication
- Demo auth is on by default
- Disable with `TASKFORGE_DEMO_AUTH=false`
- When enabled, a test user is auto‑created on first use

### Configuration
- Data directory default: `./data`
- Override with `TASKFORGE_DATA_DIR`

### Development Commands
```bash
pytest -q
flake8 taskforge/ tests/
mypy taskforge/
bandit -r taskforge/
```

### Repository Structure
```
taskforge/
  api/        REST API (FastAPI)
  cli/        CLI (Typer + Rich)
  core/       Core models + TaskManager
  storage/    JSON storage + interfaces
  utils/      Auth, config, search, analytics
examples/     Demo scripts
```

### Roadmap (Planned)
- PostgreSQL/MySQL backends
- Production‑grade authentication
- Stronger RBAC and audit controls

---

<a id="zh-cn"></a>

## 中文

### 概述
TaskForge 是面向团队与开发者的 Python 任务管理库与 API，强调清晰的领域模型、可维护的服务层与异步优先架构。本仓库当前为**演示/原型**阶段，可运行 API 与 CLI，但**认证与生产化能力尚未完成**。

### 亮点
- 核心模型：Task / Project / User
- TaskManager 服务层
- JSON 文件存储
- REST API（FastAPI）
- CLI（Typer + Rich）
- 搜索与分析工具（实验性）

### 当前状态
- 演示认证默认开启
- 默认存储为 JSON 文件
- PostgreSQL/MySQL 计划中，尚不可生产使用

### 快速开始
```bash
pip install -e ".[dev]"

# CLI（演示）
taskforge --help

# API（演示）
uvicorn taskforge.api.main:app --reload
# 访问 http://127.0.0.1:8000/docs
```

### 演示认证
- 默认开启演示认证
- 通过 `TASKFORGE_DEMO_AUTH=false` 关闭
- 开启时会自动创建测试用户

### 配置
- 默认数据目录：`./data`
- 通过 `TASKFORGE_DATA_DIR` 覆盖

### 开发命令
```bash
pytest -q
flake8 taskforge/ tests/
mypy taskforge/
bandit -r taskforge/
```

### 目录结构
```
taskforge/
  api/        REST API（FastAPI）
  cli/        CLI（Typer + Rich）
  core/       核心模型与 TaskManager
  storage/    JSON 存储与接口
  utils/      认证、配置、搜索、分析
examples/     演示脚本
```

### 路线图（计划中）
- PostgreSQL/MySQL 后端
- 生产级认证与权限
- 更完善的 RBAC 与审计能力

---

## License
MIT
