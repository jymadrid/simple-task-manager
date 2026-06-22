import pytest

import taskforge.storage as storage_package
from taskforge.core.project import Project
from taskforge.core.queries import TaskQuery
from taskforge.core.task import Task, TaskPriority, TaskStatus
from taskforge.core.user import User
from taskforge.storage.base import StorageBackend
from taskforge.storage.json_storage import JSONStorage
from taskforge.storage.simple_json_storage import SimpleJSONStorage
from taskforge.storage.simple_postgresql_storage import SimplePostgreSQLStorage


def test_storage_package_exports_are_stable():
    assert storage_package.JSONStorage is JSONStorage
    assert storage_package.JsonStorage is JSONStorage
    assert storage_package.StorageBackend is StorageBackend
    assert storage_package.__all__.count("PostgreSQLStorage") == 1
    assert storage_package.PostgreSQLStorage is not None
    assert SimpleJSONStorage("data").data_dir
    assert SimplePostgreSQLStorage("postgresql://example").database_url


@pytest.mark.asyncio
async def test_postgresql_fallback_storage_implements_backend_contract():
    storage = storage_package.PostgreSQLStorage("postgresql://example")

    assert isinstance(storage, StorageBackend)

    user = User.create_user("pguser", "pguser@example.com", "password")
    await storage.create_user(user)
    project = Project(name="Postgres Project", owner_id=user.id)
    await storage.create_project(project)
    task = Task(
        title="Postgres Task",
        description="Find me",
        status="done",
        priority="high",
        project_id=project.id,
        assigned_to=user.id,
    )
    await storage.create_task(task)

    assert await storage.get_user_by_username("pguser") == user
    assert await storage.get_user_by_email("pguser@example.com") == user
    assert await storage.get_user_projects(user.id) == [project]

    results = await storage.search_tasks(
        TaskQuery(
            status=[TaskStatus.DONE],
            priority=[TaskPriority.HIGH],
            assigned_to=user.id,
            search_text="find",
        ),
        user.id,
    )
    stats = await storage.get_task_statistics(project_id=project.id)

    assert results == [task]
    assert stats["completed_tasks"] == 1
    assert stats["in_progress_tasks"] == 0


@pytest.mark.asyncio
async def test_simple_json_storage_implements_backend_contract_and_persists(tmp_path):
    storage = SimpleJSONStorage(str(tmp_path))
    await storage.initialize()

    assert isinstance(storage, StorageBackend)

    user = User.create_user("jsonuser", "jsonuser@example.com", "password")
    await storage.create_user(user)
    project = Project(name="JSON Project", owner_id=user.id)
    await storage.create_project(project)
    task = Task(
        title="JSON Task",
        description="Find json",
        status="done",
        priority="high",
        project_id=project.id,
        assigned_to=user.id,
    )
    await storage.create_task(task)

    assert await storage.get_user_by_username("jsonuser") == user
    assert await storage.get_user_by_email("jsonuser@example.com") == user
    assert await storage.get_user_projects(user.id) == [project]

    results = await storage.search_tasks(
        TaskQuery(
            status=[TaskStatus.DONE],
            priority=[TaskPriority.HIGH],
            assigned_to=user.id,
            search_text="json",
        ),
        user.id,
    )
    stats = await storage.get_task_statistics(project_id=project.id)
    backup = await storage.export_data()

    reloaded = SimpleJSONStorage(str(tmp_path))
    await reloaded.initialize()
    imported = SimpleJSONStorage(str(tmp_path / "imported"))
    await imported.initialize()

    assert results == [task]
    assert stats["completed_tasks"] == 1
    assert await reloaded.get_user_by_username("jsonuser") is not None
    assert await reloaded.get_project(project.id) is not None
    assert await imported.import_data(backup)
    assert await imported.get_task(task.id) is not None


@pytest.mark.asyncio
async def test_simple_json_statistics_filter_by_assignee(tmp_path):
    storage = SimpleJSONStorage(str(tmp_path))
    await storage.initialize()

    user_one = User.create_user("jsonone", "jsonone@example.com", "password")
    user_two = User.create_user("jsontwo", "jsontwo@example.com", "password")

    await storage.create_task(
        Task(title="Done for one", status="done", assigned_to=user_one.id)
    )
    await storage.create_task(
        Task(
            title="Progress for one",
            status=TaskStatus.IN_PROGRESS,
            assigned_to=user_one.id,
        )
    )
    await storage.create_task(
        Task(title="Done for two", status="done", assigned_to=user_two.id)
    )

    stats = await storage.get_task_statistics(user_id=user_one.id)

    assert stats["total_tasks"] == 2
    assert stats["completed_tasks"] == 1
    assert stats["in_progress_tasks"] == 1
    assert stats["completion_rate"] == 0.5


@pytest.mark.asyncio
async def test_postgresql_fallback_statistics_filter_by_assignee():
    storage = storage_package.PostgreSQLStorage("postgresql://example")
    direct_storage = SimplePostgreSQLStorage("postgresql://example")

    for backend in (storage, direct_storage):
        user_one = User.create_user("pgone", "pgone@example.com", "password")
        user_two = User.create_user("pgtwo", "pgtwo@example.com", "password")

        await backend.create_task(
            Task(title="Done for one", status="done", assigned_to=user_one.id)
        )
        await backend.create_task(
            Task(
                title="Progress for one",
                status=TaskStatus.IN_PROGRESS,
                assigned_to=user_one.id,
            )
        )
        await backend.create_task(
            Task(title="Done for two", status="done", assigned_to=user_two.id)
        )

        stats = await backend.get_task_statistics(user_id=user_one.id)

        assert stats["total_tasks"] == 2
        assert stats["completed_tasks"] == 1
        assert stats["in_progress_tasks"] == 1
        assert stats["completion_rate"] == 0.5
