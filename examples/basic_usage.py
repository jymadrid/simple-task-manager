#!/usr/bin/env python3
"""
Basic TaskForge Usage Examples
==============================

This example demonstrates the fundamental features of TaskForge,
including task creation, management, and basic workflows.

Great for: New users, quick start guides, documentation examples
"""

import asyncio
from datetime import datetime, timedelta
from taskforge import TaskManager, Task, Project, TaskPriority, TaskStatus
from taskforge.storage import JsonStorage


async def basic_task_operations():
    """Demonstrate basic task CRUD operations."""
    print("🚀 TaskForge Basic Operations Demo")
    print("=" * 40)
    
    # Initialize storage and manager
    storage = JsonStorage("./examples_data/basic")
    await storage.initialize()
    manager = TaskManager(storage)
    
    # Create a user (in real apps, this would be handled by auth)
    user_id = "demo_user"
    
    print("\n1. Creating tasks...")
    
    # Create various types of tasks
    tasks = [
        Task(
            title="Set up development environment",
            description="Install Python, IDE, and required dependencies",
            priority=TaskPriority.HIGH,
            due_date=datetime.now() + timedelta(days=1)
        ),
        Task(
            title="Write project documentation",
            description="Create README, API docs, and user guide",
            priority=TaskPriority.MEDIUM,
            tags=["documentation", "writing"]
        ),
        Task(
            title="Implement core features",
            description="Build the main functionality of the application",
            priority=TaskPriority.HIGH,
            estimated_hours=8
        ),
        Task(
            title="Write unit tests",
            description="Create comprehensive test coverage",
            priority=TaskPriority.MEDIUM,
            tags=["testing", "quality"]
        ),
        Task(
            title="Deploy to production",
            description="Set up CI/CD and deploy the application",
            priority=TaskPriority.LOW,
            due_date=datetime.now() + timedelta(days=7)
        )
    ]
    
    created_tasks = []
    for task in tasks:
        created_task = await manager.create_task(task, user_id)
        created_tasks.append(created_task)
        print(f"   ✅ Created: {created_task.title}")
    
    print(f"\n2. Listing all tasks (Total: {len(created_tasks)})")
    all_tasks = await manager.get_user_tasks(user_id)
    for task in all_tasks:
        status_icon = "⏳" if task.status == TaskStatus.TODO else "✅"
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority.value, "⚪")
        print(f"   {status_icon} {priority_icon} {task.title}")
    
    print("\n3. Filtering tasks by priority...")
    from taskforge.core.manager import TaskQuery
    
    high_priority_query = TaskQuery(priority=[TaskPriority.HIGH])
    high_priority_tasks = await manager.search_tasks(high_priority_query, user_id)
    print(f"   High priority tasks: {len(high_priority_tasks)}")
    for task in high_priority_tasks:
        print(f"   🔴 {task.title}")
    
    print("\n4. Updating task status...")
    # Complete the first task
    first_task = created_tasks[0]
    updated_task = await manager.update_task_status(
        first_task.id, TaskStatus.COMPLETED, user_id
    )
    print(f"   ✅ Completed: {updated_task.title}")
    
    # Start working on second task
    second_task = created_tasks[1]
    in_progress_task = await manager.update_task_status(
        second_task.id, TaskStatus.IN_PROGRESS, user_id
    )
    print(f"   🔄 Started: {in_progress_task.title}")
    
    print("\n5. Adding task notes...")
    await manager.add_task_note(
        second_task.id,
        "Started working on README.md file. Added installation instructions.",
        user_id
    )
    print(f"   📝 Added note to: {second_task.title}")
    
    print("\n6. Task statistics...")
    stats = await manager.get_task_statistics(user_id)
    print(f"   📊 Total tasks: {stats.get('total', 0)}")
    print(f"   ⏳ Todo: {stats.get('todo', 0)}")
    print(f"   🔄 In Progress: {stats.get('in_progress', 0)}")
    print(f"   ✅ Completed: {stats.get('completed', 0)}")
    
    print("\n✨ Basic operations demo completed!")
    return created_tasks


