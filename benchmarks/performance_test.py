"""
Performance benchmarking script for TaskForge
测试优化前后的性能对比 - 包含最新的性能优化
"""

import asyncio
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import shutil
from typing import List
import statistics

from taskforge.core.task import Task, TaskStatus, TaskPriority
from taskforge.core.queries import TaskQuery
from taskforge.storage.json_storage import JSONStorage
from taskforge.storage.optimized_storage import OptimizedJSONStorage
from taskforge.utils.performance import get_metrics, clear_metrics


class PerformanceBenchmark:
    """性能基准测试"""

    def __init__(self, data_dir: str = "./benchmark_data"):
        self.data_dir = Path(data_dir)
        self.storage = None

    async def setup(self):
        """设置测试环境"""
        # 清理旧数据
        if self.data_dir.exists():
            shutil.rmtree(self.data_dir)

        # 初始化存储
        self.storage = JSONStorage(str(self.data_dir))
        await self.storage.initialize()
        clear_metrics()

    async def teardown(self):
        """清理测试环境"""
        if self.storage:
            await self.storage.cleanup()
        if self.data_dir.exists():
            shutil.rmtree(self.data_dir)

    def create_sample_tasks(self, count: int) -> List[Task]:
        """创建样本任务"""
        tasks = []
        statuses = list(TaskStatus)
        priorities = list(TaskPriority)

        for i in range(count):
            task = Task(
                title=f"Task {i}",
                description=f"Description for task {i}",
                status=statuses[i % len(statuses)],
                priority=priorities[i % len(priorities)],
                project_id=f"project-{i % 10}",
                assigned_to=f"user-{i % 5}",
                due_date=datetime.now(timezone.utc) + timedelta(days=i % 30)
            )
            tasks.append(task)

        return tasks

    async def benchmark_bulk_create(self, count: int = 1000):
        """测试批量创建性能"""
        print(f"\n📝 批量创建 {count} 个任务...")

        tasks = self.create_sample_tasks(count)

        start_time = time.perf_counter()
        await self.storage.bulk_create_tasks(tasks)
        end_time = time.perf_counter()

        duration = end_time - start_time
        rate = count / duration

        print(f"✅ 完成: {duration:.3f}秒")
        print(f"⚡ 速率: {rate:.1f} tasks/sec")

        return duration, rate

    async def benchmark_search_by_status(self):
        """测试按状态查询性能"""
        print(f"\n🔍 按状态查询...")

        query = TaskQuery(status=[TaskStatus.TODO, TaskStatus.IN_PROGRESS])

        start_time = time.perf_counter()
        results = await self.storage.search_tasks(query, "user-1")
        end_time = time.perf_counter()

        duration = end_time - start_time

        print(f"✅ 找到 {len(results)} 个任务")
        print(f"⚡ 用时: {duration*1000:.2f}ms")

        return duration, len(results)

    async def benchmark_search_by_project(self):
        """测试按项目查询性能"""
        print(f"\n📁 按项目查询...")

        query = TaskQuery(project_id="project-5")

        start_time = time.perf_counter()
        results = await self.storage.search_tasks(query, "user-1")
        end_time = time.perf_counter()

        duration = end_time - start_time

        print(f"✅ 找到 {len(results)} 个任务")
        print(f"⚡ 用时: {duration*1000:.2f}ms")

        return duration, len(results)

    async def benchmark_complex_query(self):
        """测试复合查询性能"""
        print(f"\n🔎 复合查询 (状态+优先级+项目)...")

        query = TaskQuery(
            status=[TaskStatus.TODO],
            priority=[TaskPriority.HIGH, TaskPriority.CRITICAL],
            project_id="project-3"
        )

        start_time = time.perf_counter()
        results = await self.storage.search_tasks(query, "user-1")
        end_time = time.perf_counter()

        duration = end_time - start_time

        print(f"✅ 找到 {len(results)} 个任务")
        print(f"⚡ 用时: {duration*1000:.2f}ms")

        return duration, len(results)

    async def benchmark_bulk_update(self, count: int = 500):
        """测试批量更新性能"""
        print(f"\n✏️ 批量更新 {count} 个任务...")

        # 获取要更新的任务
        query = TaskQuery(limit=count)
        tasks = await self.storage.search_tasks(query, "user-1")

        # 更新状态
        for task in tasks:
            task.status = TaskStatus.DONE

        start_time = time.perf_counter()
        await self.storage.bulk_update_tasks(tasks)
        end_time = time.perf_counter()

        duration = end_time - start_time
        rate = count / duration

        print(f"✅ 完成: {duration:.3f}秒")
        print(f"⚡ 速率: {rate:.1f} updates/sec")

        return duration, rate

    async def benchmark_statistics(self):
        """测试统计查询性能"""
        print(f"\n📊 统计查询...")

        start_time = time.perf_counter()
        stats = await self.storage.get_task_statistics()
        end_time = time.perf_counter()

        duration = end_time - start_time

        print(f"✅ 统计完成")
        print(f"   - 总任务数: {stats['total_tasks']}")
        print(f"   - 完成率: {stats['completion_rate']*100:.1f}%")
        print(f"⚡ 用时: {duration*1000:.2f}ms")

        return duration, stats


