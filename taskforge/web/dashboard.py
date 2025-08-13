"""
Web dashboard using Streamlit
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from taskforge.core.manager import TaskManager, TaskQuery
from taskforge.core.task import Task, TaskPriority, TaskStatus
from taskforge.storage.json_storage import JsonStorage

# Configure Streamlit page
st.set_page_config(
    page_title="TaskForge Dashboard",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "manager" not in st.session_state:
    storage = JsonStorage("./data")
    st.session_state.manager = TaskManager(storage)

if "current_user" not in st.session_state:
    st.session_state.current_user = "default_user"  # TODO: Implement proper auth


def get_manager() -> TaskManager:
    """Get task manager from session state"""
    return st.session_state.manager


async def load_dashboard_data() -> Dict[str, Any]:
    """Load all dashboard data"""
    mgr = get_manager()
    user_id = st.session_state.current_user

    # Load various data in parallel
    all_tasks_query = TaskQuery(limit=1000)
    all_tasks = await mgr.search_tasks(all_tasks_query, user_id)

    overdue_tasks = await mgr.get_overdue_tasks(user_id)
    upcoming_tasks = await mgr.get_upcoming_tasks(7, user_id)
    stats = await mgr.get_task_statistics()
    productivity = await mgr.get_productivity_metrics(user_id, 30)

    return {
        "all_tasks": all_tasks,
        "overdue_tasks": overdue_tasks,
        "upcoming_tasks": upcoming_tasks,
        "stats": stats,
        "productivity": productivity,
    }


def create_task_status_chart(tasks: List[Task]) -> go.Figure:
    """Create task status distribution chart"""
    status_counts = {}
    for task in tasks:
        status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1

    fig = px.pie(
        values=list(status_counts.values()),
        names=list(status_counts.keys()),
        title="Task Status Distribution",
        color_discrete_map={
            "todo": "#FFA07A",
            "in_progress": "#87CEEB",
            "blocked": "#FF6B6B",
            "review": "#FFD93D",
            "done": "#6BCF7F",
            "cancelled": "#D3D3D3",
        },
    )
    fig.update_layout(height=400)
    return fig


def create_priority_chart(tasks: List[Task]) -> go.Figure:
    """Create task priority distribution chart"""
    priority_counts = {}
    for task in tasks:
        priority_counts[task.priority.value] = (
            priority_counts.get(task.priority.value, 0) + 1
        )

    fig = px.bar(
        x=list(priority_counts.keys()),
        y=list(priority_counts.values()),
        title="Task Priority Distribution",
        color=list(priority_counts.keys()),
        color_discrete_map={
            "critical": "#FF4136",
            "high": "#FF851B",
            "medium": "#FFDC00",
            "low": "#2ECC40",
            "none": "#AAAAAA",
        },
    )
    fig.update_layout(height=400)
    return fig


def create_completion_trend_chart(tasks: List[Task]) -> go.Figure:
    """Create task completion trend chart"""
    # Group tasks by completion date
    completion_dates = {}
    for task in tasks:
        if task.status == TaskStatus.DONE and task.completed_at:
            date = task.completed_at.date()
            completion_dates[date] = completion_dates.get(date, 0) + 1

    if not completion_dates:
        # Return empty chart
        fig = go.Figure()
        fig.add_annotation(
            text="No completed tasks yet",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        fig.update_layout(title="Task Completion Trend", height=400)
        return fig

    dates = sorted(completion_dates.keys())
    counts = [completion_dates[date] for date in dates]

    fig = px.line(
        x=dates,
        y=counts,
        title="Task Completion Trend",
        labels={"x": "Date", "y": "Tasks Completed"},
    )
    fig.update_layout(height=400)
    return fig


def render_task_table(tasks: List[Task], title: str):
    """Render a task table"""
    if not tasks:
        st.info(f"No {title.lower()} found.")
        return

    # Convert tasks to DataFrame
    task_data = []
    for task in tasks:
        task_data.append(
            {
                "ID": task.id[:8],
                "Title": task.title,
                "Status": task.status.value,
                "Priority": task.priority.value,
                "Progress": f"{task.progress}%",
                "Due Date": (
                    task.due_date.strftime("%Y-%m-%d")
                    if task.due_date
                    else "No due date"
                ),
                "Created": task.created_at.strftime("%Y-%m-%d"),
            }
        )

    df = pd.DataFrame(task_data)

    st.subheader(title)
    st.dataframe(df, use_container_width=True)


def main():
    """Main dashboard application"""
    st.title("🔥 TaskForge Dashboard")
    st.markdown("Welcome to your comprehensive task management dashboard!")

    # Sidebar for navigation and filters
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page", ["Dashboard", "Tasks", "Projects", "Analytics", "Settings"]
    )

    if page == "Dashboard":
        render_dashboard_page()
    elif page == "Tasks":
        render_tasks_page()
    elif page == "Projects":
        render_projects_page()
    elif page == "Analytics":
        render_analytics_page()
    elif page == "Settings":
        render_settings_page()


def render_dashboard_page():
    """Render the main dashboard page"""
    st.header("📊 Overview")

    # Load data
    with st.spinner("Loading dashboard data..."):
        try:
            data = asyncio.run(load_dashboard_data())
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Total Tasks", value=len(data["all_tasks"]), delta=None)

    with col2:
        completed_count = len(
            [t for t in data["all_tasks"] if t.status == TaskStatus.DONE]
        )
        st.metric(label="Completed Tasks", value=completed_count, delta=None)

    with col3:
        in_progress_count = len(
            [t for t in data["all_tasks"] if t.status == TaskStatus.IN_PROGRESS]
        )
        st.metric(label="In Progress", value=in_progress_count, delta=None)

    with col4:
        st.metric(label="Overdue Tasks", value=len(data["overdue_tasks"]), delta=None)

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        if data["all_tasks"]:
            fig = create_task_status_chart(data["all_tasks"])
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if data["all_tasks"]:
            fig = create_priority_chart(data["all_tasks"])
            st.plotly_chart(fig, use_container_width=True)

    # Completion trend
    if data["all_tasks"]:
        fig = create_completion_trend_chart(data["all_tasks"])
        st.plotly_chart(fig, use_container_width=True)

    # Task lists
    col1, col2 = st.columns(2)

    with col1:
        render_task_table(data["overdue_tasks"][:10], "⚠️ Overdue Tasks")

    with col2:
        render_task_table(data["upcoming_tasks"][:10], "📅 Upcoming Tasks")


def render_tasks_page():
    """Render the tasks management page"""
    st.header("📋 Task Management")

    # Task creation form
    with st.expander("➕ Create New Task"):
        with st.form("create_task_form"):
            col1, col2 = st.columns(2)

            with col1:
                title = st.text_input("Task Title*", placeholder="Enter task title...")
                description = st.text_area(
                    "Description", placeholder="Task description..."
                )
                due_date = st.date_input("Due Date")

            with col2:
                priority = st.selectbox("Priority", list(TaskPriority))
                task_type = st.selectbox("Type", [t.value for t in TaskType])
                tags = st.text_input("Tags", placeholder="tag1, tag2, tag3")

            submitted = st.form_submit_button("Create Task")

            if submitted and title:
                try:
                    mgr = get_manager()

                    # Create task
                    task = Task(
                        title=title,
                        description=description if description else None,
                        priority=priority,
                        task_type=TaskType(task_type),
                        due_date=(
                            datetime.combine(due_date, datetime.min.time())
                            if due_date
                            else None
                        ),
                        tags=set(tag.strip() for tag in tags.split(",") if tag.strip()),
                    )

                    # Save task
                    created_task = asyncio.run(
                        mgr.create_task(task, st.session_state.current_user)
                    )
                    st.success(f"✅ Task created: {created_task.title}")
                    st.experimental_rerun()

                except Exception as e:
                    st.error(f"❌ Error creating task: {e}")

    # Task filters
    st.subheader("🔍 Filter Tasks")
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.multiselect("Status", [s.value for s in TaskStatus])
    with col2:
        priority_filter = st.multiselect("Priority", [p.value for p in TaskPriority])
    with col3:
        search_text = st.text_input("Search", placeholder="Search tasks...")

    # Load and display tasks
    try:
        mgr = get_manager()
        query = TaskQuery(
            status=[TaskStatus(s) for s in status_filter] if status_filter else None,
            priority=(
                [TaskPriority(p) for p in priority_filter] if priority_filter else None
            ),
            search_text=search_text if search_text else None,
            limit=100,
        )

        tasks = asyncio.run(mgr.search_tasks(query, st.session_state.current_user))
        render_task_table(tasks, f"Tasks ({len(tasks)} found)")

    except Exception as e:
        st.error(f"Error loading tasks: {e}")


def render_projects_page():
    """Render the projects page"""
    st.header("📁 Project Management")
    st.info("Project management features coming soon!")


def render_analytics_page():
    """Render the analytics page"""
    st.header("📈 Analytics")
    st.info("Advanced analytics features coming soon!")


def render_settings_page():
    """Render the settings page"""
    st.header("⚙️ Settings")

    st.subheader("User Preferences")
    st.selectbox("Theme", ["Light", "Dark", "Auto"])
    st.selectbox("Language", ["English", "Spanish", "French", "German"])

    st.subheader("Notifications")
    st.checkbox("Email notifications", value=True)
    st.checkbox("Desktop notifications", value=False)
    st.checkbox("Due date reminders", value=True)

    if st.button("Save Settings"):
        st.success("Settings saved!")


if __name__ == "__main__":
    main()
