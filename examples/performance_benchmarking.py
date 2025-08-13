#!/usr/bin/env python3
"""
TaskForge Performance Benchmarking
==================================

This module provides comprehensive performance benchmarking for TaskForge,
including database operations, API endpoints, concurrent usage scenarios,
and scalability testing.

Great for: Performance testing, optimization, capacity planning
"""

import asyncio
import concurrent.futures
import json
import random
import statistics
import time
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from taskforge import Project, Task, TaskManager, TaskPriority, TaskStatus
from taskforge.core.user import User
from taskforge.storage import JsonStorage


@dataclass
class BenchmarkResult:
    """Represents a benchmark test result."""

    test_name: str
    operation_count: int
    total_time_seconds: float
    operations_per_second: float
    average_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    memory_usage_mb: Optional[float] = None
    error_count: int = 0
    metadata: Dict[str, Any] = None


class PerformanceBenchmark:
    """Performance benchmarking suite for TaskForge."""

    def __init__(self, storage_type: str = "json"):
        self.storage_type = storage_type
        self.storage = None
        self.manager = None
        self.results: List[BenchmarkResult] = []
        self.test_data = {"users": [], "projects": [], "tasks": []}

    async def setup(self):
        """Initialize storage and manager for benchmarking."""
        if self.storage_type == "json":
            self.storage = JsonStorage("./benchmark_data")
        # Add other storage types as needed

        await self.storage.initialize()
        self.manager = TaskManager(self.storage)
        print(f"📊 Benchmark setup complete using {self.storage_type} storage")

    async def cleanup(self):
        """Clean up benchmark data."""
        if self.storage:
            await self.storage.cleanup()
        print("🧹 Benchmark cleanup complete")

    @asynccontextmanager
    async def measure_time(self):
        """Context manager to measure execution time."""
        start_time = time.perf_counter()
        yield
        end_time = time.perf_counter()
        self.last_execution_time = end_time - start_time

    def calculate_statistics(self, latencies: List[float]) -> Dict[str, float]:
        """Calculate latency statistics."""
        if not latencies:
            return {"min": 0, "max": 0, "avg": 0, "p95": 0, "p99": 0}

        latencies_ms = [lat * 1000 for lat in latencies]  # Convert to milliseconds

        return {
            "min": min(latencies_ms),
            "max": max(latencies_ms),
            "avg": statistics.mean(latencies_ms),
            "p95": (
                statistics.quantiles(latencies_ms, n=20)[18]
                if len(latencies_ms) > 20
                else max(latencies_ms)
            ),
            "p99": (
                statistics.quantiles(latencies_ms, n=100)[98]
                if len(latencies_ms) > 100
                else max(latencies_ms)
            ),
        }

    async def benchmark_task_creation(self, num_tasks: int = 1000) -> BenchmarkResult:
        """Benchmark task creation performance."""
        print(f"🚀 Benchmarking task creation ({num_tasks:,} tasks)")

        latencies = []
        errors = 0
        user_id = "benchmark_user"

        # Create sample projects for tasks
        projects = []
        for i in range(10):
            project = Project(
                name=f"Benchmark Project {i+1}",
                description=f"Performance test project {i+1}",
            )
            created_project = await self.manager.create_project(project, user_id)
            projects.append(created_project)

        start_time = time.perf_counter()

        for i in range(num_tasks):
            try:
                task_start = time.perf_counter()

                task = Task(
                    title=f"Benchmark Task {i+1}",
                    description=f"Performance test task {i+1} - Testing creation speed",
                    priority=random.choice(list(TaskPriority)),
                    project_id=random.choice(projects).id if projects else None,
                    tags=[f"benchmark", f"batch-{i // 100}"],
                    estimated_hours=random.uniform(0.5, 8.0),
                )

                await self.manager.create_task(task, user_id)

                task_end = time.perf_counter()
                latencies.append(task_end - task_start)

                # Progress indicator
                if (i + 1) % 100 == 0:
                    print(f"   ⏳ Created {i+1:,} tasks...")

            except Exception as e:
                errors += 1
                print(f"   ❌ Error creating task {i+1}: {e}")

        end_time = time.perf_counter()
        total_time = end_time - start_time

        stats = self.calculate_statistics(latencies)

        result = BenchmarkResult(
            test_name="Task Creation",
            operation_count=num_tasks,
            total_time_seconds=total_time,
            operations_per_second=(num_tasks - errors) / total_time,
            average_latency_ms=stats["avg"],
            min_latency_ms=stats["min"],
            max_latency_ms=stats["max"],
            p95_latency_ms=stats["p95"],
            p99_latency_ms=stats["p99"],
            error_count=errors,
            metadata={"projects_created": len(projects)},
        )

        self.results.append(result)
        print(
            f"   ✅ Task creation benchmark complete: {result.operations_per_second:.1f} ops/sec"
        )
        return result

    async def benchmark_task_queries(self, num_queries: int = 500) -> BenchmarkResult:
        """Benchmark task query performance."""
        print(f"🔍 Benchmarking task queries ({num_queries:,} queries)")

        # First ensure we have data to query
        user_id = "benchmark_user"
        if not self.test_data["tasks"]:
            await self.create_sample_data(100, 10, 1000)  # Create sample data

        latencies = []
        errors = 0

        query_types = [
            lambda: self.manager.get_user_tasks(user_id),
            lambda: self.manager.search_tasks(
                self.manager.TaskQuery(priority=[TaskPriority.HIGH]), user_id
            ),
            lambda: self.manager.search_tasks(
                self.manager.TaskQuery(status=[TaskStatus.TODO]), user_id
            ),
            lambda: self.manager.search_tasks(
                self.manager.TaskQuery(tags=["benchmark"]), user_id
            ),
        ]

        start_time = time.perf_counter()

        for i in range(num_queries):
            try:
                query_start = time.perf_counter()

                # Randomly select query type
                query_func = random.choice(query_types)
                results = await query_func()

                query_end = time.perf_counter()
                latencies.append(query_end - query_start)

                if (i + 1) % 50 == 0:
                    print(f"   ⏳ Executed {i+1:,} queries...")

            except Exception as e:
                errors += 1
                print(f"   ❌ Error in query {i+1}: {e}")

        end_time = time.perf_counter()
        total_time = end_time - start_time

        stats = self.calculate_statistics(latencies)

        result = BenchmarkResult(
            test_name="Task Queries",
            operation_count=num_queries,
            total_time_seconds=total_time,
            operations_per_second=(num_queries - errors) / total_time,
            average_latency_ms=stats["avg"],
            min_latency_ms=stats["min"],
            max_latency_ms=stats["max"],
            p95_latency_ms=stats["p95"],
            p99_latency_ms=stats["p99"],
            error_count=errors,
        )

        self.results.append(result)
        print(
            f"   ✅ Query benchmark complete: {result.operations_per_second:.1f} queries/sec"
        )
        return result

    async def benchmark_task_updates(self, num_updates: int = 500) -> BenchmarkResult:
        """Benchmark task update performance."""
        print(f"📝 Benchmarking task updates ({num_updates:,} updates)")

        # Ensure we have tasks to update
        user_id = "benchmark_user"
        if not self.test_data["tasks"]:
            await self.create_sample_data(50, 5, 500)

        tasks = await self.manager.get_user_tasks(user_id)
        if not tasks:
            print("   ⚠️  No tasks available for update benchmark")
            return

        latencies = []
        errors = 0

        start_time = time.perf_counter()

        for i in range(num_updates):
            try:
                update_start = time.perf_counter()

                # Select random task to update
                task = random.choice(tasks)

                # Perform various update operations
                update_operations = [
                    lambda: self.manager.update_task_status(
                        task.id, random.choice(list(TaskStatus)), user_id
                    ),
                    lambda: self.manager.add_task_note(
                        task.id, f"Update note {i+1}: Performance test", user_id
                    ),
                    lambda: self.manager.update_task(
                        task.id,
                        {"priority": random.choice(list(TaskPriority))},
                        user_id,
                    ),
                ]

                update_op = random.choice(update_operations)
                await update_op()

                update_end = time.perf_counter()
                latencies.append(update_end - update_start)

                if (i + 1) % 50 == 0:
                    print(f"   ⏳ Executed {i+1:,} updates...")

            except Exception as e:
                errors += 1
                print(f"   ❌ Error in update {i+1}: {e}")

        end_time = time.perf_counter()
        total_time = end_time - start_time

        stats = self.calculate_statistics(latencies)

        result = BenchmarkResult(
            test_name="Task Updates",
            operation_count=num_updates,
            total_time_seconds=total_time,
            operations_per_second=(num_updates - errors) / total_time,
            average_latency_ms=stats["avg"],
            min_latency_ms=stats["min"],
            max_latency_ms=stats["max"],
            p95_latency_ms=stats["p95"],
            p99_latency_ms=stats["p99"],
            error_count=errors,
        )

        self.results.append(result)
        print(
            f"   ✅ Update benchmark complete: {result.operations_per_second:.1f} updates/sec"
        )
        return result

    async def benchmark_concurrent_operations(
        self, num_concurrent_users: int = 10, operations_per_user: int = 50
    ) -> BenchmarkResult:
        """Benchmark concurrent operations from multiple users."""
        print(
            f"👥 Benchmarking concurrent operations ({num_concurrent_users} users, {operations_per_user} ops each)"
        )

        async def simulate_user_workload(user_id: str, operations: int) -> List[float]:
            """Simulate a single user's workload."""
            user_latencies = []

            for i in range(operations):
                try:
                    op_start = time.perf_counter()

                    # Mix of operations a user might perform
                    operations_pool = [
                        # Create task
                        lambda: self.manager.create_task(
                            Task(
                                title=f"Concurrent task {user_id}-{i}",
                                description=f"Task created by {user_id}",
                                priority=random.choice(list(TaskPriority)),
                            ),
                            user_id,
                        ),
                        # Query tasks
                        lambda: self.manager.get_user_tasks(user_id),
                        # Search tasks
                        lambda: self.manager.search_tasks(
                            self.manager.TaskQuery(priority=[TaskPriority.HIGH]),
                            user_id,
                        ),
                    ]

                    operation = random.choice(operations_pool)
                    await operation()

                    op_end = time.perf_counter()
                    user_latencies.append(op_end - op_start)

                except Exception as e:
                    print(f"   ❌ Error for user {user_id}: {e}")

            return user_latencies

        # Create concurrent user tasks
        user_tasks = []
        for i in range(num_concurrent_users):
            user_id = f"concurrent_user_{i+1}"
            task = simulate_user_workload(user_id, operations_per_user)
            user_tasks.append(task)

        start_time = time.perf_counter()

        # Execute all user workloads concurrently
        all_latencies = []
        try:
            results = await asyncio.gather(*user_tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    all_latencies.extend(result)
                else:
                    print(f"   ⚠️  Exception in concurrent execution: {result}")

        except Exception as e:
            print(f"   ❌ Error in concurrent execution: {e}")

        end_time = time.perf_counter()
        total_time = end_time - start_time
        total_operations = num_concurrent_users * operations_per_user

        stats = self.calculate_statistics(all_latencies)

        result = BenchmarkResult(
            test_name="Concurrent Operations",
            operation_count=total_operations,
            total_time_seconds=total_time,
            operations_per_second=(
                len(all_latencies) / total_time if total_time > 0 else 0
            ),
            average_latency_ms=stats["avg"],
            min_latency_ms=stats["min"],
            max_latency_ms=stats["max"],
            p95_latency_ms=stats["p95"],
            p99_latency_ms=stats["p99"],
            error_count=total_operations - len(all_latencies),
            metadata={
                "concurrent_users": num_concurrent_users,
                "operations_per_user": operations_per_user,
            },
        )

        self.results.append(result)
        print(
            f"   ✅ Concurrent benchmark complete: {result.operations_per_second:.1f} ops/sec"
        )
        return result

    async def benchmark_large_dataset_operations(
        self, dataset_size: int = 10000
    ) -> BenchmarkResult:
        """Benchmark operations on large datasets."""
        print(f"📈 Benchmarking large dataset operations ({dataset_size:,} records)")

        user_id = "dataset_user"

        # Create large dataset
        print("   📊 Creating large dataset...")
        dataset_creation_start = time.perf_counter()

        # Create projects
        projects = []
        for i in range(50):
            project = Project(
                name=f"Large Dataset Project {i+1}",
                description=f"Project {i+1} for large dataset testing",
            )
            created_project = await self.manager.create_project(project, user_id)
            projects.append(created_project)

        # Create large number of tasks
        tasks = []
        batch_size = 100
        for batch_start in range(0, dataset_size, batch_size):
            batch_end = min(batch_start + batch_size, dataset_size)

            batch_tasks = []
            for i in range(batch_start, batch_end):
                task = Task(
                    title=f"Large Dataset Task {i+1}",
                    description=f"Task {i+1} in large dataset test with detailed description",
                    priority=random.choice(list(TaskPriority)),
                    project_id=random.choice(projects).id,
                    tags=[
                        f"large-dataset",
                        f"batch-{i // batch_size}",
                        f"category-{i % 10}",
                    ],
                    estimated_hours=random.uniform(1, 16),
                )
                batch_tasks.append(task)

            # Create batch of tasks
            for task in batch_tasks:
                created_task = await self.manager.create_task(task, user_id)
                tasks.append(created_task)

            print(f"   ⏳ Created {batch_end:,}/{dataset_size:,} tasks...")

        dataset_creation_end = time.perf_counter()
        dataset_creation_time = dataset_creation_end - dataset_creation_start

        print(f"   ✅ Dataset created in {dataset_creation_time:.1f}s")

        # Now benchmark operations on large dataset
        latencies = []

        operations = [
            ("Get all user tasks", lambda: self.manager.get_user_tasks(user_id)),
            (
                "Search high priority",
                lambda: self.manager.search_tasks(
                    self.manager.TaskQuery(priority=[TaskPriority.HIGH]), user_id
                ),
            ),
            (
                "Search by tag",
                lambda: self.manager.search_tasks(
                    self.manager.TaskQuery(tags=["large-dataset"]), user_id
                ),
            ),
            (
                "Search by project",
                lambda: self.manager.search_tasks(
                    self.manager.TaskQuery(project_ids=[projects[0].id]), user_id
                ),
            ),
        ]

        print("   🔍 Testing operations on large dataset...")

        operation_results = {}
        for op_name, op_func in operations:
            op_start = time.perf_counter()

            results = await op_func()

            op_end = time.perf_counter()
            op_time = op_end - op_start

            latencies.append(op_time)
            operation_results[op_name] = {
                "time_seconds": op_time,
                "results_count": len(results) if results else 0,
            }

            print(
                f"      {op_name}: {op_time:.3f}s ({len(results) if results else 0} results)"
            )

        stats = self.calculate_statistics(latencies)

        result = BenchmarkResult(
            test_name="Large Dataset Operations",
            operation_count=len(operations),
            total_time_seconds=sum(latencies),
            operations_per_second=len(operations) / sum(latencies),
            average_latency_ms=stats["avg"],
            min_latency_ms=stats["min"],
            max_latency_ms=stats["max"],
            p95_latency_ms=stats["p95"],
            p99_latency_ms=stats["p99"],
            error_count=0,
            metadata={
                "dataset_size": dataset_size,
                "dataset_creation_time": dataset_creation_time,
                "operation_results": operation_results,
            },
        )

        self.results.append(result)
        print(f"   ✅ Large dataset benchmark complete")
        return result

    async def create_sample_data(
        self, num_users: int, num_projects: int, num_tasks: int
    ):
        """Create sample data for benchmarking."""
        print(
            f"📊 Creating sample data ({num_users} users, {num_projects} projects, {num_tasks} tasks)"
        )

        # Create users
        for i in range(num_users):
            user_id = f"sample_user_{i+1}"
            self.test_data["users"].append(user_id)

        # Create projects
        for i in range(num_projects):
            project = Project(
                name=f"Sample Project {i+1}",
                description=f"Sample project {i+1} for benchmarking",
            )
            created_project = await self.manager.create_project(
                project, self.test_data["users"][0]
            )
            self.test_data["projects"].append(created_project)

        # Create tasks
        for i in range(num_tasks):
            user_id = random.choice(self.test_data["users"])
            project = (
                random.choice(self.test_data["projects"])
                if self.test_data["projects"]
                else None
            )

            task = Task(
                title=f"Sample Task {i+1}",
                description=f"Sample task {i+1} for benchmarking purposes",
                priority=random.choice(list(TaskPriority)),
                project_id=project.id if project else None,
                tags=["sample", "benchmark", f"category-{i % 5}"],
            )

            created_task = await self.manager.create_task(task, user_id)
            self.test_data["tasks"].append(created_task)

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report."""
        if not self.results:
            return {"error": "No benchmark results available"}

        report = {
            "benchmark_summary": {
                "total_tests": len(self.results),
                "storage_type": self.storage_type,
                "timestamp": datetime.now().isoformat(),
            },
            "test_results": [],
            "performance_analysis": {},
            "recommendations": [],
        }

        # Add individual test results
        for result in self.results:
            report["test_results"].append(asdict(result))

        # Performance analysis
        total_operations = sum(r.operation_count for r in self.results)
        total_time = sum(r.total_time_seconds for r in self.results)
        avg_ops_per_sec = statistics.mean(
            [r.operations_per_second for r in self.results]
        )

        report["performance_analysis"] = {
            "total_operations": total_operations,
            "total_execution_time": total_time,
            "average_operations_per_second": avg_ops_per_sec,
            "fastest_test": max(
                self.results, key=lambda r: r.operations_per_second
            ).test_name,
            "slowest_test": min(
                self.results, key=lambda r: r.operations_per_second
            ).test_name,
        }

        # Generate recommendations
        recommendations = []

        # Performance recommendations
        if avg_ops_per_sec < 100:
            recommendations.append(
                "Consider optimizing database queries or using connection pooling"
            )

        # Check for high latency
        high_latency_tests = [r for r in self.results if r.p95_latency_ms > 1000]
        if high_latency_tests:
            recommendations.append(
                f"High latency detected in {len(high_latency_tests)} tests - investigate bottlenecks"
            )

        # Check for errors
        error_tests = [r for r in self.results if r.error_count > 0]
        if error_tests:
            recommendations.append(
                f"Errors detected in {len(error_tests)} tests - review error handling"
            )

        # Storage-specific recommendations
        if self.storage_type == "json":
            recommendations.append(
                "Consider upgrading to PostgreSQL for better performance at scale"
            )

        report["recommendations"] = recommendations

        return report

    def print_summary(self):
        """Print a formatted summary of benchmark results."""
        print("\n" + "=" * 60)
        print("📊 TASKFORGE PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 60)

        if not self.results:
            print("❌ No benchmark results to display")
            return

        print(f"Storage Type: {self.storage_type}")
        print(f"Total Tests: {len(self.results)}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Results table header
        print(
            f"{'Test Name':<25} {'Ops/sec':<12} {'Avg Latency':<15} {'P95 Latency':<15} {'Errors':<8}"
        )
        print("-" * 75)

        # Results table rows
        for result in self.results:
            print(
                f"{result.test_name:<25} "
                f"{result.operations_per_second:<12.1f} "
                f"{result.average_latency_ms:<15.2f}ms "
                f"{result.p95_latency_ms:<15.2f}ms "
                f"{result.error_count:<8}"
            )

        print()

        # Performance analysis
        total_ops = sum(r.operation_count for r in self.results)
        avg_ops_per_sec = statistics.mean(
            [r.operations_per_second for r in self.results]
        )

        fastest_test = max(self.results, key=lambda r: r.operations_per_second)
        slowest_test = min(self.results, key=lambda r: r.operations_per_second)

        print("📈 Performance Analysis:")
        print(f"   Total Operations: {total_ops:,}")
        print(f"   Average Ops/sec: {avg_ops_per_sec:.1f}")
        print(
            f"   Fastest Test: {fastest_test.test_name} ({fastest_test.operations_per_second:.1f} ops/sec)"
        )
        print(
            f"   Slowest Test: {slowest_test.test_name} ({slowest_test.operations_per_second:.1f} ops/sec)"
        )

        # Recommendations
        print("\n💡 Recommendations:")
        if avg_ops_per_sec > 1000:
            print(
                "   ✅ Excellent performance! Your TaskForge setup is well optimized."
            )
        elif avg_ops_per_sec > 500:
            print(
                "   👍 Good performance. Consider monitoring for potential bottlenecks."
            )
        elif avg_ops_per_sec > 100:
            print(
                "   ⚠️  Moderate performance. Consider database optimization or hardware upgrades."
            )
        else:
            print(
                "   🚨 Performance issues detected. Review database configuration and system resources."
            )

        if self.storage_type == "json" and total_ops > 10000:
            print(
                "   💾 Consider upgrading to PostgreSQL for better performance with large datasets."
            )

        error_count = sum(r.error_count for r in self.results)
        if error_count > 0:
            print(
                f"   ❌ {error_count} errors detected across tests. Review error logs."
            )
        else:
            print("   ✅ No errors detected in benchmark tests.")

        print("\n" + "=" * 60)


async def run_comprehensive_benchmark():
    """Run a comprehensive performance benchmark suite."""
    print("🚀 Starting TaskForge Comprehensive Performance Benchmark")
    print("=" * 65)

    # Test different configurations
    storage_types = ["json"]  # Add more storage types as available

    all_results = {}

    for storage_type in storage_types:
        print(f"\n🔧 Testing with {storage_type} storage...")

        benchmark = PerformanceBenchmark(storage_type)

        try:
            await benchmark.setup()

            # Run benchmark suite
            await benchmark.benchmark_task_creation(1000)
            await benchmark.benchmark_task_queries(500)
            await benchmark.benchmark_task_updates(300)
            await benchmark.benchmark_concurrent_operations(10, 20)
            await benchmark.benchmark_large_dataset_operations(5000)

            # Generate and save report
            report = benchmark.generate_report()
            all_results[storage_type] = report

            # Print summary
            benchmark.print_summary()

            # Save detailed report to file
            report_filename = f"benchmark_report_{storage_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, "w") as f:
                json.dump(report, f, indent=2, default=str)
            print(f"📄 Detailed report saved to: {report_filename}")

        except Exception as e:
            print(f"❌ Error during {storage_type} benchmark: {e}")
            import traceback

            traceback.print_exc()

        finally:
            await benchmark.cleanup()

    return all_results


async def main():
    """Run the performance benchmark suite."""
    print("📊 TaskForge Performance Benchmarking Suite")
    print("=" * 45)
    print("This benchmark tests TaskForge performance across various scenarios:")
    print("- Task creation speed")
    print("- Query performance")
    print("- Update operations")
    print("- Concurrent user simulation")
    print("- Large dataset handling")
    print("=" * 45)

    try:
        results = await run_comprehensive_benchmark()

        print("\n🎉 Comprehensive Benchmark Complete!")
        print("=" * 42)

        for storage_type, result in results.items():
            if "error" in result:
                print(f"❌ {storage_type}: {result['error']}")
            else:
                summary = result["benchmark_summary"]
                analysis = result["performance_analysis"]
                print(
                    f"✅ {storage_type}: {summary['total_tests']} tests, "
                    f"{analysis['average_operations_per_second']:.1f} avg ops/sec"
                )

        print("\n📋 Benchmark completed successfully!")
        print("Check the generated report files for detailed analysis.")

    except Exception as e:
        print(f"\n❌ Error running comprehensive benchmark: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
