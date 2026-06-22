import pytest

from taskforge.utils.performance import (
    PerformanceMonitor,
    PerformanceTimer,
    async_timer,
    clear_metrics,
    get_metrics,
)


def test_performance_monitor_reports_instance_metrics_only():
    clear_metrics()
    monitor = PerformanceMonitor()
    monitor.record("operation", 0.2)
    monitor.record("operation", 0.4)

    global_stats = get_metrics("operation")
    instance_stats = monitor.get_stats("operation")

    assert global_stats["operation"]["count"] == 0
    assert instance_stats["operation"]["count"] == 2
    assert instance_stats["operation"]["avg"] == pytest.approx(0.3)
    assert instance_stats["operation"]["last"] == 0.4


def test_performance_timer_duration_handles_zero_start_time():
    timer = PerformanceTimer("manual")
    timer.start_time = 0.0
    timer.end_time = 0.5

    assert timer.duration == 0.5


@pytest.mark.asyncio
async def test_async_timer_records_global_metric():
    clear_metrics("async-operation")

    async with async_timer("async-operation"):
        pass

    stats = get_metrics("async-operation")
    assert stats["async-operation"]["count"] == 1
    assert stats["async-operation"]["last"] >= 0
