"""
PostgreSQL storage backend
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import asyncpg
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from taskforge.core.manager import TaskQuery
from taskforge.core.project import Project
from taskforge.core.task import Task, TaskPriority, TaskStatus
from taskforge.core.user import User
from taskforge.storage.base import StorageBackend
from taskforge.storage.models import Base, ProjectModel, TaskModel, UserModel


class PostgreSQLStorage(StorageBackend):
    """PostgreSQL storage implementation using SQLAlchemy"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None

    async def initialize(self) -> None:
        """Initialize the storage backend"""
        self.engine = create_async_engine(
            self.database_url, echo=False, pool_size=10, max_overflow=20
        )

        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def cleanup(self) -> None:
        """Cleanup and close connections"""
        if self.engine:
            await self.engine.dispose()

    async def _get_session(self) -> AsyncSession:
        """Get a database session"""
        return self.session_factory()

    # Task operations
    async def create_task(self, task: Task) -> Task:
        """Create a new task"""
        async with self._get_session() as session:
            task_model = TaskModel.from_task(task)
            session.add(task_model)

            try:
                await session.commit()
                await session.refresh(task_model)
                return task_model.to_task()
            except IntegrityError:
                await session.rollback()
                raise ValueError(f"Task with ID {task.id} already exists")

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        async with self._get_session() as session:
            result = await session.execute(
                select(TaskModel).where(TaskModel.id == task_id)
            )
            task_model = result.scalar_one_or_none()
            return task_model.to_task() if task_model else None

    async def update_task(self, task: Task) -> Task:
        """Update an existing task"""
        async with self._get_session() as session:
            task.updated_at = datetime.now(timezone.utc)

            stmt = (
                update(TaskModel)
                .where(TaskModel.id == task.id)
                .values(**TaskModel.from_task(task).to_dict())
            )

            result = await session.execute(stmt)

            if result.rowcount == 0:
                raise ValueError(f"Task {task.id} not found")

            await session.commit()
            return task

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        async with self._get_session() as session:
            stmt = delete(TaskModel).where(TaskModel.id == task_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def search_tasks(self, query: TaskQuery, user_id: str) -> List[Task]:
        """Search tasks with filtering"""
        async with self._get_session() as session:
            stmt = select(TaskModel)
            conditions = []

            # Apply filters
            if query.status:
                conditions.append(TaskModel.status.in_([s.value for s in query.status]))

            if query.priority:
                conditions.append(
                    TaskModel.priority.in_([p.value for p in query.priority])
                )

            if query.assigned_to:
                conditions.append(TaskModel.assigned_to == query.assigned_to)

            if query.project_id:
                conditions.append(TaskModel.project_id == query.project_id)

            if query.created_after:
                conditions.append(TaskModel.created_at >= query.created_after)

            if query.created_before:
                conditions.append(TaskModel.created_at <= query.created_before)

            if query.due_after:
                conditions.append(TaskModel.due_date >= query.due_after)

            if query.due_before:
                conditions.append(TaskModel.due_date <= query.due_before)

            if query.search_text:
                search_pattern = f"%{query.search_text}%"
                conditions.append(
                    or_(
                        TaskModel.title.ilike(search_pattern),
                        TaskModel.description.ilike(search_pattern),
                    )
                )

            if conditions:
                stmt = stmt.where(and_(*conditions))

            # Order by creation date (newest first)
            stmt = stmt.order_by(TaskModel.created_at.desc())

            # Apply pagination
            stmt = stmt.offset(query.offset).limit(query.limit)

            result = await session.execute(stmt)
            task_models = result.scalars().all()

            return [task_model.to_task() for task_model in task_models]

    # Project operations
    async def create_project(self, project: Project) -> Project:
        """Create a new project"""
        async with self._get_session() as session:
            project_model = ProjectModel.from_project(project)
            session.add(project_model)

            try:
                await session.commit()
                await session.refresh(project_model)
                return project_model.to_project()
            except IntegrityError:
                await session.rollback()
                raise ValueError(f"Project with ID {project.id} already exists")

    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID"""
        async with self._get_session() as session:
            result = await session.execute(
                select(ProjectModel).where(ProjectModel.id == project_id)
            )
            project_model = result.scalar_one_or_none()
            return project_model.to_project() if project_model else None

    async def update_project(self, project: Project) -> Project:
        """Update an existing project"""
        async with self._get_session() as session:
            project.updated_at = datetime.now(timezone.utc)

            stmt = (
                update(ProjectModel)
                .where(ProjectModel.id == project.id)
                .values(**ProjectModel.from_project(project).to_dict())
            )

            result = await session.execute(stmt)

            if result.rowcount == 0:
                raise ValueError(f"Project {project.id} not found")

            await session.commit()
            return project

    async def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        async with self._get_session() as session:
            stmt = delete(ProjectModel).where(ProjectModel.id == project_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def get_user_projects(self, user_id: str) -> List[Project]:
        """Get all projects for a user"""
        async with self._get_session() as session:
            stmt = select(ProjectModel).where(
                or_(
                    ProjectModel.owner_id == user_id,
                    ProjectModel.team_members.contains([user_id]),
                )
            )

            result = await session.execute(stmt)
            project_models = result.scalars().all()

            return [project_model.to_project() for project_model in project_models]

    # User operations
    async def create_user(self, user: User) -> User:
        """Create a new user"""
        async with self._get_session() as session:
            user_model = UserModel.from_user(user)
            session.add(user_model)

            try:
                await session.commit()
                await session.refresh(user_model)
                return user_model.to_user()
            except IntegrityError:
                await session.rollback()
                raise ValueError(
                    f"User with username {user.username} or email {user.email} already exists"
                )

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        async with self._get_session() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user_model = result.scalar_one_or_none()
            return user_model.to_user() if user_model else None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        async with self._get_session() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.username == username)
            )
            user_model = result.scalar_one_or_none()
            return user_model.to_user() if user_model else None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        async with self._get_session() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            user_model = result.scalar_one_or_none()
            return user_model.to_user() if user_model else None

    async def update_user(self, user: User) -> User:
        """Update an existing user"""
        async with self._get_session() as session:
            user.updated_at = datetime.now(timezone.utc)

            stmt = (
                update(UserModel)
                .where(UserModel.id == user.id)
                .values(**UserModel.from_user(user).to_dict())
            )

            result = await session.execute(stmt)

            if result.rowcount == 0:
                raise ValueError(f"User {user.id} not found")

            await session.commit()
            return user

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        async with self._get_session() as session:
            stmt = delete(UserModel).where(UserModel.id == user_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    # Statistics and analytics
    async def get_task_statistics(
        self, project_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get task statistics"""
        async with self._get_session() as session:
            base_query = select(TaskModel)
            conditions = []

            if project_id:
                conditions.append(TaskModel.project_id == project_id)

            if user_id:
                conditions.append(TaskModel.assigned_to == user_id)

            if conditions:
                base_query = base_query.where(and_(*conditions))

            # Total tasks
            total_result = await session.execute(
                select(func.count()).select_from(base_query.subquery())
            )
            total_tasks = total_result.scalar()

            # Completed tasks
            completed_query = base_query.where(
                TaskModel.status == TaskStatus.DONE.value
            )
            completed_result = await session.execute(
                select(func.count()).select_from(completed_query.subquery())
            )
            completed_tasks = completed_result.scalar()

            # In progress tasks
            in_progress_query = base_query.where(
                TaskModel.status == TaskStatus.IN_PROGRESS.value
            )
            in_progress_result = await session.execute(
                select(func.count()).select_from(in_progress_query.subquery())
            )
            in_progress_tasks = in_progress_result.scalar()

            # Overdue tasks
            overdue_query = base_query.where(
                and_(
                    TaskModel.due_date < datetime.now(timezone.utc),
                    TaskModel.status.notin_(
                        [TaskStatus.DONE.value, TaskStatus.CANCELLED.value]
                    ),
                )
            )
            overdue_result = await session.execute(
                select(func.count()).select_from(overdue_query.subquery())
            )
            overdue_tasks = overdue_result.scalar()

            completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0

            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "overdue_tasks": overdue_tasks,
                "completion_rate": completion_rate,
            }

    # Bulk operations (optimized for PostgreSQL)
    async def bulk_create_tasks(self, tasks: List[Task]) -> List[Task]:
        """Create multiple tasks efficiently"""
        async with self._get_session() as session:
            task_models = [TaskModel.from_task(task) for task in tasks]
            session.add_all(task_models)

            try:
                await session.commit()
                # Refresh all models to get generated IDs
                for task_model in task_models:
                    await session.refresh(task_model)

                return [task_model.to_task() for task_model in task_models]
            except IntegrityError:
                await session.rollback()
                raise ValueError("One or more tasks already exist")

    async def bulk_update_tasks(self, tasks: List[Task]) -> List[Task]:
        """Update multiple tasks efficiently"""
        async with self._get_session() as session:
            for task in tasks:
                task.updated_at = datetime.now(timezone.utc)
                stmt = (
                    update(TaskModel)
                    .where(TaskModel.id == task.id)
                    .values(**TaskModel.from_task(task).to_dict())
                )
                await session.execute(stmt)

            await session.commit()
            return tasks
