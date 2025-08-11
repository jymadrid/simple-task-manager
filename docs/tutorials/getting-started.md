# Getting Started with TaskForge

Welcome to TaskForge! This tutorial will guide you through setting up and using TaskForge for personal productivity, team collaboration, and project management.

## Table of Contents

1. [Installation](#installation)
2. [Basic Setup](#basic-setup)
3. [Your First Task](#your-first-task)
4. [Project Organization](#project-organization)
5. [Team Collaboration](#team-collaboration)
6. [Advanced Features](#advanced-features)
7. [Integration Setup](#integration-setup)
8. [Next Steps](#next-steps)

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
# Install TaskForge with basic features
pip install taskforge

# Install with all features (recommended for teams)
pip install taskforge[all]

# Install specific feature sets
pip install taskforge[web,integrations,postgres]
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/taskforge-community/taskforge.git
cd taskforge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Check TaskForge version
taskforge --version

# View available commands
taskforge --help
```

## Basic Setup

### Initialize TaskForge

```bash
# Initialize TaskForge in your current directory
taskforge init

# Or specify a custom data directory
taskforge init --data-dir ~/taskforge-data
```

This creates:
- Configuration file (`taskforge.json`)
- Data directory for storing tasks and projects
- Initial user profile

### Configuration

Edit `taskforge.json` to customize your setup:

```json
{
  "storage": {
    "type": "json",
    "path": "./data"
  },
  "user": {
    "name": "Your Name",
    "email": "you@example.com",
    "timezone": "UTC"
  },
  "preferences": {
    "date_format": "YYYY-MM-DD",
    "time_format": "24h"
  }
}
```

## Your First Task

### Create a Simple Task

```bash
# Create a basic task
taskforge task add "Review project requirements"

# Create a task with more details
taskforge task add "Implement user authentication" \
  --description "Add login/logout functionality with JWT tokens" \
  --priority high \
  --due 2024-02-15 \
  --tags backend,security

# Create a task with time estimate
taskforge task add "Write unit tests" \
  --estimated-hours 4 \
  --priority medium
```

### View Your Tasks

```bash
# List all tasks
taskforge task list

# List only high priority tasks
taskforge task list --priority high

# List tasks due this week
taskforge task list --due-this-week

# Show task details
taskforge task show <task-id>
```

### Update Task Status

```bash
# Start working on a task
taskforge task start <task-id>

# Mark task as completed
taskforge task complete <task-id>

# Add notes to a task
taskforge task note <task-id> "Completed authentication middleware"
```

## Project Organization

### Create Your First Project

```bash
# Create a project
taskforge project create "Web Application" \
  --description "E-commerce web application with React and FastAPI" \
  --tags web,react,python

# List projects
taskforge project list

# Show project details
taskforge project show <project-id>
```

### Organize Tasks by Project

```bash
# Add task to specific project
taskforge task add "Design database schema" \
  --project "Web Application" \
  --priority high \
  --estimated-hours 6

# List tasks for a project
taskforge task list --project "Web Application"

# Show project progress
taskforge project progress <project-id>
```

### Project Templates

Create reusable project templates:

```bash
# Create from template
taskforge project create-from-template web-app "My New Project"

# Create your own template
taskforge template create my-template \
  --from-project <project-id> \
  --description "Custom template for web projects"
```

## Team Collaboration

### Share Projects

```bash
# Add team member to project
taskforge project add-member <project-id> colleague@company.com

# Assign task to team member
taskforge task assign <task-id> colleague@company.com

# Set up notifications
taskforge config set notifications.email.enabled true
taskforge config set notifications.slack.webhook_url https://hooks.slack.com/...
```

### Collaborative Workflows

1. **Daily Standup Reports**
```bash
# Generate daily status report
taskforge report daily --user colleague@company.com

# Generate team summary
taskforge report team --project <project-id>
```

2. **Task Dependencies**
```bash
# Create dependent tasks
taskforge task add "Implement API endpoints" --after <design-task-id>
taskforge task add "Write API tests" --after <implement-task-id>

# View dependency chain
taskforge task dependencies <task-id>
```

3. **Comments and Communication**
```bash
# Add comment to task
taskforge task comment <task-id> "Updated the authentication logic"

# Mention team member
taskforge task comment <task-id> "@colleague Please review this approach"

# View task conversation
taskforge task conversation <task-id>
```

## Advanced Features

### Time Tracking

```bash
# Start time tracking
taskforge task start <task-id>

# Stop time tracking
taskforge task stop <task-id>

# Log time manually
taskforge task log-time <task-id> 2h30m "Working on user interface"

# View time reports
taskforge report time --user me --last-week
```

### Custom Fields and Tags

```bash
# Add custom fields to tasks
taskforge task update <task-id> \
  --custom-field "Client=Acme Corp" \
  --custom-field "Billable=true"

# Advanced tagging
taskforge task add "Client meeting" \
  --tags client,meeting,acme-corp \
  --custom-field "Meeting-Type=Discovery"

# Search by custom fields
taskforge task search --custom-field "Client=Acme Corp"
```

### Recurring Tasks

```bash
# Create daily recurring task
taskforge task add "Daily standup" \
  --recurrence daily \
  --time "09:00"

# Create weekly recurring task
taskforge task add "Team retrospective" \
  --recurrence weekly \
  --day friday \
  --time "15:00"

# Create monthly recurring task
taskforge task add "Monthly planning" \
  --recurrence monthly \
  --day-of-month 1 \
  --time "10:00"
```

### Advanced Searching and Filtering

```bash
# Complex search queries
taskforge task search "authentication OR security" \
  --priority high \
  --status todo \
  --tags backend

# Date range filtering
taskforge task list \
  --created-after 2024-01-01 \
  --due-before 2024-03-01

# Advanced filters
taskforge task list \
  --assigned-to me \
  --no-due-date \
  --estimated-hours-min 4
```

## Integration Setup

### GitHub Integration

```bash
# Configure GitHub integration
taskforge integration add github \
  --token <your-github-token> \
  --repo owner/repository

# Sync issues
taskforge integration sync github

# Create GitHub issue from task
taskforge task create-issue <task-id>
```

### Slack Integration

```bash
# Configure Slack
taskforge integration add slack \
  --webhook-url <webhook-url> \
  --channel "#development"

# Enable notifications
taskforge config set notifications.slack.task_completed true
taskforge config set notifications.slack.task_overdue true
```

### Calendar Integration

```bash
# Sync with Google Calendar
taskforge integration add google-calendar \
  --credentials-file ~/google-credentials.json

# Create calendar events for tasks with due dates
taskforge calendar sync --project <project-id>
```

### Trello Import

```bash
# Import from Trello
taskforge import trello \
  --board-url <trello-board-url> \
  --api-key <trello-api-key> \
  --token <trello-token>
```

## Web Interface

### Launch Web Dashboard

```bash
# Start web interface
taskforge web

# Custom port and host
taskforge web --port 8080 --host 0.0.0.0

# Production mode
taskforge web --production
```

The web interface provides:
- Interactive task board (Kanban view)
- Calendar view with due dates
- Team collaboration features
- Analytics and reporting
- Project timeline view

### API Server

```bash
# Start REST API server
taskforge serve --host 0.0.0.0 --port 8000

# Enable API documentation
taskforge serve --docs

# Production deployment
taskforge serve --workers 4 --reload false
```

API endpoints include:
- `/api/v1/tasks` - Task management
- `/api/v1/projects` - Project operations
- `/api/v1/users` - User management
- `/api/v1/reports` - Analytics and reporting

## Workflow Examples

### Personal Productivity Workflow

```bash
# Morning routine
taskforge task list --due-today           # Check today's tasks
taskforge task list --priority high       # Review high priority items
taskforge task start <urgent-task-id>     # Start most important task

# During the day
taskforge task note <task-id> "Progress update"  # Add progress notes
taskforge task log-time <task-id> 1h30m          # Log time spent

# Evening review
taskforge task complete <completed-task-id>      # Mark completed tasks
taskforge report daily --user me                 # Review daily progress
```

### Team Project Workflow

```bash
# Project setup
taskforge project create "Q1 Product Launch"
taskforge project add-member <project-id> team@company.com

# Sprint planning
taskforge task add "User story: Login flow" --project <project-id> --story-points 5
taskforge task add "Bug fix: Payment validation" --project <project-id> --priority high

# Daily coordination
taskforge report team --project <project-id>     # Team status
taskforge task list --assigned-to me --in-progress  # My active tasks

# Sprint review
taskforge report sprint --project <project-id> --last-week
```

### Freelancer/Client Workflow

```bash
# Client project setup
taskforge project create "Client ABC - Website Redesign" \
  --custom-field "Client=ABC Corp" \
  --custom-field "Rate=75/hour"

# Billable time tracking
taskforge task add "Design mockups" --project <project-id> --billable
taskforge task start <task-id>  # Start timer automatically
taskforge task complete <task-id>  # Stop timer and mark complete

# Generate invoices
taskforge report billing --project <project-id> --month 2024-02
```

## Next Steps

### Explore Advanced Features

1. **Plugin Development**
   - Create custom integrations
   - Build workflow automation
   - Extend TaskForge functionality

2. **Enterprise Features**
   - Multi-tenant deployment
   - LDAP/SSO integration
   - Advanced security and compliance

3. **Automation and Scripting**
   - Use Python API for automation
   - Create custom CLI commands
   - Build integrations with your tools

### Learn More

- **Documentation**: [https://docs.taskforge.dev](https://docs.taskforge.dev)
- **Examples**: Check the `examples/` directory in your installation
- **Community**: Join our Discord server for support and discussions
- **Contribute**: Visit our GitHub repository to contribute

### Get Support

- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions in GitHub Discussions
- **Community**: Join our Discord community
- **Enterprise**: Contact enterprise@taskforge.dev for business inquiries

### Sample Workflows to Try

1. **Personal GTD (Getting Things Done)**
   ```bash
   # Set up GTD contexts
   taskforge task add "Review meeting notes" --context @computer --energy-level high
   taskforge task add "Call client" --context @phone --energy-level medium
   
   # Weekly review
   taskforge task list --status todo --sort-by priority
   ```

2. **Agile Development**
   ```bash
   # Sprint setup
   taskforge project create "Sprint 23" --start-date 2024-02-01 --end-date 2024-02-14
   
   # User stories with acceptance criteria
   taskforge task add "As a user, I want to reset my password" \
     --acceptance-criteria "Email sent, link expires in 24h, password updated"
   ```

3. **Content Creation**
   ```bash
   # Content calendar
   taskforge project create "Blog Content Q1"
   taskforge task add "Write 'Getting Started with TaskForge'" --due 2024-02-15
   taskforge task add "Create tutorial videos" --estimated-hours 8 --due 2024-02-28
   ```

Happy task management with TaskForge! 🚀