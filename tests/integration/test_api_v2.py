from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from taskforge.api.dependencies import get_current_user, get_task_manager
from taskforge.api.main import app
from taskforge.core.project import Project
from taskforge.core.task import Task, TaskPriority, TaskStatus
from taskforge.core.user import User

# Use a test client for the app
client = TestClient(app)


@pytest.fixture
def mock_task_manager():
    """Fixture to create a mock TaskManager."""
    return AsyncMock()


@pytest.fixture(autouse=True)
def override_dependencies(mock_task_manager):
    """
    Fixture to automatically override app dependencies for all tests.
    This ensures each test runs in isolation with fresh mocks.
    """
    app.dependency_overrides[get_task_manager] = lambda: mock_task_manager
    # Provide a default mock user for get_current_user
    mock_user = User(
        id="user-test-id",
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user

    yield

    # Clean up overrides after test
    app.dependency_overrides = {}


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- User Endpoint Tests ---
def test_create_user(mock_task_manager):
    user_data = {"username": "newuser", "email": "new@example.com", "password": "pwd"}
    mock_task_manager.storage.create_user.return_value = User(id="new-id", **user_data)

    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    assert response.json()["username"] == "newuser"


def test_get_user(mock_task_manager):
    mock_task_manager.get_user.return_value = User(
        id="user-id", username="test", email="t@e.com", password_hash="h"
    )
    response = client.get("/api/v1/users/user-id")
    assert response.status_code == 200
    assert response.json()["username"] == "test"


# --- Project Endpoint Tests ---
def test_create_project(mock_task_manager):
    project_data = {"name": "Test Project", "description": "A test project"}
    mock_user = User(
        id="user-test-id",
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )

    # Mock the create_project method to return a valid Project object
    mock_task_manager.create_project.return_value = Project(
        id="proj-id", owner_id=mock_user.id, **project_data
    )

    response = client.post("/api/v1/projects/", json=project_data)
    assert response.status_code == 201
    assert response.json()["name"] == "Test Project"


def test_get_project(mock_task_manager):
    mock_project = Project(id="proj-123", name="My Project", owner_id="user-test-id")
    mock_task_manager.get_project.return_value = mock_project

    response = client.get(f"/api/v1/projects/{mock_project.id}")
    assert response.status_code == 200
    assert response.json()["name"] == "My Project"


# --- Task Endpoint Tests ---
def test_create_task(mock_task_manager):
    task_data = {"title": "Test Task", "project_id": "proj-123"}
    mock_user = User(
        id="user-test-id",
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    mock_project = Project(id="proj-123", name="My Project", owner_id=mock_user.id)

    mock_task_manager.get_project.return_value = mock_project
    mock_task_manager.create_task.return_value = Task(
        id="task-id", created_by=mock_user.id, assigned_to=mock_user.id, **task_data
    )

    response = client.post("/api/v1/tasks/", json=task_data)
    assert response.status_code == 201
    assert response.json()["title"] == "Test Task"


def test_get_task(mock_task_manager):
    mock_user = User(
        id="user-test-id",
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    mock_project = Project(id="proj-123", name="My Project", owner_id=mock_user.id)
    mock_task = Task(id="task-123", title="My Task", project_id=mock_project.id)

    mock_task_manager.get_task.return_value = mock_task
    mock_task_manager.get_project.return_value = mock_project

    response = client.get(f"/api/v1/tasks/{mock_task.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "My Task"
