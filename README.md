# TaskForge

Enterprise-grade task management library for Python. This repository is currently in a **demo / prototype** stage. The API and CLI are runnable, but **authentication and production hardening are not complete**.

## English

### Status
- Demo-grade authentication and CLI
- Default storage is JSON files
- PostgreSQL/MySQL backends are planned (not production-ready)

### Features
- Core models: Task, Project, User
- TaskManager service layer
- JSON storage backend (file-based)
- REST API (FastAPI)
- CLI (Typer + Rich)
- Search/analytics utilities (experimental)

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
- Demo auth is enabled by default.
- Set `TASKFORGE_DEMO_AUTH=false` to disable demo auth.
- When demo auth is enabled, the API will create a test user on first use.

### Configuration
- Default data directory: `./data`
- Override via `TASKFORGE_DATA_DIR`

### Development
```bash
pytest -q
flake8 taskforge/ tests/
mypy taskforge/
bandit -r taskforge/
```

## ??

### ????
- ??? CLI ?????
- ????? JSON ??
- PostgreSQL/MySQL ?????????????

### ????
- ?????Task / Project / User
- TaskManager ???
- JSON ????
- REST API?FastAPI?
- ??????Typer + Rich?
- ?? / ?????????

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
- ?? `TASKFORGE_DEMO_AUTH=false` ???????
- ?????????????????

### ??
- ???????`./data`
- ??? `TASKFORGE_DATA_DIR` ??

### ????
```bash
pytest -q
flake8 taskforge/ tests/
mypy taskforge/
bandit -r taskforge/
```

## License
MIT
