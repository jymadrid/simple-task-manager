"""
Performance monitoring and optimization utilities
"""

import asyncio
import time
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Callable, Dict, Optional

# Performance metrics storage
_metrics: Dict[str, list] = {}


class PerformanceTimer:
    """Context manager for timing operations"""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration = self.end_time - self.start_time
        record_metric(self.name, duration)

    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


def record_metric(name: str, value: float) -> None:
    """Record a performance metric"""
    if name not in _metrics:
        _metrics[name] = []
    _metrics[name].append(value)


def get_metrics(name: Optional[str] = None) -> Dict[str, Dict[str, float]]:
    """Get performance metrics statistics"""
    if name:
        data = {name: _metrics.get(name, [])}
    else:
        data = _metrics

    stats = {}
    for metric_name, values in data.items():
        if values:
            stats[metric_name] = {
                'count': len(values),
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'last': values[-1]
            }
        else:
            stats[metric_name] = {
                'count': 0,
                'avg': 0.0,
                'min': 0.0,
                'max': 0.0,
                'last': 0.0
            }

    return stats


def clear_metrics(name: Optional[str] = None) -> None:
    """Clear performance metrics"""
    if name:
        _metrics.pop(name, None)
    else:
        _metrics.clear()


def time_function(func: Callable) -> Callable:
    """Decorator to time function execution"""
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
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
        def sync_wrapper(*args, **kwargs):
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
async def async_timer(name: str):
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

    def __init__(self):
        self.metrics: Dict[str, list] = {}

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

        return get_metrics() if name is None else get_metrics(name)

    def reset(self) -> None:
        """Reset all metrics"""
        self.metrics.clear()