async def project_management_example():
    """Demonstrate project-based task organization."""
    print("\n\n🏗️ Project Management Demo")
    print("=" * 30)
    
    storage = JsonStorage("./examples_data/projects")
    await storage.initialize()
    manager = TaskManager(storage)
    
    user_id = "project_user"
    
    print("\n1. Creating a project...")
    
    # Create a web application project
    project = Project(
        name="TaskForge Web App",
        description="A modern web application for task management with real-time collaboration",
        tags=["web", "python", "react"],
        metadata={
            "tech_stack": ["Python", "FastAPI", "React", "PostgreSQL"],
            "team_size": 5,
            "deadline": "2024-06-01"
        }
    )
    
    created_project = await manager.create_project(project, user_id)
    print(f"   ✅ Created project: {created_project.name}")
    
    print("\n2. Adding project tasks...")
    
    # Create project-specific tasks
    project_tasks = [
        Task(
            title="Design system architecture",
            description="Create detailed system design and database schema",
            priority=TaskPriority.HIGH,
            project_id=created_project.id,
            tags=["architecture", "design"],
            estimated_hours=16
        ),
        Task(
            title="Set up backend API",
            description="Implement FastAPI backend with authentication and core endpoints",
            priority=TaskPriority.HIGH,
            project_id=created_project.id,
            tags=["backend", "api"],
            estimated_hours=32
        ),
        Task(
            title="Create React frontend",
            description="Build responsive UI with task management interface",
            priority=TaskPriority.HIGH,
            project_id=created_project.id,
            tags=["frontend", "ui"],
            estimated_hours=40
        ),
        Task(
            title="Implement real-time features",
            description="Add WebSocket support for live collaboration",
            priority=TaskPriority.MEDIUM,
            project_id=created_project.id,
            tags=["websocket", "collaboration"],
            estimated_hours=24
        ),
        Task(
            title="Deploy to production",
            description="Set up CI/CD pipeline and production deployment",
            priority=TaskPriority.MEDIUM,
            project_id=created_project.id,
            tags=["deployment", "devops"],
            estimated_hours=16
        )
    ]
    
    created_project_tasks = []
    total_estimated_hours = 0
    for task in project_tasks:
        created_task = await manager.create_task(task, user_id)
        created_project_tasks.append(created_task)
        total_estimated_hours += task.estimated_hours or 0
        print(f"   ✅ Added: {created_task.title} ({task.estimated_hours}h)")
    
    print(f"\n3. Project overview...")
    print(f"   📋 Total tasks: {len(created_project_tasks)}")
    print(f"   ⏱️ Total estimated hours: {total_estimated_hours}")
    
    # Get project tasks
    project_tasks_list = await manager.get_project_tasks(created_project.id, user_id)
    print(f"   🎯 Project tasks: {len(project_tasks_list)}")
    
    print("\n4. Simulating project progress...")
    
    # Complete first task
    first_task = created_project_tasks[0]
    await manager.update_task_status(first_task.id, TaskStatus.COMPLETED, user_id)
    await manager.add_task_note(
        first_task.id,
        "Architecture design completed. Using microservices pattern with FastAPI and React.",
        user_id
    )
    print(f"   ✅ Completed: {first_task.title}")
    
    # Start second task
    second_task = created_project_tasks[1]
    await manager.update_task_status(second_task.id, TaskStatus.IN_PROGRESS, user_id)
    print(f"   🔄 Started: {second_task.title}")
    
    print("\n5. Project progress report...")
    completed_tasks = [t for t in project_tasks_list if t.status == TaskStatus.COMPLETED]
    in_progress_tasks = [t for t in project_tasks_list if t.status == TaskStatus.IN_PROGRESS]
    todo_tasks = [t for t in project_tasks_list if t.status == TaskStatus.TODO]
    
    progress_percentage = (len(completed_tasks) / len(project_tasks_list)) * 100
    print(f"   📈 Progress: {progress_percentage:.1f}%")
    print(f"   ✅ Completed: {len(completed_tasks)}")
    print(f"   🔄 In Progress: {len(in_progress_tasks)}")
    print(f"   ⏳ Todo: {len(todo_tasks)}")
    
    print("\n✨ Project management demo completed!")
    return created_project, created_project_tasks


