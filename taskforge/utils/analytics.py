"""
Analytics and reporting engine for TaskForge
"""

import asyncio
import logging
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from taskforge.core.project import Project, ProjectStatus
from taskforge.core.task import Task, TaskPriority, TaskStatus, TaskType
from taskforge.core.user import User

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics"""

    COUNT = "count"
    PERCENTAGE = "percentage"
    AVERAGE = "average"
    SUM = "sum"
    RATE = "rate"
    DISTRIBUTION = "distribution"


class TimePeriod(str, Enum):
    """Time periods for analytics"""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


@dataclass
class Metric:
    """Individual metric value"""

    name: str
    value: Union[int, float, Dict[str, Any]]
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeSeriesPoint:
    """Point in a time series"""

    timestamp: datetime
    value: Union[int, float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeSeries:
    """Time series data"""

    name: str
    points: List[TimeSeriesPoint]
    period: TimePeriod
    start_date: datetime
    end_date: datetime


@dataclass
class AnalyticsReport:
    """Comprehensive analytics report"""

    title: str
    metrics: List[Metric]
    time_series: List[TimeSeries]
    charts: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)


class AnalyticsEngine:
    """Advanced analytics and reporting engine"""

    def __init__(self, storage_backend=None):
        self.storage = storage_backend
        self._cache = {}
        self._cache_ttl = timedelta(minutes=15)
        self._last_cache_clear = datetime.utcnow()

    async def get_task_statistics(
        self, project_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive task statistics"""
        cache_key = f"task_stats_{project_id}_{user_id}"
        cached = self._get_cached_result(cache_key)
        if cached:
            return cached

        # Get tasks based on filters
        if self.storage:
            tasks = await self._get_filtered_tasks(project_id, user_id)
        else:
            tasks = []  # Fallback for when storage is not available

        if not tasks:
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "in_progress_tasks": 0,
                "overdue_tasks": 0,
                "completion_rate": 0.0,
                "average_completion_time": 0.0,
            }

        # Calculate basic statistics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.DONE])
        in_progress_tasks = len(
            [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        )
        overdue_tasks = len([t for t in tasks if t.is_overdue()])

        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0.0

        # Calculate average completion time
        completion_times = []
        for task in tasks:
            if task.status == TaskStatus.DONE and task.completed_at:
                completion_time = (
                    task.completed_at - task.created_at
                ).total_seconds() / 3600  # hours
                completion_times.append(completion_time)

        avg_completion_time = (
            statistics.mean(completion_times) if completion_times else 0.0
        )

        # Status distribution
        status_distribution = Counter(task.status.value for task in tasks)

        # Priority distribution
        priority_distribution = Counter(task.priority.value for task in tasks)

        # Type distribution
        type_distribution = Counter(task.task_type.value for task in tasks)

        # Monthly trends (last 12 months)
        monthly_trends = await self._calculate_monthly_trends(tasks)

        result = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "overdue_tasks": overdue_tasks,
            "completion_rate": round(completion_rate, 3),
            "average_completion_time": round(avg_completion_time, 2),
            "status_distribution": dict(status_distribution),
            "priority_distribution": dict(priority_distribution),
            "type_distribution": dict(type_distribution),
            "monthly_trends": monthly_trends,
        }

        self._cache_result(cache_key, result)
        return result

    async def get_productivity_metrics(
        self, user_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get user productivity metrics"""
        cache_key = f"productivity_{user_id}_{days}"
        cached = self._get_cached_result(cache_key)
        if cached:
            return cached

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        if self.storage:
            # Get tasks for the user in the time period
            tasks = await self._get_user_tasks_in_period(user_id, start_date, end_date)
        else:
            tasks = []

        # Calculate productivity metrics
        tasks_created = len([t for t in tasks if t.created_at >= start_date])
        tasks_completed = len(
            [
                t
                for t in tasks
                if t.status == TaskStatus.DONE
                and t.completed_at
                and t.completed_at >= start_date
            ]
        )

        # Daily productivity
        daily_productivity = self._calculate_daily_productivity(
            tasks, start_date, end_date
        )

        # Velocity (tasks completed per day)
        velocity = tasks_completed / days if days > 0 else 0.0

        # Focus score (percentage of high/critical priority tasks)
        high_priority_tasks = len(
            [
                t
                for t in tasks
                if t.priority in [TaskPriority.HIGH, TaskPriority.CRITICAL]
            ]
        )
        focus_score = high_priority_tasks / len(tasks) if tasks else 0.0

        # Consistency score (standard deviation of daily completions)
        daily_completions = [day["completed"] for day in daily_productivity]
        consistency_score = (
            1.0
            - (
                statistics.stdev(daily_completions)
                / max(statistics.mean(daily_completions), 1)
            )
            if len(daily_completions) > 1
            else 1.0
        )
        consistency_score = max(0.0, min(1.0, consistency_score))

        # Time distribution
        time_by_type = defaultdict(float)
        for task in tasks:
            if hasattr(task, "time_tracking") and task.time_tracking.actual_hours > 0:
                time_by_type[task.task_type.value] += task.time_tracking.actual_hours

        result = {
            "period_days": days,
            "tasks_created": tasks_created,
            "tasks_completed": tasks_completed,
            "velocity": round(velocity, 2),
            "focus_score": round(focus_score, 3),
            "consistency_score": round(consistency_score, 3),
            "daily_productivity": daily_productivity,
            "time_by_type": dict(time_by_type),
            "total_time_logged": sum(time_by_type.values()),
        }

        self._cache_result(cache_key, result)
        return result

    async def get_project_analytics(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive project analytics"""
        cache_key = f"project_analytics_{project_id}"
        cached = self._get_cached_result(cache_key)
        if cached:
            return cached

        if not self.storage:
            return {}

        # Get project and its tasks
        project = await self.storage.get_project(project_id)
        if not project:
            return {}

        tasks = await self._get_project_tasks(project_id)

        # Basic project metrics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.DONE])

        # Progress calculation
        if project.start_date and project.end_date:
            total_duration = (project.end_date - project.start_date).days
            elapsed_duration = (datetime.utcnow() - project.start_date).days
            time_progress = min(
                1.0, elapsed_duration / total_duration if total_duration > 0 else 0.0
            )
        else:
            time_progress = 0.5  # Default if dates not set

        task_progress = completed_tasks / total_tasks if total_tasks > 0 else 0.0

        # Team performance
        team_performance = await self._calculate_team_performance(tasks)

        # Risk indicators
        risk_score = await self._calculate_project_risk(project, tasks)

        # Burndown data
        burndown_data = await self._calculate_burndown(
            tasks, project.start_date, project.end_date
        )

        result = {
            "project_id": project_id,
            "project_name": project.name,
            "status": project.status.value,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "task_progress": round(task_progress, 3),
            "time_progress": round(time_progress, 3),
            "schedule_health": (
                "on_track" if task_progress >= time_progress else "behind"
            ),
            "team_performance": team_performance,
            "risk_score": risk_score,
            "burndown_data": burndown_data,
            "estimated_completion": await self._estimate_completion_date(
                tasks, project
            ),
        }

        self._cache_result(cache_key, result)
        return result

    async def get_team_analytics(
        self, team_members: List[str], project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get team analytics"""
        cache_key = f"team_analytics_{'_'.join(team_members)}_{project_id}"
        cached = self._get_cached_result(cache_key)
        if cached:
            return cached

        # Get tasks for team members
        team_tasks = []
        if self.storage:
            for user_id in team_members:
                user_tasks = await self._get_filtered_tasks(project_id, user_id)
                team_tasks.extend(user_tasks)

        # Individual performance
        individual_metrics = {}
        for user_id in team_members:
            user_tasks = [t for t in team_tasks if t.assigned_to == user_id]
            individual_metrics[user_id] = {
                "tasks_assigned": len(user_tasks),
                "tasks_completed": len(
                    [t for t in user_tasks if t.status == TaskStatus.DONE]
                ),
                "avg_completion_time": await self._calculate_avg_completion_time(
                    user_tasks
                ),
                "overdue_count": len([t for t in user_tasks if t.is_overdue()]),
            }

        # Collaboration metrics
        collaboration_score = await self._calculate_collaboration_score(team_tasks)

        # Team velocity
        completed_this_week = len(
            [
                t
                for t in team_tasks
                if t.status == TaskStatus.DONE
                and t.completed_at
                and t.completed_at >= datetime.utcnow() - timedelta(days=7)
            ]
        )

        result = {
            "team_size": len(team_members),
            "total_tasks": len(team_tasks),
            "team_velocity": completed_this_week,
            "collaboration_score": collaboration_score,
            "individual_metrics": individual_metrics,
            "workload_distribution": await self._calculate_workload_distribution(
                individual_metrics
            ),
        }

        self._cache_result(cache_key, result)
        return result

    async def generate_report(self, report_type: str, **kwargs) -> AnalyticsReport:
        """Generate comprehensive analytics report"""
        if report_type == "task_summary":
            return await self._generate_task_summary_report(**kwargs)
        elif report_type == "productivity":
            return await self._generate_productivity_report(**kwargs)
        elif report_type == "project":
            return await self._generate_project_report(**kwargs)
        elif report_type == "team":
            return await self._generate_team_report(**kwargs)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

    async def get_time_series(
        self,
        metric_name: str,
        period: TimePeriod,
        start_date: datetime,
        end_date: datetime,
        filters: Optional[Dict[str, Any]] = None,
    ) -> TimeSeries:
        """Get time series data for a metric"""
        points = []
        current_date = start_date

        while current_date <= end_date:
            # Calculate metric value for this period
            period_end = self._get_period_end(current_date, period)
            value = await self._calculate_metric_for_period(
                metric_name, current_date, period_end, filters
            )

            points.append(TimeSeriesPoint(timestamp=current_date, value=value))

            current_date = self._get_next_period_start(current_date, period)

        return TimeSeries(
            name=metric_name,
            points=points,
            period=period,
            start_date=start_date,
            end_date=end_date,
        )

    # Private helper methods

    async def _get_filtered_tasks(
        self, project_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> List[Task]:
        """Get tasks with optional filters"""
        if not self.storage:
            return []

        # This would use the storage backend to get filtered tasks
        # For now, return empty list as placeholder
        try:
            from taskforge.core.manager import TaskQuery

            query = TaskQuery(project_id=project_id, assigned_to=user_id, limit=1000)
            return await self.storage.search_tasks(query, user_id or "system")
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []

    async def _get_user_tasks_in_period(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> List[Task]:
        """Get user's tasks within a time period"""
        tasks = await self._get_filtered_tasks(user_id=user_id)
        return [t for t in tasks if start_date <= t.created_at <= end_date]

    async def _get_project_tasks(self, project_id: str) -> List[Task]:
        """Get all tasks for a project"""
        return await self._get_filtered_tasks(project_id=project_id)

    def _calculate_monthly_trends(
        self, tasks: List[Task]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Calculate monthly trends for tasks"""
        trends = {"created": [], "completed": [], "completion_rate": []}

        # Group tasks by month for the last 12 months
        now = datetime.utcnow()
        for i in range(12):
            month_start = now.replace(day=1) - timedelta(days=30 * i)
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end - timedelta(days=month_end.day)

            created_count = len(
                [t for t in tasks if month_start <= t.created_at <= month_end]
            )
            completed_count = len(
                [
                    t
                    for t in tasks
                    if t.status == TaskStatus.DONE
                    and t.completed_at
                    and month_start <= t.completed_at <= month_end
                ]
            )

            completion_rate = (
                completed_count / created_count if created_count > 0 else 0.0
            )

            trends["created"].append(
                {"month": month_start.strftime("%Y-%m"), "value": created_count}
            )
            trends["completed"].append(
                {"month": month_start.strftime("%Y-%m"), "value": completed_count}
            )
            trends["completion_rate"].append(
                {
                    "month": month_start.strftime("%Y-%m"),
                    "value": round(completion_rate, 3),
                }
            )

        return trends

    def _calculate_daily_productivity(
        self, tasks: List[Task], start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Calculate daily productivity metrics"""
        daily_data = []
        current_date = start_date.date()

        while current_date <= end_date.date():
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = day_start + timedelta(days=1)

            created = len([t for t in tasks if day_start <= t.created_at < day_end])
            completed = len(
                [
                    t
                    for t in tasks
                    if t.status == TaskStatus.DONE
                    and t.completed_at
                    and day_start <= t.completed_at < day_end
                ]
            )

            daily_data.append(
                {
                    "date": current_date.isoformat(),
                    "created": created,
                    "completed": completed,
                    "net_progress": completed - created,
                }
            )

            current_date += timedelta(days=1)

        return daily_data

    async def _calculate_team_performance(self, tasks: List[Task]) -> Dict[str, Any]:
        """Calculate team performance metrics"""
        if not tasks:
            return {}

        # Group by assignee
        by_assignee = defaultdict(list)
        for task in tasks:
            if task.assigned_to:
                by_assignee[task.assigned_to].append(task)

        performance = {}
        for user_id, user_tasks in by_assignee.items():
            completed = len([t for t in user_tasks if t.status == TaskStatus.DONE])
            total = len(user_tasks)

            performance[user_id] = {
                "tasks_assigned": total,
                "tasks_completed": completed,
                "completion_rate": completed / total if total > 0 else 0.0,
                "overdue_count": len([t for t in user_tasks if t.is_overdue()]),
            }

        return performance

    async def _calculate_project_risk(
        self, project: Project, tasks: List[Task]
    ) -> float:
        """Calculate project risk score (0-1, higher is riskier)"""
        risk_factors = []

        # Overdue tasks factor
        overdue_count = len([t for t in tasks if t.is_overdue()])
        total_tasks = len(tasks)
        overdue_ratio = overdue_count / total_tasks if total_tasks > 0 else 0.0
        risk_factors.append(overdue_ratio * 0.4)  # 40% weight

        # Schedule slippage factor
        if project.end_date:
            days_to_deadline = (project.end_date - datetime.utcnow()).days
            if days_to_deadline < 0:
                risk_factors.append(0.5)  # Project is overdue
            elif days_to_deadline < 7:
                risk_factors.append(0.3)  # Less than a week
            elif days_to_deadline < 30:
                risk_factors.append(0.1)  # Less than a month
            else:
                risk_factors.append(0.0)  # Plenty of time

        # Team capacity factor (simplified)
        assigned_users = set(t.assigned_to for t in tasks if t.assigned_to)
        unassigned_tasks = len([t for t in tasks if not t.assigned_to])
        unassigned_ratio = unassigned_tasks / total_tasks if total_tasks > 0 else 0.0
        risk_factors.append(unassigned_ratio * 0.3)  # 30% weight

        return min(1.0, sum(risk_factors))

    async def _calculate_burndown(
        self,
        tasks: List[Task],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> List[Dict[str, Any]]:
        """Calculate burndown chart data"""
        if not start_date or not end_date:
            return []

        burndown = []
        total_tasks = len(tasks)
        current_date = start_date.date()

        while current_date <= end_date.date():
            completed_by_date = len(
                [
                    t
                    for t in tasks
                    if t.status == TaskStatus.DONE
                    and t.completed_at
                    and t.completed_at.date() <= current_date
                ]
            )

            remaining = total_tasks - completed_by_date

            burndown.append(
                {
                    "date": current_date.isoformat(),
                    "remaining": remaining,
                    "completed": completed_by_date,
                    "ideal_remaining": max(
                        0,
                        total_tasks
                        - (
                            total_tasks
                            * (current_date - start_date.date()).days
                            / (end_date.date() - start_date.date()).days
                        ),
                    ),
                }
            )

            current_date += timedelta(days=1)

        return burndown

    async def _estimate_completion_date(
        self, tasks: List[Task], project: Project
    ) -> Optional[str]:
        """Estimate project completion date based on current velocity"""
        if not tasks:
            return None

        remaining_tasks = len([t for t in tasks if t.status != TaskStatus.DONE])
        if remaining_tasks == 0:
            return datetime.utcnow().date().isoformat()

        # Calculate recent velocity (tasks completed per day in last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_completions = len(
            [
                t
                for t in tasks
                if t.status == TaskStatus.DONE
                and t.completed_at
                and t.completed_at >= thirty_days_ago
            ]
        )

        velocity = recent_completions / 30  # tasks per day

        if velocity <= 0:
            return None  # Cannot estimate

        days_to_completion = remaining_tasks / velocity
        estimated_date = datetime.utcnow() + timedelta(days=days_to_completion)

        return estimated_date.date().isoformat()

    async def _calculate_collaboration_score(self, tasks: List[Task]) -> float:
        """Calculate team collaboration score"""
        if not tasks:
            return 0.0

        # Simple collaboration metrics
        tasks_with_dependencies = len([t for t in tasks if t.dependencies])
        tasks_with_subtasks = len([t for t in tasks if t.subtasks])

        collaboration_indicators = tasks_with_dependencies + tasks_with_subtasks
        return min(1.0, collaboration_indicators / len(tasks))

    async def _calculate_workload_distribution(
        self, individual_metrics: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate workload distribution fairness"""
        if not individual_metrics:
            return {}

        task_counts = [
            metrics["tasks_assigned"] for metrics in individual_metrics.values()
        ]
        if not task_counts:
            return {}

        mean_tasks = statistics.mean(task_counts)
        max_tasks = max(task_counts)
        min_tasks = min(task_counts)

        return {
            "mean_tasks_per_person": round(mean_tasks, 2),
            "max_tasks": max_tasks,
            "min_tasks": min_tasks,
            "distribution_ratio": (
                max_tasks / min_tasks if min_tasks > 0 else float("inf")
            ),
            "fairness_score": (
                1.0 - (max_tasks - min_tasks) / mean_tasks if mean_tasks > 0 else 1.0
            ),
        }

    async def _calculate_avg_completion_time(self, tasks: List[Task]) -> float:
        """Calculate average completion time for tasks"""
        completion_times = []
        for task in tasks:
            if task.status == TaskStatus.DONE and task.completed_at:
                hours = (task.completed_at - task.created_at).total_seconds() / 3600
                completion_times.append(hours)

        return statistics.mean(completion_times) if completion_times else 0.0

    def _get_cached_result(self, key: str) -> Optional[Any]:
        """Get cached result if still valid"""
        if datetime.utcnow() - self._last_cache_clear > self._cache_ttl:
            self._cache.clear()
            self._last_cache_clear = datetime.utcnow()

        return self._cache.get(key)

    def _cache_result(self, key: str, result: Any):
        """Cache a result"""
        self._cache[key] = result

    def _get_period_end(self, start: datetime, period: TimePeriod) -> datetime:
        """Get end of period"""
        if period == TimePeriod.DAY:
            return start + timedelta(days=1)
        elif period == TimePeriod.WEEK:
            return start + timedelta(weeks=1)
        elif period == TimePeriod.MONTH:
            # Next month's first day
            if start.month == 12:
                return start.replace(year=start.year + 1, month=1, day=1)
            else:
                return start.replace(month=start.month + 1, day=1)
        elif period == TimePeriod.QUARTER:
            return start + timedelta(days=90)  # Approximate
        elif period == TimePeriod.YEAR:
            return start.replace(year=start.year + 1)
        return start

    def _get_next_period_start(self, current: datetime, period: TimePeriod) -> datetime:
        """Get start of next period"""
        return self._get_period_end(current, period)

    async def _calculate_metric_for_period(
        self,
        metric_name: str,
        start: datetime,
        end: datetime,
        filters: Optional[Dict[str, Any]],
    ) -> float:
        """Calculate metric value for a time period"""
        # Placeholder implementation
        return 0.0

    # Report generation methods

    async def _generate_task_summary_report(self, **kwargs) -> AnalyticsReport:
        """Generate task summary report"""
        stats = await self.get_task_statistics()

        metrics = [
            Metric("Total Tasks", stats["total_tasks"], MetricType.COUNT),
            Metric("Completion Rate", stats["completion_rate"], MetricType.PERCENTAGE),
            Metric(
                "Average Completion Time",
                stats["average_completion_time"],
                MetricType.AVERAGE,
            ),
        ]

        return AnalyticsReport(
            title="Task Summary Report",
            metrics=metrics,
            time_series=[],
            insights=[
                f"You have completed {stats['completion_rate']:.1%} of your tasks",
                f"Average completion time is {stats['average_completion_time']:.1f} hours",
            ],
        )

    async def _generate_productivity_report(
        self, user_id: str, days: int = 30, **kwargs
    ) -> AnalyticsReport:
        """Generate productivity report"""
        productivity = await self.get_productivity_metrics(user_id, days)

        metrics = [
            Metric("Tasks Created", productivity["tasks_created"], MetricType.COUNT),
            Metric(
                "Tasks Completed", productivity["tasks_completed"], MetricType.COUNT
            ),
            Metric("Velocity", productivity["velocity"], MetricType.RATE),
            Metric("Focus Score", productivity["focus_score"], MetricType.PERCENTAGE),
        ]

        return AnalyticsReport(
            title=f"Productivity Report ({days} days)",
            metrics=metrics,
            time_series=[],
            insights=[
                f"Your velocity is {productivity['velocity']:.2f} tasks per day",
                f"Focus score: {productivity['focus_score']:.1%}",
            ],
        )

    async def _generate_project_report(
        self, project_id: str, **kwargs
    ) -> AnalyticsReport:
        """Generate project report"""
        analytics = await self.get_project_analytics(project_id)

        metrics = [
            Metric(
                "Project Progress", analytics["task_progress"], MetricType.PERCENTAGE
            ),
            Metric("Schedule Health", analytics["schedule_health"], MetricType.COUNT),
            Metric("Risk Score", analytics["risk_score"], MetricType.PERCENTAGE),
        ]

        return AnalyticsReport(
            title=f"Project Report: {analytics['project_name']}",
            metrics=metrics,
            time_series=[],
            insights=[
                f"Project is {analytics['task_progress']:.1%} complete",
                f"Schedule status: {analytics['schedule_health']}",
            ],
        )

    async def _generate_team_report(
        self, team_members: List[str], **kwargs
    ) -> AnalyticsReport:
        """Generate team report"""
        analytics = await self.get_team_analytics(team_members)

        metrics = [
            Metric("Team Size", analytics["team_size"], MetricType.COUNT),
            Metric("Team Velocity", analytics["team_velocity"], MetricType.RATE),
            Metric(
                "Collaboration Score",
                analytics["collaboration_score"],
                MetricType.PERCENTAGE,
            ),
        ]

        return AnalyticsReport(
            title="Team Performance Report",
            metrics=metrics,
            time_series=[],
            insights=[
                f"Team completed {analytics['team_velocity']} tasks this week",
                f"Collaboration score: {analytics['collaboration_score']:.1%}",
            ],
        )


# Factory function
def create_analytics_engine(storage_backend=None) -> AnalyticsEngine:
    """Create a configured analytics engine"""
    return AnalyticsEngine(storage_backend)
