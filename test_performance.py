"""
Quick performance test to verify the optimizations work
快速验证性能优化效果的测试脚本
"""

import asyncio
import time
from pathlib import Path
import shutil

from taskforge.core.task import Task, TaskStatus, TaskPriority
from taskforge.core.queries import TaskQuery
from taskforge.storage.json_storage import JSONStorage
from taskforge.storage.optimized_storage import OptimizedJSONStorage


async def quick_performance_test():
    """快速性能验证测试"""
    print("TaskForge 性能优化验证测试")
    print("=" * 50)

    # 创建测试数据
    tasks = []
    for i in range(1000):
        task = Task(
            id=f"task-{i}",
            title=f"Test Task {i}",
            description=f"Description for task {i}",
            status=list(TaskStatus)[i % len(TaskStatus)],
            priority=list(TaskPriority)[i % len(TaskPriority)],
            project_id=f"project-{i % 10}",
            assigned_to=f"user-{i % 5}",
            tags={f"tag-{j}" for j in range(i % 3)},
        )
        tasks.append(task)

    print(f"创建了 {len(tasks)} 个测试任务")

    # 测试优化存储
    print("\n测试优化存储...")
    opt_storage = OptimizedJSONStorage("./test_optimized", save_delay=0.1)

    try:
        await opt_storage.initialize()

        # 测试批量创建
        start_time = time.perf_counter()
        for task in tasks:
            await opt_storage.create_task(task)
        create_time = time.perf_counter() - start_time

        print(f"   创建 {len(tasks)} 任务: {create_time:.3f}秒")

        # 测试查询性能
        query = TaskQuery(status=[TaskStatus.IN_PROGRESS])
        start_time = time.perf_counter()
        results = await opt_storage.search_tasks(query, "user-1")
        search_time = time.perf_counter() - start_time

        print(f"   状态查询找到 {len(results)} 个任务: {search_time*1000:.2f}ms")

        # 测试缓存效果
        start_time = time.perf_counter()
        results2 = await opt_storage.search_tasks(query, "user-1")
        cache_time = time.perf_counter() - start_time

        print(f"   缓存查询: {cache_time*1000:.2f}ms")
        if cache_time > 0:
            speedup = search_time / cache_time
            print(f"   缓存加速: {speedup:.1f}x")

        # 显示统计
        cache_stats = await opt_storage.get_cache_stats()
        index_stats = opt_storage.get_index_statistics()

        print(f"\n性能统计:")
        print(f"   缓存命中率: {cache_stats['hit_rate']*100:.1f}%")
        print(f"   索引大小: {index_stats['status_index_size']} 个状态索引")
        print(f"   延迟写入: {'启用' if opt_storage.is_dirty() else '空闲'}")

        await opt_storage.force_save()  # 确保存盘
        print("   数据已保存")

    finally:
        await opt_storage.cleanup()
        if Path("./test_optimized").exists():
            shutil.rmtree("./test_optimized")

    print("\n性能优化验证完成!")
    print("\n主要优化特性:")
    print("   延迟写入机制 - 批量磁盘I/O")
    print("   多级索引系统 - 快速查询")
    print("   智能缓存 - 重复查询加速")
    print("   异步处理 - 并发优化")
    print("   批量操作 - 高效数据处理")


if __name__ == "__main__":
    asyncio.run(quick_performance_test())