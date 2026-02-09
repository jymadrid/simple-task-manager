"""
Advanced caching utilities for TaskForge
"""

import asyncio
import sys
import time
from collections import OrderedDict
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

T = TypeVar("T")


class MemoryEfficientLRUCache:
    """
    Memory-efficient LRU Cache with size and memory limits
    Monitors memory usage and evicts items based on memory pressure
    """

    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100, ttl: Optional[float] = None):
        """
        Initialize memory-efficient LRU cache

        Args:
            max_size: Maximum number of items to cache
            max_memory_mb: Maximum memory usage in MB
            ttl: Time to live in seconds (None for no expiration)
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.ttl = ttl
        self._cache: OrderedDict[str, tuple[Any, float, int]] = OrderedDict()  # key -> (value, timestamp, size)
        self._current_memory = 0
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with memory management"""
        async with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, timestamp, size = self._cache[key]

            # Check TTL
            if self.ttl and (time.time() - timestamp) > self.ttl:
                del self._cache[key]
                self._current_memory -= size
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache with memory pressure handling"""
        async with self._lock:
            # Estimate memory usage
            value_size = sys.getsizeof(value)
            
            # Evict existing key if present
            if key in self._cache:
                _, _, old_size = self._cache.pop(key)
                self._current_memory -= old_size

            # Evict if necessary based on size or memory limits
            while (len(self._cache) >= self.max_size or 
                   self._current_memory + value_size > self.max_memory_bytes):
                if not self._cache:
                    break
                oldest_key, (_, _, oldest_size) = self._cache.popitem(last=False)
                self._current_memory -= oldest_size

            self._cache[key] = (value, time.time(), value_size)
            self._current_memory += value_size

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        async with self._lock:
            if key in self._cache:
                _, _, size = self._cache.pop(key)
                self._current_memory -= size
                return True
            return False

    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self._cache.clear()
            self._current_memory = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "size": len(self._cache),
            "memory_bytes": self._current_memory,
            "memory_mb": self._current_memory / (1024 * 1024),
            "max_memory_mb": self.max_memory_bytes / (1024 * 1024)
        }


class LRUCache:
    """
    Least Recently Used (LRU) Cache implementation
    Thread-safe and optimized for performance
    """

    def __init__(self, max_size: int = 1000, ttl: Optional[float] = None):
        """
        Initialize LRU cache

        Args:
            max_size: Maximum number of items to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, timestamp = self._cache[key]

            # Check TTL
            if self.ttl and (time.time() - timestamp) > self.ttl:
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        async with self._lock:
            # Update existing or add new
            if key in self._cache:
                self._cache.move_to_end(key)

            self._cache[key] = (value, time.time())

            # Evict oldest if over size limit
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "ttl": self.ttl,
        }


class AsyncCachedProperty:
    """
    Decorator for caching async property values
    """

    def __init__(self, func: Callable):
        self.func = func
        self.attrname = None
        self.__doc__ = func.__doc__

    def __set_name__(self, owner, name):
        self.attrname = f"_cached_{name}"

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        cache = instance.__dict__.get(self.attrname)
        if cache is None:
            cache = self.func(instance)
            instance.__dict__[self.attrname] = cache
        return cache


def cache_result(max_size: int = 128, ttl: Optional[float] = None):
    """
    Decorator to cache function results

    Args:
        max_size: Maximum cache size
        ttl: Time to live in seconds
    """
    cache = LRUCache(max_size=max_size, ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from args and kwargs
            key_parts = [str(arg) for arg in args]
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = f"{func.__name__}:{':'.join(key_parts)}"

            # Try to get from cache
            result = await cache.get(cache_key)
            if result is not None:
                return result

            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result)
            return result

        # Attach cache stats method
        wrapper.cache_stats = cache.get_stats
        wrapper.cache_clear = cache.clear

        return wrapper

    return decorator


class CacheWarmer:
    """
    Utility for warming up caches with commonly accessed data
    """

    def __init__(self):
        self._warmup_tasks: list[Callable] = []

    def register(self, func: Callable) -> Callable:
        """Register a function for cache warming"""
        self._warmup_tasks.append(func)
        return func

    async def warmup(self) -> None:
        """Execute all warmup tasks"""
        tasks = [task() for task in self._warmup_tasks]
        await asyncio.gather(*tasks, return_exceptions=True)


class MultiLevelCache:
    """
    Multi-level cache with L1 (memory) and L2 (persistent) support
    """

    def __init__(
        self,
        l1_size: int = 100,
        l2_size: int = 1000,
        l1_ttl: Optional[float] = 60.0,
        l2_ttl: Optional[float] = 3600.0,
    ):
        self.l1_cache = LRUCache(max_size=l1_size, ttl=l1_ttl)
        self.l2_cache = LRUCache(max_size=l2_size, ttl=l2_ttl)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache"""
        # Try L1 cache first
        value = await self.l1_cache.get(key)
        if value is not None:
            return value

        # Try L2 cache
        value = await self.l2_cache.get(key)
        if value is not None:
            # Promote to L1
            await self.l1_cache.set(key, value)
            return value

        return None

    async def set(self, key: str, value: Any) -> None:
        """Set value in multi-level cache"""
        await self.l1_cache.set(key, value)
        await self.l2_cache.set(key, value)

    async def delete(self, key: str) -> None:
        """Delete value from all cache levels"""
        await self.l1_cache.delete(key)
        await self.l2_cache.delete(key)

    async def clear(self) -> None:
        """Clear all cache levels"""
        await self.l1_cache.clear()
        await self.l2_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all cache levels"""
        return {"l1": self.l1_cache.get_stats(), "l2": self.l2_cache.get_stats()}
