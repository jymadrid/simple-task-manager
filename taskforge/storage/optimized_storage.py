"""
Optimized storage layer with advanced caching integration
"""

from typing import Any, Dict, List, Optional

from taskforge.core.project import Project
from taskforge.core.queries import TaskQuery
from taskforge.core.task import Task
from taskforge.core.user import User
from taskforge.storage.json_storage import JSONStorage
from taskforge.utils.cache import MultiLevelCache, cache_result


class OptimizedJSONStorage(JSONStorage):
    """
    Extended JSON storage with integrated caching for maximum performance
    """

    def __init__(self, data_directory: str = "./data", save_delay: float = 0.5):
        super().__init__(data_directory, save_delay)

        # Multi-level cache for frequently accessed data
        self._query_cache = MultiLevelCache(
            l1_size=200,  # L1: 200 most recent queries
            l2_size=1000,  # L2: 1000 total queries
            l1_ttl=300.0,  # L1: 5 minutes
            l2_ttl=3600.0,  # L2: 1 hour
        )

    @cache_result(max_size=500, ttl=600)  # Cache 500 results for 10 minutes
    async def search_tasks_cached(self, query: TaskQuery, user_id: str) -> List[Task]:
        """
        Cached version of search_tasks using cache_result decorator
        """
        return await super().search_tasks(query, user_id)

    async def search_tasks(self, query: TaskQuery, user_id: str) -> List[Task]:
        """
        Search tasks with multi-level caching
        """
        # Create cache key from query
        query_key = self._create_query_cache_key(query, user_id)

        # Try L1/L2 cache first
        cached_result = await self._query_cache.get(query_key)
        if cached_result is not None:
            return cached_result

        # Cache miss - use parent's optimized search
        result = await super().search_tasks(query, user_id)

        # Cache the result
        await self._query_cache.set(query_key, result)

        return result

    def _create_query_cache_key(self, query: TaskQuery, user_id: str) -> str:
        """Create a unique cache key for a query"""
        key_parts = [
            f"user={user_id}",
            f"status={','.join([s.value for s in (query.status or [])])}",
            f"priority={','.join([p.value for p in (query.priority or [])])}",
            f"assigned={query.assigned_to or 'none'}",
            f"project={query.project_id or 'none'}",
            f"tags={','.join(query.tags or [])}",
            f"limit={query.limit}",
            f"offset={query.offset}",
        ]

        if query.search_text:
            key_parts.append(f"search={query.search_text}")

        return "search:" + ":".join(key_parts)

    @cache_result(max_size=1000, ttl=1800)  # Cache 1000 tasks for 30 minutes
    async def get_task_cached(self, task_id: str) -> Optional[Task]:
        """Cached version of get_task"""
        return await super().get_task(task_id)

    @cache_result(max_size=500, ttl=1800)  # Cache 500 projects for 30 minutes
    async def get_project_cached(self, project_id: str) -> Optional[Project]:
        """Cached version of get_project"""
        return await super().get_project(project_id)

    async def invalidate_caches(self) -> None:
        """Invalidate all caches when data changes"""
        await self._query_cache.clear()

    async def create_task(self, task: Task) -> Task:
        """Create task and invalidate relevant caches"""
        result = await super().create_task(task)
        await self.invalidate_caches()
        return result

    async def update_task(self, task: Task) -> Task:
        """Update task and invalidate relevant caches"""
        result = await super().update_task(task)
        await self.invalidate_caches()
        return result

    async def delete_task(self, task_id: str) -> bool:
        """Delete task and invalidate relevant caches"""
        result = await super().delete_task(task_id)
        await self.invalidate_caches()
        return result

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        base_stats = super().get_cache_statistics()

        # Add multi-level cache stats
        ml_cache_stats = self._query_cache.get_stats()

        return {
            **base_stats,
            "multi_level_cache": ml_cache_stats,
        }

    async def cleanup(self) -> None:
        """Cleanup with cache clearing"""
        await self.invalidate_caches()
        await super().cleanup()


# Factory function for easy instantiation
def create_optimized_storage(
    data_directory: str = "./data", save_delay: float = 0.5
) -> OptimizedJSONStorage:
    """
    Factory function to create an optimized storage instance

    Args:
        data_directory: Directory for JSON files
        save_delay: Delay in seconds for batch writes

    Returns:
        OptimizedJSONStorage instance
    """
    return OptimizedJSONStorage(data_directory, save_delay)
