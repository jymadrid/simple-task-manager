# TaskForge

<div align="center">
  <strong>Enterprise?grade Task Management Platform (Demo)</strong>
  <br />
  <sub>FastAPI + Async-first + Pluggable Storage</sub>
  <br /><br />
  <a href="#english"><img src="https://img.shields.io/badge/English-View-2F80ED?style=for-the-badge" alt="English"></a>
  <a href="#zh-cn"><img src="https://img.shields.io/badge/%E4%B8%AD%E6%96%87-%E6%9F%A5%E7%9C%8B-27AE60?style=for-the-badge" alt="??"></a>
</div>

---

<div id="english"></div>

## English

### Positioning
TaskForge is a Python task management library and API designed for teams who want a clean service layer, clear models, and an async-first architecture. This repository is currently a **demo/prototype**. API and CLI are runnable, but **authentication and production hardening are not complete**.

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
- PostgreSQL/MySQL: planned, not production-ready

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
- When enabled, a test user is auto-created on first use

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
- Production-grade authentication
- Stronger RBAC and audit controls

---

<div id="zh-cn"></div>

## ??

### ??
TaskForge ?????????? Python ?????? API??????????????????????????**??/??**?????? API ? CLI??**????????????**?

### ??
- ?????Task / Project / User
- TaskManager ???
- JSON ????
- REST API?FastAPI?
- CLI?Typer + Rich?
- ????????????

### ????
- ????????
- ????? JSON ??
- PostgreSQL/MySQL ???????????

### ????
```bash
pip install -e ".[dev]"

# CLI????
taskforge --help

# API????
uvicorn taskforge.api.main:app --reload
# ?? http://127.0.0.1:8000/docs
```

### ????
- ????????
- ?? `TASKFORGE_DEMO_AUTH=false` ??
- ????????????

### ??
- ???????`./data`
- ?? `TASKFORGE_DATA_DIR` ??

### ????
```bash
pytest -q
flake8 taskforge/ tests/
mypy taskforge/
bandit -r taskforge/
```

### ????
```
taskforge/
  api/        REST API?FastAPI?
  cli/        CLI?Typer + Rich?
  core/       ????? TaskManager
  storage/    JSON ?????
  utils/      ???????????
examples/     ????
```

### ????????
- PostgreSQL/MySQL ??
- ????????
- ???? RBAC ?????

---

## License
MIT