async def advanced_querying_example():
    """Demonstrate advanced task searching and filtering."""
    print("\n\n🔍 Advanced Querying Demo")
    print("=" * 30)
    
    storage = JsonStorage("./examples_data/advanced")
    await storage.initialize()
    manager = TaskManager(storage)
    
    user_id = "power_user"
    
    # Create a variety of tasks for demonstration
    sample_tasks = [
        Task(title="Fix critical bug", priority=TaskPriority.HIGH, tags=["bug", "urgent"]),
        Task(title="Add user authentication", priority=TaskPriority.HIGH, tags=["feature", "security"]),
        Task(title="Write documentation", priority=TaskPriority.MEDIUM, tags=["docs", "writing"]),
        Task(title="Optimize database queries", priority=TaskPriority.MEDIUM, tags=["performance", "database"]),
        Task(title="Update dependencies", priority=TaskPriority.LOW, tags=["maintenance", "security"]),
        Task(title="Design new logo", priority=TaskPriority.LOW, tags=["design", "branding"]),
    ]
    
    print("\n1. Creating sample tasks...")
    created_tasks = []
    for task in sample_tasks:
        task.due_date = datetime.now() + timedelta(days=len(created_tasks) + 1)
        created_task = await manager.create_task(task, user_id)
        created_tasks.append(created_task)
    
    print(f"   ✅ Created {len(created_tasks)} tasks")
    
    print("\n2. Querying examples...")
    
    from taskforge.core.manager import TaskQuery
    
    # Query by priority
    high_priority_query = TaskQuery(priority=[TaskPriority.HIGH])
    high_tasks = await manager.search_tasks(high_priority_query, user_id)
    print(f"   🔴 High priority tasks: {len(high_tasks)}")
    for task in high_tasks:
        print(f"      - {task.title}")
    
    # Query by tags
    security_query = TaskQuery(tags=["security"])
    security_tasks = await manager.search_tasks(security_query, user_id)
    print(f"   🔐 Security-related tasks: {len(security_tasks)}")
    for task in security_tasks:
        print(f"      - {task.title}")
    
    # Query by due date range
    upcoming_query = TaskQuery(
        due_date_from=datetime.now(),
        due_date_to=datetime.now() + timedelta(days=3)
    )
    upcoming_tasks = await manager.search_tasks(upcoming_query, user_id)
    print(f"   📅 Tasks due in next 3 days: {len(upcoming_tasks)}")
    for task in upcoming_tasks:
        print(f"      - {task.title} (due: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No due date'})")
    
    # Complex query combining multiple criteria
    complex_query = TaskQuery(
        priority=[TaskPriority.HIGH, TaskPriority.MEDIUM],
        tags=["feature", "bug", "security"],
        status=[TaskStatus.TODO]
    )
    complex_results = await manager.search_tasks(complex_query, user_id)
    print(f"   🎯 High/Medium priority feature/bug/security tasks: {len(complex_results)}")
    for task in complex_results:
        priority_icon = {"high": "🔴", "medium": "🟡"}.get(task.priority.value, "⚪")
        print(f"      - {priority_icon} {task.title} [{', '.join(task.tags)}]")
    
    print("\n✨ Advanced querying demo completed!")
    return created_tasks


