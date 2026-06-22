import asyncio

import pytest

from taskforge.utils.cache import CacheWarmer, MultiLevelCache, cache_result


@pytest.mark.asyncio
async def test_cache_result_exposes_stats_and_clear_helpers():
    calls = 0

    @cache_result(max_size=2)
    async def load_value(key: str) -> str:
        nonlocal calls
        calls += 1
        return f"value:{key}"

    assert await load_value("a") == "value:a"
    assert await load_value("a") == "value:a"
    assert calls == 1

    stats = load_value.cache_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1

    await load_value.cache_clear()
    assert await load_value("a") == "value:a"
    assert calls == 2


@pytest.mark.asyncio
async def test_multi_level_cache_promotes_l2_hits_to_l1():
    cache = MultiLevelCache(l1_size=1, l2_size=2, l1_ttl=None, l2_ttl=None)

    await cache.l2_cache.set("task", {"id": "task-1"})

    assert await cache.get("task") == {"id": "task-1"}
    assert await cache.l1_cache.get("task") == {"id": "task-1"}

    await cache.clear()
    assert await cache.get("task") is None


@pytest.mark.asyncio
async def test_cache_warmer_runs_registered_async_tasks():
    warmer = CacheWarmer()
    warmed = []

    @warmer.register
    async def warm_task() -> None:
        await asyncio.sleep(0)
        warmed.append("done")

    await warmer.warmup()

    assert warmed == ["done"]
