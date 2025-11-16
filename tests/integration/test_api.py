"""
Integration tests for API endpoints
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from taskforge.api import create_app
from taskforge.core.task import Task, TaskPriority, TaskStatus
from taskforge.core.user import User, UserRole


@pytest.fixture
def api_client():
    """Create test API client"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test-token"}


class TestTaskAPI:
    """Integration tests for task API endpoints"""

    def test_health_check(self, api_client):
        """Test health check endpoint"""
        response = api_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_create_task(self, api_client, auth_headers, monkeypatch):
        """Test task creation via API"""
        # Mock get_current_user and dependencies first
        mock_user = Mock(spec=User)
        mock_user.id = "test-user-id"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"

        # Mock the task manager
        mock_manager = AsyncMock()
        mock_task = Task(
            id="test-task-id",
            title="API Test Task",
            description="Created via API",
            priority=TaskPriority.HIGH,
        )
        mock_manager.create_task.return_value = mock_task
        mock_manager.get_user.return_value = mock_user

        # Mock get_manager function
        monkeypatch.setattr("taskforge.api.get_manager", lambda: mock_manager)

        async def mock_get_current_user(credentials=None):
            return mock_user

        monkeypatch.setattr("taskforge.api.get_current_user", mock_get_current_user)

        # Mock auth manager
        async def mock_verify_token(token):
            return mock_user.id

        mock_auth_mgr = AsyncMock()
        mock_auth_mgr.verify_token_async = mock_verify_token
        monkeypatch.setattr("taskforge.api.get_auth_manager", lambda: mock_auth_mgr)

        task_data = {
            "title": "API Test Task",
            "description": "Created via API",
            "priority": "high",
        }

        response = api_client.post("/tasks", json=task_data, headers=auth_headers)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["title"] == "API Test Task"
        assert response_data["priority"] == "high"

    def test_create_task_unauthorized(self, api_client):
        """Test task creation without authorization"""
        task_data = {"title": "Unauthorized Task", "description": "Should fail"}

        response = api_client.post("/tasks", json=task_data)
        assert response.status_code == 403  # Forbidden without auth

    def test_create_task_invalid_data(self, api_client, auth_headers, monkeypatch):
        """Test task creation with invalid data"""
        # Mock authentication
        mock_user = User.create_user("testuser", "test@example.com", "password")

        async def mock_get_current_user(credentials):
            return mock_user

        monkeypatch.setattr("taskforge.api.get_current_user", mock_get_current_user)

        # Missing required title
        task_data = {"description": "No title provided"}

        response = api_client.post("/tasks", json=task_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_list_tasks(self, api_client, auth_headers, monkeypatch):
        """Test task listing via API"""
        # Mock the task manager
        mock_manager = AsyncMock()
        mock_tasks = [
            Task(title="Task 1", priority=TaskPriority.HIGH),
            Task(title="Task 2", priority=TaskPriority.LOW),
        ]
        mock_manager.search_tasks.return_value = mock_tasks

        monkeypatch.setattr("taskforge.api.get_manager", lambda: mock_manager)

        # Mock authentication
        mock_user = User.create_user("testuser", "test@example.com", "password")

        async def mock_get_current_user(credentials):
            return mock_user

        monkeypatch.setattr("taskforge.api.get_current_user", mock_get_current_user)

        response = api_client.get("/tasks", headers=auth_headers)
        assert response.status_code == 200

        response_data = response.json()
        assert len(response_data) == 2
        assert response_data[0]["title"] == "Task 1"
        assert response_data[1]["title"] == "Task 2"

    @pytest.mark.asyncio
    async def test_list_tasks_with_filters(self, api_client, auth_headers, monkeypatch):
        """Test task listing with query filters"""
        mock_manager = AsyncMock()
        mock_tasks = [Task(title="High Priority Task", priority=TaskPriority.HIGH)]
        mock_manager.search_tasks.return_value = mock_tasks

        monkeypatch.setattr("taskforge.api.get_manager", lambda: mock_manager)

        # Mock authentication
        mock_user = User.create_user("testuser", "test@example.com", "password")

        async def mock_get_current_user(credentials):
            return mock_user

        monkeypatch.setattr("taskforge.api.get_current_user", mock_get_current_user)

        response = api_client.get(
            "/tasks?priority=high&status=todo&limit=10", headers=auth_headers
        )
        assert response.status_code == 200

        # Verify search_tasks was called with correct parameters
        mock_manager.search_tasks.assert_called_once()
        call_args = mock_manager.search_tasks.call_args[0][0]  # TaskQuery object
        assert TaskPriority.HIGH in call_args.priority
        assert TaskStatus.TODO in call_args.status
        assert call_args.limit == 10

    @pytest.mark.asyncio
    async def test_get_task_by_id(self, api_client, auth_headers, monkeypatch):
        """Test retrieving specific task by ID"""
        mock_manager = AsyncMock()
        mock_task = Task(title="Specific Task", priority=TaskPriority.MEDIUM)
        mock_manager.get_task.return_value = mock_task

        monkeypatch.setattr("taskforge.api.get_manager", lambda: mock_manager)

        # Mock authentication
        mock_user = User.create_user("testuser", "test@example.com", "password")

        async def mock_get_current_user(credentials):
            return mock_user

        monkeypatch.setattr("taskforge.api.get_current_user", mock_get_current_user)

        task_id = "test-task-id"
        response = api_client.get(f"/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["title"] == "Specific Task"

    def test_get_nonexistent_task(self, api_client, auth_headers, monkeypatch):
        """Test retrieving non-existent task"""
        mock_manager = AsyncMock()
        mock_manager.get_task.return_value = None

        monkeypatch.setattr("taskforge.api.get_manager", lambda: mock_manager)

        # Mock authentication
        mock_user = User.create_user("testuser", "test@example.com", "password")

        async def mock_get_current_user(credentials):
            return mock_user

        monkeypatch.setattr("taskforge.api.get_current_user", mock_get_current_user)

        response = api_client.get("/tasks/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_task(self, api_client, auth_headers, monkeypatch):
        """Test task updates via API"""
        mock_manager = AsyncMock()
        updated_task = Task(
            title="Updated Task",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
        )
        mock_manager.update_task.return_value = updated_task

        monkeypatch.setattr("taskforge.api.get_manager", lambda: mock_manager)

        # Mock authentication
        mock_user = User.create_user("testuser", "test@example.com", "password")

        async def mock_get_current_user(credentials):
            return mock_user

        monkeypatch.setattr("taskforge.api.get_current_user", mock_get_current_user)

        update_data = {"title": "Updated Task", "status": "in_progress", "progress": 50}

        task_id = "test-task-id"
        response = api_client.patch(
            f"/tasks/{task_id}", json=update_data, headers=auth_headers
        )
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["title"] == "Updated Task"
        assert response_data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_delete_task(self, api_client, auth_headers, monkeypatch):
        """Test task deletion via API"""
        mock_manager = AsyncMock()
        mock_manager.delete_task.return_value = True

        monkeypatch.setattr("taskforge.api.get_manager", lambda: mock_manager)

        # Mock authentication
        mock_user = User.create_user("testuser", "test@example.com", "password")

        async def mock_get_current_user(credentials):
            return mock_user

        monkeypatch.setattr("taskforge.api.get_current_user", mock_get_current_user)

        task_id = "test-task-id"
        response = api_client.delete(f"/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 200

        response_data = response.json()
        assert "deleted successfully" in response_data["message"]


class TestProjectAPI:
    """Integration tests for project API endpoints"""

    @pytest.mark.asyncio
    async def test_create_project(self, api_client, auth_headers, monkeypatch):
        """Test project creation via API"""
        from taskforge.core.project import Project

        mock_manager = AsyncMock()
        mock_project = Project(
            name="API Test Project", description="Created via API", owner_id="user-123"
        )
        mock_manager.create_project.return_value = mock_project

        monkeypatch.setattr("taskforge.api.get_manager", lambda: mock_manager)

        # Mock authentication
        mock_user = User.create_user("testuser", "test@example.com", "password")

        async def mock_get_current_user(credentials):
            return mock_user

        monkeypatch.setattr("taskforge.api.get_current_user", mock_get_current_user)

        project_data = {"name": "API Test Project", "description": "Created via API"}

        response = api_client.post("/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["name"] == "API Test Project"


class TestStatisticsAPI:
    """Integration tests for statistics API endpoints"""

    @pytest.mark.asyncio
    async def test_get_task_statistics(self, api_client, auth_headers, monkeypatch):
        """Test task statistics endpoint"""
        mock_manager = AsyncMock()
        mock_stats = {
            "total_tasks": 100,
            "completed_tasks": 75,
            "in_progress_tasks": 20,
            "completion_rate": 0.75,
        }
        mock_manager.get_task_statistics.return_value = mock_stats

        monkeypatch.setattr("taskforge.api.get_manager", lambda: mock_manager)

        # Mock authentication
        mock_user = User.create_user("testuser", "test@example.com", "password")

        async def mock_get_current_user(credentials):
            return mock_user

        monkeypatch.setattr("taskforge.api.get_current_user", mock_get_current_user)

        response = api_client.get("/stats/tasks", headers=auth_headers)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["total_tasks"] == 100
        assert response_data["completion_rate"] == 0.75

    @pytest.mark.asyncio
    async def test_get_productivity_metrics(
        self, api_client, auth_headers, monkeypatch
    ):
        """Test productivity metrics endpoint"""
        mock_manager = AsyncMock()
        mock_metrics = {
            "total_tasks": 50,
            "completed_tasks": 30,
            "completion_rate": 0.6,
            "avg_completion_time": 2.5,
        }
        mock_manager.get_productivity_metrics.return_value = mock_metrics

        monkeypatch.setattr("taskforge.api.get_manager", lambda: mock_manager)

        # Mock authentication
        mock_user = User.create_user("testuser", "test@example.com", "password")

        async def mock_get_current_user(credentials):
            return mock_user

        monkeypatch.setattr("taskforge.api.get_current_user", mock_get_current_user)

        response = api_client.get("/stats/productivity?days=30", headers=auth_headers)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["completion_rate"] == 0.6
        assert response_data["avg_completion_time"] == 2.5


class TestAuthenticationAPI:
    """Integration tests for authentication endpoints"""

    def test_user_registration(self, api_client, monkeypatch):
        """Test user registration endpoint"""
        mock_manager = AsyncMock()
        mock_auth_manager = AsyncMock()

        # Mock user creation
        mock_user = User.create_user("newuser", "new@example.com", "password123")
        mock_manager.storage.create_user.return_value = mock_user

        # Mock token creation
        mock_auth_manager.create_token.return_value = "test-access-token"

        monkeypatch.setattr("taskforge.api.get_manager", lambda: mock_manager)
        monkeypatch.setattr("taskforge.api.get_auth_manager", lambda: mock_auth_manager)

        user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123",
            "full_name": "New User",
        }

        response = api_client.post("/auth/register", json=user_data)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["access_token"] == "test-access-token"
        assert response_data["token_type"] == "bearer"
