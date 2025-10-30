"""
Performance benchmarking script for TaskForge
测试优化前后的性能对比
"""

import asyncio
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import shutil
from typing import List

from taskforge.core.task import Task, TaskStatus, TaskPriority
from taskforge.core.queries import TaskQuery
from taskforge.storage.json_storage import JSONStorage
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

    async def run_full_benchmark(self):
        """运行完整基准测试"""
        print("=" * 60)
        print("🚀 TaskForge 性能基准测试")
        print("=" * 60)

        try:
            await self.setup()

            # 1. 批量创建测试
            create_time, create_rate = await self.benchmark_bulk_create(1000)

            # 2. 查询测试
            status_time, status_count = await self.benchmark_search_by_status()
            project_time, project_count = await self.benchmark_search_by_project()
            complex_time, complex_count = await self.benchmark_complex_query()

            # 3. 批量更新测试
            update_time, update_rate = await self.benchmark_bulk_update(500)

            # 4. 统计测试
            stats_time, stats = await self.benchmark_statistics()

            # 显示性能指标摘要
            print("\n" + "=" * 60)
            print("📈 性能指标摘要")
            print("=" * 60)

            metrics = get_metrics()
            if metrics:
                print("\n🔥 热点函数:")
                sorted_metrics = sorted(
                    metrics.items(),
                    key=lambda x: x[1]['avg'],
                    reverse=True
                )[:5]

                for name, data in sorted_metrics:
                    print(f"   {name}:")
                    print(f"      平均: {data['avg']*1000:.2f}ms")
                    print(f"      调用: {data['count']}次")

            print("\n✅ 基准测试完成!")

        finally:
            await self.teardown()


async def main():
    """主函数"""
    benchmark = PerformanceBenchmark()
    await benchmark.run_full_benchmark()


if __name__ == "__main__":
    asyncio.run(main())
