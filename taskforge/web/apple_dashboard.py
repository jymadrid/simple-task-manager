"""
Apple-inspired web dashboard using Streamlit with modern design
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from taskforge.core.manager import TaskManager, TaskQuery
from taskforge.core.task import Task, TaskPriority, TaskStatus
from taskforge.storage.json_storage import JSONStorage
from taskforge.web.helpers import (
    display_value,
    ensure_dashboard_user,
    is_overdue_task,
    is_upcoming_task,
)

# Apple Design System Configuration
APPLE_COLORS = {
    "primary": "#007AFF",  # SF Blue
    "secondary": "#5856D6",  # SF Purple
    "success": "#34C759",  # SF Green
    "warning": "#FF9500",  # SF Orange
    "error": "#FF3B30",  # SF Red
    "background": "#F2F2F7",  # Light background
    "surface": "#FFFFFF",  # Pure white
    "text_primary": "#000000",  # Black
    "text_secondary": "#8E8E93",  # SF Gray
    "border": "#E5E5EA",  # Light border
    "accent": "#AF52DE",  # SF Purple variant
    "system_gray": "#F2F2F7",
    "system_gray2": "#AEAEB2",
    "system_gray3": "#C7C7CC",
    "system_gray4": "#D1D1D6",
    "system_gray5": "#E5E5EA",
    "system_gray6": "#F2F2F7",
}

# Configure Streamlit page with Apple aesthetics
st.set_page_config(
    page_title="TaskForge • Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apple-inspired CSS
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Root variables for Apple design system */
:root {{
    --apple-blue: {APPLE_COLORS["primary"]};
    --apple-green: {APPLE_COLORS["success"]};
    --apple-orange: {APPLE_COLORS["warning"]};
    --apple-red: {APPLE_COLORS["error"]};
    --apple-purple: {APPLE_COLORS["secondary"]};
    --apple-background: {APPLE_COLORS["background"]};
    --apple-surface: {APPLE_COLORS["surface"]};
    --apple-text: {APPLE_COLORS["text_primary"]};
    --apple-text-secondary: {APPLE_COLORS["text_secondary"]};
    --apple-border: {APPLE_COLORS["border"]};
}}

/* Main layout styling */
.main .block-container {{
    padding-top: 2rem;
    padding-bottom: 2rem;
    background: var(--apple-background);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}}

/* Header styling */
.main h1, .main h2, .main h3 {{
    color: var(--apple-text);
    font-weight: 600;
    letter-spacing: -0.025em;
}}

.main h1 {{
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}}

/* Sidebar styling */
.css-1d391kg {{
    background: var(--apple-surface);
    border-right: 1px solid var(--apple-border);
}}

.css-1d391kg .css-1v0mbdj {{
    color: var(--apple-text);
    font-weight: 500;
}}

/* Metric cards with Apple-style glassmorphism */
.metric-card {{
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(20px);
    border: 1px solid var(--apple-border);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    margin-bottom: 1rem;
}}

.metric-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}}

/* Button styling */
.stButton > button {{
    background: var(--apple-blue);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.75rem 1.5rem;
    font-weight: 500;
    font-size: 1rem;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(0, 122, 255, 0.3);
}}

.stButton > button:hover {{
    background: #0051D5;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(0, 122, 255, 0.4);
}}

/* Form elements */
.stTextInput > div > div > input {{
    border: 1px solid var(--apple-border);
    border-radius: 8px;
    padding: 0.75rem;
    font-size: 1rem;
    transition: border-color 0.2s ease;
}}

.stTextInput > div > div > input:focus {{
    border-color: var(--apple-blue);
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
}}

.stSelectbox > div > div {{
    border-radius: 8px;
    border: 1px solid var(--apple-border);
}}

/* Table styling */
.dataframe {{
    border: none;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 16px rgba(0, 0, 0, 0.1);
}}

.dataframe th {{
    background: var(--apple-background);
    color: var(--apple-text);
    font-weight: 600;
    padding: 1rem;
    border: none;
}}

.dataframe td {{
    padding: 0.75rem 1rem;
    border: none;
    border-bottom: 1px solid var(--apple-border);
}}

/* Status badges */
.status-todo {{
    background: #FFE5B4;
    color: #B25000;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
}}

.status-in-progress {{
    background: #E1F5FE;
    color: #0277BD;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
}}

.status-done {{
    background: #E8F5E8;
    color: #2E7D32;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
}}

/* Priority badges */
.priority-critical {{
    background: #FFEBEE;
    color: #C62828;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
}}

.priority-high {{
    background: #FFF3E0;
    color: #EF6C00;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
}}

.priority-medium {{
    background: #F3E5F5;
    color: #7B1FA2;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
}}

.priority-low {{
    background: #E8F5E8;
    color: #388E3C;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
}}

/* Charts */
.plotly-graph-div {{
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}}

/* Alert styling */
.stAlert {{
    border-radius: 12px;
    border: none;
    backdrop-filter: blur(20px);
}}

/* Expander styling */
.streamlit-expanderHeader {{
    background: var(--apple-surface);
    border-radius: 12px;
    border: 1px solid var(--apple-border);
    font-weight: 500;
}}

/* Loading spinner */
.stSpinner > div {{
    border-color: var(--apple-blue);
}}

/* Custom glass panel */
.glass-panel {{
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(20px);
    border: 1px solid var(--apple-border);
    border-radius: 20px;
    padding: 2rem;
    margin: 1rem 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}}

/* Typography improvements */
.big-metric {{
    font-size: 3rem;
    font-weight: 700;
    color: var(--apple-text);
    line-height: 1;
    margin: 0;
}}

.metric-label {{
    font-size: 1rem;
    color: var(--apple-text-secondary);
    font-weight: 500;
    margin-top: 0.5rem;
}}

.section-header {{
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--apple-text);
    margin: 2rem 0 1rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "manager" not in st.session_state:
    storage = JSONStorage("./data")
    st.session_state.manager = TaskManager(storage)

if "current_user" not in st.session_state:
    st.session_state.current_user = "default_user"


def get_manager() -> TaskManager:
    """Get task manager from session state"""
    return st.session_state.manager


async def load_dashboard_data() -> Dict[str, Any]:
    """Load all dashboard data"""
    mgr = get_manager()
    user = await ensure_dashboard_user(mgr, st.session_state.current_user)
    user_id = user.id

    # Load various data
    all_tasks_query = TaskQuery(limit=1000)
    all_tasks = await mgr.search_tasks(all_tasks_query, user_id)

    # Calculate metrics
    now = datetime.now(timezone.utc)
    overdue_tasks = [t for t in all_tasks if is_overdue_task(t, now)]
    upcoming_tasks = [t for t in all_tasks if is_upcoming_task(t, now=now)]

    stats = {
        "total_tasks": len(all_tasks),
        "completed_tasks": len([t for t in all_tasks if t.status == TaskStatus.DONE]),
        "in_progress_tasks": len(
            [t for t in all_tasks if t.status == TaskStatus.IN_PROGRESS]
        ),
        "overdue_tasks": len(overdue_tasks),
        "completion_rate": (
            len([t for t in all_tasks if t.status == TaskStatus.DONE]) / len(all_tasks)
            if all_tasks
            else 0
        ),
    }

    return {
        "all_tasks": all_tasks,
        "overdue_tasks": overdue_tasks,
        "upcoming_tasks": upcoming_tasks,
        "stats": stats,
    }


def create_apple_metric_card(
    title: str, value: str, delta: str = None, color: str = "blue"
):
    """Create an Apple-style metric card"""
    color_map = {
        "blue": APPLE_COLORS["primary"],
        "green": APPLE_COLORS["success"],
        "orange": APPLE_COLORS["warning"],
        "red": APPLE_COLORS["error"],
        "purple": APPLE_COLORS["secondary"],
    }

    card_color = color_map.get(color, APPLE_COLORS["primary"])

    return f"""
    <div class="metric-card">
        <div class="big-metric" style="color: {card_color};">{value}</div>
        <div class="metric-label">{title}</div>
        {f'<div style="color: {APPLE_COLORS["success"]}; font-size: 0.875rem; margin-top: 0.25rem;">{delta}</div>' if delta else ''}
    </div>
    """


def create_apple_status_chart(tasks: List[Task]) -> go.Figure:
    """Create Apple-style task status distribution chart"""
    status_counts = {}
    for task in tasks:
        status = display_value(task.status)
        status_counts[status] = status_counts.get(status, 0) + 1

    fig = px.pie(
        values=list(status_counts.values()),
        names=list(status_counts.keys()),
        title="Task Status",
        color_discrete_map={
            "todo": APPLE_COLORS["warning"],
            "in_progress": APPLE_COLORS["primary"],
            "blocked": APPLE_COLORS["error"],
            "review": APPLE_COLORS["secondary"],
            "done": APPLE_COLORS["success"],
            "cancelled": APPLE_COLORS["text_secondary"],
        },
    )

    fig.update_layout(
        height=350,
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", size=14
        ),
        title_font_size=18,
        title_font_color=APPLE_COLORS["text_primary"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5),
    )

    return fig


def create_apple_priority_chart(tasks: List[Task]) -> go.Figure:
    """Create Apple-style task priority distribution chart"""
    priority_counts = {}
    for task in tasks:
        priority = display_value(task.priority)
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    fig = px.bar(
        x=list(priority_counts.keys()),
        y=list(priority_counts.values()),
        title="Task Priority",
        color=list(priority_counts.keys()),
        color_discrete_map={
            "critical": APPLE_COLORS["error"],
            "high": APPLE_COLORS["warning"],
            "medium": APPLE_COLORS["secondary"],
            "low": APPLE_COLORS["success"],
        },
    )

    fig.update_layout(
        height=350,
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", size=14
        ),
        title_font_size=18,
        title_font_color=APPLE_COLORS["text_primary"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(title="", gridcolor=APPLE_COLORS["border"]),
        yaxis=dict(title="Tasks", gridcolor=APPLE_COLORS["border"]),
    )

    fig.update_traces(marker_line_width=0)
    return fig


def render_apple_task_table(tasks: List[Task], title: str):
    """Render an Apple-style task table"""
    if not tasks:
        st.markdown(
            f'<div class="glass-panel"><p style="text-align: center; color: {APPLE_COLORS["text_secondary"]};">No {title.lower()} found.</p></div>',
            unsafe_allow_html=True,
        )
        return

    # Convert tasks to DataFrame
    task_data = []
    for task in tasks:
        task_data.append(
            {
                "ID": task.id[:8],
                "Title": task.title,
                "Status": display_value(task.status),
                "Priority": display_value(task.priority),
                "Progress": f"{task.progress}%",
                "Due Date": task.due_date.strftime("%m/%d") if task.due_date else "—",
                "Created": task.created_at.strftime("%m/%d"),
            }
        )

    df = pd.DataFrame(task_data)

    st.markdown(f'<h3 class="section-header">{title}</h3>', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)


def main():
    """Main Apple-inspired dashboard application"""
    # Header with Apple-style design
    st.markdown(
        '<h1 style="text-align: center; margin-bottom: 2rem;">⚡ TaskForge</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="text-align: center; color: #8E8E93; font-size: 1.2rem; margin-bottom: 3rem;">Beautifully designed task management</p>',
        unsafe_allow_html=True,
    )

    # Sidebar navigation
    st.sidebar.markdown(
        '<h2 style="margin-bottom: 2rem;">Navigation</h2>', unsafe_allow_html=True
    )
    page = st.sidebar.selectbox(
        "",
        ["📊 Dashboard", "📋 Tasks", "📁 Projects", "📈 Analytics", "⚙️ Settings"],
        format_func=lambda x: x,
    )

    if page == "📊 Dashboard":
        render_dashboard_page()
    elif page == "📋 Tasks":
        render_tasks_page()
    elif page == "📁 Projects":
        render_projects_page()
    elif page == "📈 Analytics":
        render_analytics_page()
    elif page == "⚙️ Settings":
        render_settings_page()


def render_dashboard_page():
    """Render the main Apple-style dashboard page"""
    # Load data with loading indicator
    with st.spinner("Loading your workspace..."):
        try:
            data = asyncio.run(load_dashboard_data())
        except Exception as e:
            st.error(f"Unable to load data: {e}")
            return

    # Quick stats with Apple-style metric cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            create_apple_metric_card(
                "Total Tasks", str(data["stats"]["total_tasks"]), color="blue"
            ),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            create_apple_metric_card(
                "Completed",
                str(data["stats"]["completed_tasks"]),
                f"{data['stats']['completion_rate']:.0%} completion rate",
                color="green",
            ),
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            create_apple_metric_card(
                "In Progress", str(data["stats"]["in_progress_tasks"]), color="purple"
            ),
            unsafe_allow_html=True,
        )

    with col4:
        overdue_color = "red" if data["stats"]["overdue_tasks"] > 0 else "green"
        st.markdown(
            create_apple_metric_card(
                "Overdue", str(data["stats"]["overdue_tasks"]), color=overdue_color
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts section
    if data["all_tasks"]:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
            fig = create_apple_status_chart(data["all_tasks"])
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
            fig = create_apple_priority_chart(data["all_tasks"])
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # Task lists
    col1, col2 = st.columns(2)

    with col1:
        render_apple_task_table(data["overdue_tasks"][:10], "⚠️ Needs Attention")

    with col2:
        render_apple_task_table(data["upcoming_tasks"][:10], "📅 Coming Up")


def render_tasks_page():
    """Render the Apple-style tasks management page"""
    st.markdown(
        '<h2 class="section-header">📋 Task Management</h2>', unsafe_allow_html=True
    )

    # Task creation form with Apple design
    with st.expander("➕ Create New Task", expanded=False):
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)

        with st.form("create_task_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                title = st.text_input(
                    "Task Title", placeholder="What needs to be done?"
                )
                description = st.text_area(
                    "Description", placeholder="Add more details..."
                )
                due_date = st.date_input("Due Date")

            with col2:
                priority = st.selectbox("Priority", [p.value for p in TaskPriority])
                tags = st.text_input("Tags", placeholder="design, urgent, frontend")

            submitted = st.form_submit_button("Create Task", use_container_width=True)

            if submitted and title:
                try:
                    mgr = get_manager()
                    user = asyncio.run(
                        ensure_dashboard_user(mgr, st.session_state.current_user)
                    )
                    task = Task(
                        title=title,
                        description=description or None,
                        priority=TaskPriority(priority),
                        due_date=(
                            datetime.combine(
                                due_date, datetime.min.time(), tzinfo=timezone.utc
                            )
                            if due_date
                            else None
                        ),
                        assigned_to=user.id,
                        tags=set(tag.strip() for tag in tags.split(",") if tag.strip()),
                    )
                    created_task = asyncio.run(mgr.create_task(task, user.id))
                    st.success(f"✅ Task '{created_task.title}' created successfully!")
                except Exception as e:
                    st.error(f"❌ Error creating task: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

    # Search and filters
    st.markdown('<h3 class="section-header">🔍 Find Tasks</h3>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        search_text = st.text_input("Search", placeholder="Search tasks...")
    with col2:
        status_filter = st.multiselect("Status", [s.value for s in TaskStatus])
    with col3:
        priority_filter = st.multiselect("Priority", [p.value for p in TaskPriority])

    try:
        mgr = get_manager()
        user = asyncio.run(ensure_dashboard_user(mgr, st.session_state.current_user))
        query = TaskQuery(
            status=[TaskStatus(s) for s in status_filter] if status_filter else None,
            priority=(
                [TaskPriority(p) for p in priority_filter] if priority_filter else None
            ),
            search_text=search_text or None,
            limit=100,
        )
        tasks = asyncio.run(mgr.search_tasks(query, user.id))
        render_apple_task_table(tasks, f"Your Tasks ({len(tasks)})")
    except Exception as e:
        st.error(f"Unable to load tasks: {e}")


def render_projects_page():
    """Render the Apple-style projects page"""
    st.markdown('<h2 class="section-header">📁 Projects</h2>', unsafe_allow_html=True)

    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown("### Coming Soon")
    st.markdown(
        "Project management features are being designed with the same beautiful Apple aesthetics."
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_analytics_page():
    """Render the Apple-style analytics page"""
    st.markdown('<h2 class="section-header">📈 Analytics</h2>', unsafe_allow_html=True)

    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown("### Advanced Analytics")
    st.markdown("Detailed insights and productivity metrics coming soon.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_settings_page():
    """Render the Apple-style settings page"""
    st.markdown('<h2 class="section-header">⚙️ Settings</h2>', unsafe_allow_html=True)

    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.markdown("### Appearance")
    st.selectbox("Theme", ["Light", "Dark", "Auto"])
    st.selectbox("Accent Color", ["Blue", "Purple", "Green", "Orange"])

    st.markdown("### Notifications")
    st.checkbox("Email notifications", value=True)
    st.checkbox("Push notifications", value=True)
    st.checkbox("Due date reminders", value=True)

    if st.button("Save Settings", use_container_width=True):
        st.success("✅ Settings saved successfully!")

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