class OptimizedPerformanceBenchmark(PerformanceBenchmark):
    """优化版性能基准测试 - 使用最新的优化存储"""

    async def setup(self):
        """设置测试环境 - 使用优化存储"""
        # 清理旧数据
        if self.data_dir.exists():
            shutil.rmtree(self.data_dir)

        # 初始化优化存储
        self.storage = OptimizedJSONStorage(str(self.data_dir), save_delay=0.1)  # 更短的延迟用于测试
        await self.storage.initialize()
        clear_metrics()

    async def benchmark_cache_performance(self):
        """测试缓存性能"""
        print(f"\n🚀 缓存性能测试...")

        # 第一次查询 (缓存未命中)
        query = TaskQuery(status=[TaskStatus.TODO], priority=[TaskPriority.HIGH])

        start_time = time.perf_counter()
        results1 = await self.storage.search_tasks(query, "user-1")
        first_query_time = time.perf_counter() - start_time

        # 第二次相同查询 (缓存命中)
        start_time = time.perf_counter()
        results2 = await self.storage.search_tasks(query, "user-1")
        second_query_time = time.perf_counter() - start_time

        cache_speedup = first_query_time / second_query_time if second_query_time > 0 else float('inf')

        print(f"✅ 首次查询: {first_query_time*1000:.2f}ms (缓存未命中)")
        print(f"✅ 缓存查询: {second_query_time*1000:.2f}ms (缓存命中)")
        print(f"🚀 缓存加速: {cache_speedup:.1f}x")

        # 获取缓存统计
        cache_stats = await self.storage.get_cache_stats()
        print(f"📊 缓存命中率: {cache_stats['hit_rate']*100:.1f}%")

        return first_query_time, second_query_time, cache_speedup

    async def benchmark_index_performance(self):
        """测试索引性能"""
        print(f"\n📈 索引性能测试...")

        # 测试状态索引查询
        query = TaskQuery(status=[TaskStatus.IN_PROGRESS])

        start_time = time.perf_counter()
        results = await self.storage.search_tasks(query, "user-1")
        indexed_time = time.perf_counter() - start_time

        print(f"✅ 索引查询找到 {len(results)} 个任务")
        print(f"⚡ 用时: {indexed_time*1000:.2f}ms")

        # 获取索引统计
        index_stats = self.storage.get_index_statistics()
        print(f"📊 索引统计:")
        for index_name, size in index_stats.items():
            if index_name.endswith('_size'):
                print(f"   - {index_name}: {size}")

        return indexed_time, len(results)