async def collaboration_example():
    """Demonstrate team collaboration features."""
    print("\n\n👥 Team Collaboration Demo")
    print("=" * 32)
    
    storage = JsonStorage("./examples_data/collaboration")
    await storage.initialize()
    manager = TaskManager(storage)
    
    # Simulate multiple team members
    team_members = ["alice", "bob", "charlie", "diana"]
    
    print("\n1. Setting up team project...")
    
    # Create a shared project
    project = Project(
        name="Open Source TaskForge Plugin",
        description="Develop a Slack integration plugin for TaskForge",
        tags=["plugin", "integration", "slack"],
        metadata={
            "repository": "https://github.com/taskforge-community/slack-plugin",
            "team_lead": "alice",
            "target_release": "v1.0.0"
        }
    )
    
    team_project = await manager.create_project(project, team_members[0])
    print(f"   ✅ Created team project: {team_project.name}")
    
    print("\n2. Assigning tasks to team members...")
    
    team_tasks = [
        ("Research Slack API capabilities", team_members[0], TaskPriority.HIGH),
        ("Design plugin architecture", team_members[1], TaskPriority.HIGH),
        ("Implement core functionality", team_members[0], TaskPriority.HIGH),
        ("Write comprehensive tests", team_members[2], TaskPriority.MEDIUM),
        ("Create user documentation", team_members[3], TaskPriority.MEDIUM),
        ("Set up CI/CD pipeline", team_members[1], TaskPriority.MEDIUM),
    ]
    
    assigned_tasks = []
    for task_title, assignee, priority in team_tasks:
        task = Task(
            title=task_title,
            description=f"Assigned to {assignee}",
            priority=priority,
            project_id=team_project.id,
            assigned_to=assignee,
            tags=["team-task"]
        )
        created_task = await manager.create_task(task, team_members[0])  # Created by team lead
        assigned_tasks.append((created_task, assignee))
        print(f"   👤 Assigned to {assignee}: {task_title}")
    
    print("\n3. Simulating collaborative work...")
    
    # Alice starts working and adds updates
    alice_task = assigned_tasks[0][0]  # Research task
    await manager.update_task_status(alice_task.id, TaskStatus.IN_PROGRESS, team_members[0])
    await manager.add_task_note(
        alice_task.id,
        "Started reviewing Slack API documentation. Found useful endpoints for messaging and user management.",
        team_members[0]
    )
    print(f"   🔄 Alice started: {alice_task.title}")
    
    # Bob provides input on Alice's research
    await manager.add_task_note(
        alice_task.id,
        "@alice Great findings! I think we should focus on the Events API for real-time notifications.",
        team_members[1]
    )
    print(f"   💬 Bob commented on Alice's task")
    
    # Charlie completes his task
    charlie_task = assigned_tasks[3][0]  # Testing task
    await manager.update_task_status(charlie_task.id, TaskStatus.COMPLETED, team_members[2])
    await manager.add_task_note(
        charlie_task.id,
        "Completed comprehensive test suite with 95% coverage. All tests passing.",
        team_members[2]
    )
    print(f"   ✅ Charlie completed: {charlie_task.title}")
    
    print("\n4. Team progress overview...")
    
    # Get all project tasks
    all_project_tasks = await manager.get_project_tasks(team_project.id, team_members[0])
    
    # Calculate team statistics
    team_stats = {}
    for member in team_members:
        member_tasks = [t for t in all_project_tasks if t.assigned_to == member]
        completed = len([t for t in member_tasks if t.status == TaskStatus.COMPLETED])
        in_progress = len([t for t in member_tasks if t.status == TaskStatus.IN_PROGRESS])
        total = len(member_tasks)
        team_stats[member] = {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "completion_rate": (completed / total * 100) if total > 0 else 0
        }
    
    for member, stats in team_stats.items():
        print(f"   👤 {member.title()}: {stats['completed']}/{stats['total']} tasks "
              f"({stats['completion_rate']:.1f}% complete)")
    
    # Project overall progress
    total_tasks = len(all_project_tasks)
    completed_tasks = len([t for t in all_project_tasks if t.status == TaskStatus.COMPLETED])
    project_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    print(f"\n   📊 Project Progress: {completed_tasks}/{total_tasks} tasks ({project_progress:.1f}%)")
    
    print("\n✨ Team collaboration demo completed!")
    return team_project, assigned_tasks


