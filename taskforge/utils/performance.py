"""
Performance monitoring and optimization utilities
"""

import asyncio
import time
from contextlib import asynccontextmanager
from functools import wraps
from types import TracebackType
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Type

# Performance metrics storage
_metrics: Dict[str, List[float]] = {}


def _summarize_metrics(
    metrics: Dict[str, List[float]], name: Optional[str] = None
) -> Dict[str, Dict[str, float]]:
    """Build summary statistics for metric samples."""
    data = {name: metrics.get(name, [])} if name else metrics

    stats: Dict[str, Dict[str, float]] = {}
    for metric_name, values in data.items():
        if values:
            stats[metric_name] = {
                "count": float(len(values)),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "last": values[-1],
            }
        else:
            stats[metric_name] = {
                "count": 0.0,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "last": 0.0,
            }

    return stats


class PerformanceTimer:
    """Context manager for timing operations"""

    def __init__(self, name: str):
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self) -> "PerformanceTimer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.end_time = time.perf_counter()
        if self.start_time is None:
            return
        duration = self.end_time - self.start_time
        record_metric(self.name, duration)

    @property
    def duration(self) -> Optional[float]:
        if self.start_time is not None and self.end_time is not None:
            return self.end_time - self.start_time
        return None


def record_metric(name: str, value: float) -> None:
    """Record a performance metric"""
    if name not in _metrics:
        _metrics[name] = []
    _metrics[name].append(value)


def get_metrics(name: Optional[str] = None) -> Dict[str, Dict[str, float]]:
    """Get performance metrics statistics"""
    return _summarize_metrics(_metrics, name)


def clear_metrics(name: Optional[str] = None) -> None:
    """Clear performance metrics"""
    if name:
        _metrics.pop(name, None)
    else:
        _metrics.clear()


def time_function(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to time function execution"""
    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                duration = end_time - start_time
                record_metric(f"{func.__module__}.{func.__name__}", duration)

        return async_wrapper
    else:

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                duration = end_time - start_time
                record_metric(f"{func.__module__}.{func.__name__}", duration)

        return sync_wrapper


@asynccontextmanager
async def async_timer(name: str) -> AsyncIterator[None]:
    """Async context manager for timing operations"""
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        duration = end_time - start_time
        record_metric(name, duration)


class PerformanceMonitor:
    """Performance monitoring class for tracking operations"""

    def __init__(self) -> None:
        self.metrics: Dict[str, List[float]] = {}

    def record(self, name: str, value: float) -> None:
        """Record a metric"""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)

    def get_stats(self, name: Optional[str] = None) -> Dict[str, Dict[str, float]]:
        """Get statistics for metrics"""
        if name:
            data = {name: self.metrics.get(name, [])}
        else:
            data = self.metrics

        return _summarize_metrics(self.metrics, name)

    def reset(self) -> None:
        """Reset all metrics"""
        self.metrics.clear()