async def run_comparison_benchmark():
    """运行对比基准测试"""
    print("=" * 80)
    print("🏁 TaskForge 性能优化对比测试")
    print("=" * 80)

    # 测试参数
    task_count = 5000
    bulk_update_count = 1000

    # 1. 测试标准存储
    print(f"\n📊 标准存储性能测试 ({task_count} 任务)")
    print("-" * 50)

    standard_bench = PerformanceBenchmark("./standard_data")

    try:
        await standard_bench.setup()

        # 创建任务
        create_time, _ = await standard_bench.benchmark_create_tasks(task_count)

        # 搜索测试
        search_time, _ = await standard_bench.benchmark_search_by_status()
        project_time, _ = await standard_bench.benchmark_search_by_project()
        complex_time, _ = await standard_bench.benchmark_complex_query()

        # 批量更新
        bulk_time, _ = await standard_bench.benchmark_bulk_update(bulk_update_count)

        # 统计
        stats_time, _ = await standard_bench.benchmark_statistics()

    finally:
        await standard_bench.teardown()

    # 2. 测试优化存储
    print(f"\n🚀 优化存储性能测试 ({task_count} 任务)")
    print("-" * 50)

    optimized_bench = OptimizedPerformanceBenchmark("./optimized_data")

    try:
        await optimized_bench.setup()

        # 创建任务
        opt_create_time, _ = await optimized_bench.benchmark_create_tasks(task_count)

        # 搜索测试
        opt_search_time, _ = await optimized_bench.benchmark_search_by_status()
        opt_project_time, _ = await optimized_bench.benchmark_search_by_project()
        opt_complex_time, _ = await optimized_bench.benchmark_complex_query()

        # 批量更新
        opt_bulk_time, _ = await optimized_bench.benchmark_bulk_update(bulk_update_count)

        # 统计
        opt_stats_time, _ = await optimized_bench.benchmark_statistics()

        # 额外的优化测试
        cache_first, cache_second, cache_speedup = await optimized_bench.benchmark_cache_performance()
        index_time, _ = await optimized_bench.benchmark_index_performance()

    finally:
        await optimized_bench.teardown()

    # 3. 性能对比总结
    print(f"\n📈 性能对比总结")
    print("=" * 80)

    print(f"{'操作':<15} {'标准存储(ms)':<12} {'优化存储(ms)':<12} {'性能提升':<10}")
    print("-" * 60)

    def calculate_improvement(standard, optimized):
        if standard == 0:
            return float('inf')
        return ((standard - optimized) / standard) * 100

    improvements = {
        '创建任务': calculate_improvement(create_time*1000, opt_create_time*1000),
        '状态搜索': calculate_improvement(search_time*1000, opt_search_time*1000),
        '项目搜索': calculate_improvement(project_time*1000, opt_project_time*1000),
        '复杂查询': calculate_improvement(complex_time*1000, opt_complex_time*1000),
        '批量更新': calculate_improvement(bulk_time*1000, opt_bulk_time*1000),
        '统计查询': calculate_improvement(stats_time*1000, opt_stats_time*1000),
    }

    for operation, improvement in improvements.items():
        if operation == '创建任务':
            print(f"{operation:<15} {create_time*1000:<12.2f} {opt_create_time*1000:<12.2f} {improvement:>+7.1f}%")
        elif operation == '状态搜索':
            print(f"{operation:<15} {search_time*1000:<12.2f} {opt_search_time*1000:<12.2f} {improvement:>+7.1f}%")
        elif operation == '项目搜索':
            print(f"{operation:<15} {project_time*1000:<12.2f} {opt_project_time*1000:<12.2f} {improvement:>+7.1f}%")
        elif operation == '复杂查询':
            print(f"{operation:<15} {complex_time*1000:<12.2f} {opt_complex_time*1000:<12.2f} {improvement:>+7.1f}%")
        elif operation == '批量更新':
            print(f"{operation:<15} {bulk_time*1000:<12.2f} {opt_bulk_time*1000:<12.2f} {improvement:>+7.1f}%")
        elif operation == '统计查询':
            print(f"{operation:<15} {stats_time*1000:<12.2f} {opt_stats_time*1000:<12.2f} {improvement:>+7.1f}%")

    print("\n🚀 优化特性:")
    print(f"   ✅ 延迟写入机制: 减少磁盘I/O")
    print(f"   ✅ 多级索引系统: 加速查询性能")
    print(f"   ✅ 智能缓存: 缓存加速 {cache_speedup:.1f}x")
    print(f"   ✅ 批量操作优化")
    print(f"   ✅ 异步并发处理")

    # 计算平均性能提升
    avg_improvement = statistics.mean([imp for imp in improvements.values() if imp != float('inf')])
    print(f"\n🎯 平均性能提升: {avg_improvement:+.1f}%")

    if avg_improvement > 50:
        print("🏆 性能优化效果显著！")


if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) > 1 and sys.argv[1] == "--compare":
            # 运行对比测试
            await run_comparison_benchmark()
        else:
            # 运行单独的标准测试
            bench = PerformanceBenchmark()

            try:
                await bench.run_full_benchmark()
            finally:
                await bench.teardown()

    # 运行测试
    asyncio.run(main())