async def automation_example():
    """Demonstrate automation and recurring tasks."""
    print("\n\n🤖 Automation & Recurring Tasks Demo")
    print("=" * 38)
    
    storage = JsonStorage("./examples_data/automation")
    await storage.initialize()
    manager = TaskManager(storage)
    
    user_id = "automation_user"
    
    print("\n1. Setting up recurring tasks...")
    
    # Daily standup meeting
    daily_standup = Task(
        title="Daily team standup meeting",
        description="Quick sync with the team on progress and blockers",
        priority=TaskPriority.MEDIUM,
        tags=["meeting", "daily"],
        recurrence_pattern="daily",
        estimated_hours=0.5,
        metadata={
            "meeting_url": "https://meet.google.com/abc-def-ghi",
            "participants": ["alice", "bob", "charlie", "diana"]
        }
    )
    
    recurring_standup = await manager.create_task(daily_standup, user_id)
    print(f"   🔄 Created daily recurring task: {recurring_standup.title}")
    
    # Weekly code review
    weekly_review = Task(
        title="Weekly code review session",
        description="Review pull requests and discuss code quality improvements",
        priority=TaskPriority.HIGH,
        tags=["review", "weekly", "code-quality"],
        recurrence_pattern="weekly",
        due_date=datetime.now() + timedelta(days=7),
        estimated_hours=2
    )
    
    recurring_review = await manager.create_task(weekly_review, user_id)
    print(f"   📅 Created weekly recurring task: {recurring_review.title}")
    
    # Monthly planning
    monthly_planning = Task(
        title="Monthly sprint planning",
        description="Plan and prioritize tasks for the upcoming month",
        priority=TaskPriority.HIGH,
        tags=["planning", "monthly", "strategy"],
        recurrence_pattern="monthly",
        estimated_hours=4,
        metadata={
            "meeting_type": "planning",
            "outcomes_required": ["backlog_prioritization", "capacity_planning", "risk_assessment"]
        }
    )
    
    recurring_planning = await manager.create_task(monthly_planning, user_id)
    print(f"   📊 Created monthly recurring task: {recurring_planning.title}")
    
    print("\n2. Demonstrating task dependencies...")
    
    # Create a chain of dependent tasks
    dependency_tasks = [
        Task(
            title="Design API endpoints",
            description="Define REST API structure and documentation",
            priority=TaskPriority.HIGH,
            tags=["design", "api"],
            estimated_hours=8
        ),
        Task(
            title="Implement API backend",
            description="Code the API endpoints using FastAPI",
            priority=TaskPriority.HIGH,
            tags=["implementation", "backend"],
            estimated_hours=16
        ),
        Task(
            title="Write API tests",
            description="Create comprehensive test suite for API endpoints",
            priority=TaskPriority.HIGH,
            tags=["testing", "api"],
            estimated_hours=8
        ),
        Task(
            title="Deploy to staging",
            description="Deploy API to staging environment for testing",
            priority=TaskPriority.MEDIUM,
            tags=["deployment", "staging"],
            estimated_hours=4
        )
    ]
    
    created_dep_tasks = []
    for i, task in enumerate(dependency_tasks):
        created_task = await manager.create_task(task, user_id)
        created_dep_tasks.append(created_task)
        
        # Set up dependencies (each task depends on the previous one)
        if i > 0:
            await manager.add_task_dependency(
                created_task.id,
                created_dep_tasks[i-1].id,
                user_id
            )
            print(f"   🔗 {created_task.title} depends on: {created_dep_tasks[i-1].title}")
        else:
            print(f"   ✅ Created initial task: {created_task.title}")
    
    print("\n3. Simulating automated workflow...")
    
    # Complete first task to unblock the next one
    first_task = created_dep_tasks[0]
    await manager.update_task_status(first_task.id, TaskStatus.COMPLETED, user_id)
    await manager.add_task_note(
        first_task.id,
        "API design completed. Documentation available at /docs/api-design.md",
        user_id
    )
    print(f"   ✅ Completed: {first_task.title}")
    
    # Start second task (now unblocked)
    second_task = created_dep_tasks[1]
    await manager.update_task_status(second_task.id, TaskStatus.IN_PROGRESS, user_id)
    print(f"   🔄 Started: {second_task.title} (dependency satisfied)")
    
    print("\n4. Automation rules simulation...")
    
    # Simulate automatic task creation based on conditions
    auto_tasks = []
    
    # If a critical bug is reported, automatically create related tasks
    bug_report = Task(
        title="Critical: Database connection timeout",
        description="Users reporting inability to save data",
        priority=TaskPriority.HIGH,
        tags=["bug", "critical", "database"],
        estimated_hours=4
    )
    
    bug_task = await manager.create_task(bug_report, user_id)
    auto_tasks.append(bug_task)
    print(f"   🚨 Auto-created critical bug task: {bug_task.title}")
    
    # Auto-create related tasks for critical bugs
    related_tasks = [
        Task(
            title="Investigate database connection issues",
            description="Analyze logs and connection pool settings",
            priority=TaskPriority.HIGH,
            tags=["investigation", "database"],
            estimated_hours=2
        ),
        Task(
            title="Prepare hotfix for database timeout",
            description="Implement and test fix for connection timeout",
            priority=TaskPriority.HIGH,
            tags=["hotfix", "database"],
            estimated_hours=3
        ),
        Task(
            title="Deploy hotfix to production",
            description="Roll out the database timeout fix",
            priority=TaskPriority.HIGH,
            tags=["deployment", "hotfix"],
            estimated_hours=1
        )
    ]
    
    for related_task in related_tasks:
        created_related = await manager.create_task(related_task, user_id)
        auto_tasks.append(created_related)
        print(f"   🤖 Auto-created related task: {created_related.title}")
    
    print(f"\n5. Automation summary...")
    print(f"   🔄 Recurring tasks created: 3")
    print(f"   🔗 Task dependencies set up: {len(created_dep_tasks) - 1}")
    print(f"   🤖 Auto-generated tasks: {len(auto_tasks)}")
    print(f"   ⚡ Total automated workflow items: {3 + len(created_dep_tasks) + len(auto_tasks)}")
    
    print("\n✨ Automation demo completed!")
    return {
        "recurring": [recurring_standup, recurring_review, recurring_planning],
        "dependencies": created_dep_tasks,
        "automated": auto_tasks
    }


async def main():
    """Run all examples in sequence."""
    print("🎯 TaskForge Comprehensive Examples")
    print("=" * 50)
    print("This demo showcases TaskForge's capabilities for various use cases:")
    print("- Individual productivity")
    print("- Team collaboration") 
    print("- Project management")
    print("- Advanced automation")
    print("=" * 50)
    
    try:
        # Run all examples
        basic_results = await basic_task_operations()
        project_results = await project_management_example()
        query_results = await advanced_querying_example()
        collab_results = await collaboration_example()
        automation_results = await automation_example()
        
        print("\n\n🎉 All Examples Completed Successfully!")
        print("=" * 45)
        print(f"✅ Basic operations: {len(basic_results)} tasks created")
        print(f"🏗️ Project management: 1 project, {len(project_results[1])} tasks")
        print(f"🔍 Advanced querying: {len(query_results)} sample tasks")
        print(f"👥 Team collaboration: 1 project, {len(collab_results[1])} team tasks")
        print(f"🤖 Automation features: {len(automation_results['recurring']) + len(automation_results['dependencies']) + len(automation_results['automated'])} total items")
        
        print("\n💡 Next steps:")
        print("- Explore the created data in ./examples_data/")
        print("- Try modifying tasks and running queries")
        print("- Check out the TaskForge CLI: `taskforge --help`")
        print("- Start the web interface: `taskforge web`")
        print("- Read the documentation: https://docs.taskforge.dev")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("Please check your TaskForge installation and try again.")


if __name__ == "__main__":
    asyncio.run(main())