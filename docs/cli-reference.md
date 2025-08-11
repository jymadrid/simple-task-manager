# TaskForge CLI Reference

Complete command-line interface reference for TaskForge task management system.

## Table of Contents

- [Global Options](#global-options)
- [Task Commands](#task-commands)
- [Project Commands](#project-commands)
- [User Commands](#user-commands)
- [Report Commands](#report-commands)
- [Integration Commands](#integration-commands)
- [Configuration Commands](#configuration-commands)
- [Import/Export Commands](#importexport-commands)
- [Server Commands](#server-commands)
- [Plugin Commands](#plugin-commands)

## Global Options

These options can be used with any command:

```bash
--config PATH          Path to configuration file (default: ./taskforge.json)
--data-dir PATH        Data directory path (default: ./data)
--verbose, -v          Verbose output
--quiet, -q           Suppress non-essential output
--format FORMAT       Output format: table, json, csv, yaml (default: table)
--no-color            Disable colored output
--help, -h            Show help message
--version             Show version information
```

## Task Commands

### `taskforge task add`

Create a new task.

```bash
taskforge task add "Task title" [OPTIONS]

Options:
  --description TEXT           Task description
  --priority PRIORITY          Priority: low, medium, high (default: medium)
  --due DATE                   Due date (YYYY-MM-DD or relative like 'tomorrow')
  --project PROJECT            Project name or ID
  --tags TAGS                  Comma-separated tags
  --assigned-to EMAIL          Assign to user email
  --estimated-hours FLOAT      Estimated time in hours
  --story-points INTEGER       Story points for agile workflows
  --context TEXT               GTD context (e.g., @phone, @computer)
  --energy-level LEVEL         Energy level: low, medium, high
  --recurrence PATTERN         Recurrence pattern: daily, weekly, monthly
  --custom-field KEY=VALUE     Custom field (can be used multiple times)
  --billable                   Mark as billable time
  --template TEMPLATE          Create from template
```

Examples:
```bash
# Simple task
taskforge task add "Fix login bug"

# Detailed task
taskforge task add "Implement OAuth" \
  --description "Add Google and GitHub OAuth support" \
  --priority high \
  --due 2024-02-15 \
  --project "Web App" \
  --tags "authentication,oauth,security" \
  --estimated-hours 8

# Recurring task
taskforge task add "Daily standup" \
  --recurrence daily \
  --time "09:00" \
  --project "Development"
```

### `taskforge task list`

List and filter tasks.

```bash
taskforge task list [OPTIONS]

Options:
  --status STATUS              Filter by status: todo, in-progress, completed, cancelled
  --priority PRIORITY          Filter by priority: low, medium, high
  --project PROJECT            Filter by project name or ID
  --assigned-to EMAIL          Filter by assignee
  --tags TAGS                  Filter by tags (comma-separated)
  --due-today                  Show tasks due today
  --due-this-week             Show tasks due this week
  --due-before DATE           Show tasks due before date
  --due-after DATE            Show tasks due after date
  --overdue                   Show overdue tasks
  --no-due-date              Show tasks without due date
  --created-after DATE        Show tasks created after date
  --created-before DATE       Show tasks created before date
  --sort-by FIELD             Sort by: created, updated, due, priority, title
  --reverse                   Reverse sort order
  --limit INTEGER             Limit number of results
  --include-completed         Include completed tasks (default: false)
  --custom-field KEY=VALUE    Filter by custom field
```

Examples:
```bash
# All active tasks
taskforge task list --status todo,in-progress

# High priority tasks due this week
taskforge task list --priority high --due-this-week

# My tasks in progress
taskforge task list --assigned-to me --status in-progress

# Tasks with specific tag
taskforge task list --tags "bug" --sort-by priority --reverse

# Project tasks due before specific date
taskforge task list --project "Web App" --due-before 2024-03-01
```

### `taskforge task show`

Show detailed task information.

```bash
taskforge task show TASK_ID [OPTIONS]

Options:
  --include-notes             Show all notes and comments
  --include-history          Show task history and changes
  --include-time-logs        Show time tracking logs
```

### `taskforge task update`

Update an existing task.

```bash
taskforge task update TASK_ID [OPTIONS]

Options:
  --title TEXT                New title
  --description TEXT          New description
  --priority PRIORITY         New priority
  --due DATE                 New due date (or 'none' to remove)
  --status STATUS            New status
  --assigned-to EMAIL        New assignee (or 'none' to unassign)
  --add-tags TAGS            Add tags (comma-separated)
  --remove-tags TAGS         Remove tags (comma-separated)
  --estimated-hours FLOAT    New time estimate
  --custom-field KEY=VALUE   Update custom field
  --remove-custom-field KEY  Remove custom field
```

### `taskforge task start`

Start working on a task (sets status to in-progress and starts time tracking).

```bash
taskforge task start TASK_ID [OPTIONS]

Options:
  --note TEXT                Add a note when starting
  --notify                   Send notifications to team members
```

### `taskforge task stop`

Stop working on a task (stops time tracking).

```bash
taskforge task stop TASK_ID [OPTIONS]

Options:
  --note TEXT                Add a note when stopping
```

### `taskforge task complete`

Mark a task as completed.

```bash
taskforge task complete TASK_ID [OPTIONS]

Options:
  --note TEXT                Add completion note
  --actual-hours FLOAT       Log actual hours spent
  --notify                   Notify assignee and project members
```

### `taskforge task delete`

Delete a task.

```bash
taskforge task delete TASK_ID [OPTIONS]

Options:
  --force                    Skip confirmation prompt
```

### `taskforge task note`

Add a note or comment to a task.

```bash
taskforge task note TASK_ID "Note text" [OPTIONS]

Options:
  --type TYPE                Note type: comment, progress, blocker, solution
  --notify                   Notify task assignee and watchers
  --private                  Make note private (only visible to author and admins)
```

### `taskforge task assign`

Assign a task to a user.

```bash
taskforge task assign TASK_ID EMAIL [OPTIONS]

Options:
  --note TEXT                Add assignment note
  --notify                   Notify the assignee
```

### `taskforge task log-time`

Log time spent on a task.

```bash
taskforge task log-time TASK_ID DURATION [OPTIONS]

Arguments:
  DURATION                   Time duration (e.g., 2h30m, 1.5h, 90m)

Options:
  --description TEXT         Description of work done
  --date DATE               Date of work (default: today)
  --billable                Mark as billable
```

### `taskforge task search`

Search tasks by text content.

```bash
taskforge task search QUERY [OPTIONS]

Options:
  --in-title                Search only in titles
  --in-description          Search only in descriptions
  --in-notes                Search in notes and comments
  --case-sensitive          Case-sensitive search
  --regex                   Use regular expression
  --project PROJECT         Limit search to project
  --date-range RANGE        Date range: last-week, last-month, this-year
```

## Project Commands

### `taskforge project create`

Create a new project.

```bash
taskforge project create "Project name" [OPTIONS]

Options:
  --description TEXT         Project description
  --tags TAGS               Comma-separated tags
  --start-date DATE         Project start date
  --end-date DATE          Project end date
  --template TEMPLATE       Create from template
  --custom-field KEY=VALUE  Custom field (can be used multiple times)
  --public                  Make project publicly visible
  --archived                Create as archived project
```

### `taskforge project list`

List projects.

```bash
taskforge project list [OPTIONS]

Options:
  --status STATUS           Filter by status: active, completed, archived
  --tags TAGS              Filter by tags
  --created-after DATE     Projects created after date
  --created-before DATE    Projects created before date
  --sort-by FIELD          Sort by: created, updated, name, progress
  --include-archived       Include archived projects
```

### `taskforge project show`

Show project details.

```bash
taskforge project show PROJECT_ID [OPTIONS]

Options:
  --include-tasks          Show all project tasks
  --include-members        Show project team members
  --include-stats          Show detailed statistics
```

### `taskforge project update`

Update project information.

```bash
taskforge project update PROJECT_ID [OPTIONS]

Options:
  --name TEXT              New project name
  --description TEXT       New description
  --add-tags TAGS         Add tags
  --remove-tags TAGS      Remove tags
  --start-date DATE       New start date
  --end-date DATE        New end date
  --status STATUS         New status
  --custom-field KEY=VALUE Update custom field
```

### `taskforge project add-member`

Add team member to project.

```bash
taskforge project add-member PROJECT_ID EMAIL [OPTIONS]

Options:
  --role ROLE              Member role: viewer, contributor, admin
  --notify                 Notify the new member
```

### `taskforge project remove-member`

Remove team member from project.

```bash
taskforge project remove-member PROJECT_ID EMAIL [OPTIONS]

Options:
  --notify                 Notify the removed member
```

### `taskforge project progress`

Show project progress report.

```bash
taskforge project progress PROJECT_ID [OPTIONS]

Options:
  --detailed               Show detailed breakdown
  --include-time-tracking  Include time tracking information
  --export PATH           Export report to file
```

### `taskforge project archive`

Archive a project.

```bash
taskforge project archive PROJECT_ID [OPTIONS]

Options:
  --reason TEXT            Reason for archiving
  --notify-members        Notify all project members
```

## User Commands

### `taskforge user create`

Create a new user.

```bash
taskforge user create EMAIL [OPTIONS]

Options:
  --username TEXT          Username (default: derived from email)
  --name TEXT             Full name
  --role ROLE             User role: admin, manager, user, viewer
  --department TEXT       Department/team
  --notify                Send welcome notification
```

### `taskforge user list`

List users.

```bash
taskforge user list [OPTIONS]

Options:
  --role ROLE             Filter by role
  --department TEXT       Filter by department
  --active-only          Show only active users
  --include-stats        Include user statistics
```

### `taskforge user show`

Show user details and statistics.

```bash
taskforge user show EMAIL [OPTIONS]

Options:
  --include-tasks         Show user's tasks
  --include-projects      Show user's projects
  --time-period PERIOD    Time period for stats: week, month, quarter, year
```

### `taskforge user update`

Update user information.

```bash
taskforge user update EMAIL [OPTIONS]

Options:
  --username TEXT         New username
  --name TEXT            New full name
  --role ROLE            New role
  --department TEXT      New department
  --active BOOL          Set active status (true/false)
```

## Report Commands

### `taskforge report daily`

Generate daily activity report.

```bash
taskforge report daily [OPTIONS]

Options:
  --user EMAIL            Report for specific user (default: current user)
  --date DATE            Report date (default: today)
  --project PROJECT      Limit to specific project
  --include-time-logs    Include detailed time logs
  --export PATH          Export to file
```

### `taskforge report weekly`

Generate weekly summary report.

```bash
taskforge report weekly [OPTIONS]

Options:
  --user EMAIL           Report for specific user
  --week-of DATE        Week starting date (default: this week)
  --project PROJECT     Limit to specific project
  --team                Team summary instead of individual
  --export PATH         Export to file
```

### `taskforge report team`

Generate team performance report.

```bash
taskforge report team [OPTIONS]

Options:
  --project PROJECT     Limit to specific project
  --department TEXT     Limit to department
  --time-period PERIOD  Time period: week, month, quarter
  --include-charts      Include visual charts
  --export PATH        Export to file
```

### `taskforge report productivity`

Generate productivity analytics report.

```bash
taskforge report productivity [OPTIONS]

Options:
  --user EMAIL          Report for specific user
  --time-period PERIOD  Time period for analysis
  --compare-to PERIOD   Compare to previous period
  --include-trends      Include trend analysis
  --export PATH        Export to file
```

### `taskforge report billing`

Generate billing report for time tracking.

```bash
taskforge report billing [OPTIONS]

Options:
  --project PROJECT     Limit to specific project
  --client TEXT        Limit to specific client
  --month MONTH        Month for billing (YYYY-MM)
  --user EMAIL         Limit to specific user
  --billable-only      Show only billable hours
  --rate RATE          Hourly rate for calculations
  --export PATH        Export to file (CSV, PDF)
```

### `taskforge report burndown`

Generate burndown chart data for projects.

```bash
taskforge report burndown PROJECT_ID [OPTIONS]

Options:
  --sprint-start DATE   Sprint start date
  --sprint-end DATE     Sprint end date
  --format FORMAT       Output format: json, csv, chart
  --export PATH        Export chart image
```

## Integration Commands

### `taskforge integration add`

Add an integration.

```bash
taskforge integration add TYPE [OPTIONS]

Types: github, slack, trello, jira, google-calendar, outlook

GitHub Options:
  --token TEXT            GitHub personal access token
  --repo TEXT            Repository (owner/repo)
  --sync-issues          Sync with GitHub Issues
  --create-branches      Auto-create branches for tasks

Slack Options:
  --webhook-url TEXT     Slack webhook URL
  --channel TEXT         Default channel
  --bot-token TEXT       Slack bot token

Trello Options:
  --api-key TEXT         Trello API key
  --token TEXT           Trello token
  --board-id TEXT        Board ID to sync

Calendar Options:
  --credentials-file PATH Google/Outlook credentials
  --calendar-id TEXT     Calendar ID
```

### `taskforge integration list`

List configured integrations.

```bash
taskforge integration list [OPTIONS]

Options:
  --active-only          Show only active integrations
  --include-status       Include connection status
```

### `taskforge integration sync`

Sync with external service.

```bash
taskforge integration sync TYPE [OPTIONS]

Options:
  --project PROJECT     Sync specific project only
  --force               Force full re-sync
  --dry-run            Show what would be synced
```

### `taskforge integration remove`

Remove an integration.

```bash
taskforge integration remove TYPE [OPTIONS]

Options:
  --keep-data           Keep synced data after removal
```

## Configuration Commands

### `taskforge config show`

Show current configuration.

```bash
taskforge config show [OPTIONS]

Options:
  --section SECTION     Show specific section only
  --format FORMAT       Output format: json, yaml, table
```

### `taskforge config set`

Set configuration value.

```bash
taskforge config set KEY VALUE

Examples:
  taskforge config set user.name "John Doe"
  taskforge config set notifications.email.enabled true
  taskforge config set storage.type postgresql
  taskforge config set storage.url "postgresql://user:pass@host:5432/db"
```

### `taskforge config unset`

Remove configuration value.

```bash
taskforge config unset KEY

Example:
  taskforge config unset notifications.slack.webhook_url
```

### `taskforge config reset`

Reset configuration to defaults.

```bash
taskforge config reset [OPTIONS]

Options:
  --section SECTION     Reset specific section only
  --backup             Create backup before reset
```

## Import/Export Commands

### `taskforge export`

Export data to various formats.

```bash
taskforge export FORMAT [OPTIONS]

Formats: json, csv, markdown, pdf

Options:
  --output PATH         Output file path
  --project PROJECT     Export specific project
  --date-range RANGE    Date range: last-week, last-month, custom
  --start-date DATE     Custom start date
  --end-date DATE       Custom end date
  --include-completed   Include completed tasks
  --include-archived    Include archived projects
  --template TEMPLATE   Use custom template for markdown/PDF
```

### `taskforge import`

Import data from external sources.

```bash
taskforge import FORMAT [OPTIONS]

Formats: json, csv, trello, asana, todoist, jira

Options:
  --file PATH          Import file path
  --project PROJECT    Import into specific project
  --mapping FILE       Field mapping configuration
  --dry-run           Preview import without saving
  --skip-duplicates   Skip duplicate entries
  --update-existing   Update existing items
```

Examples:
```bash
# Import CSV file
taskforge import csv --file tasks.csv --project "Imported Tasks"

# Import from Trello
taskforge import trello \
  --api-key YOUR_API_KEY \
  --token YOUR_TOKEN \
  --board-url https://trello.com/b/BOARD_ID

# Dry run to preview import
taskforge import csv --file tasks.csv --dry-run
```

## Server Commands

### `taskforge serve`

Start TaskForge API server.

```bash
taskforge serve [OPTIONS]

Options:
  --host TEXT           Host to bind to (default: 127.0.0.1)
  --port INTEGER        Port to bind to (default: 8000)
  --workers INTEGER     Number of worker processes
  --reload              Enable auto-reload for development
  --docs                Enable API documentation at /docs
  --access-log          Enable access logging
  --ssl-cert PATH       SSL certificate file
  --ssl-key PATH        SSL private key file
```

### `taskforge web`

Start web dashboard.

```bash
taskforge web [OPTIONS]

Options:
  --host TEXT           Host to bind to (default: 127.0.0.1)
  --port INTEGER        Port to bind to (default: 8501)
  --theme TEXT          UI theme: light, dark, auto
  --debug               Enable debug mode
```

## Plugin Commands

### `taskforge plugin list`

List installed plugins.

```bash
taskforge plugin list [OPTIONS]

Options:
  --enabled-only        Show only enabled plugins
  --include-details     Include plugin details and metadata
```

### `taskforge plugin install`

Install a plugin.

```bash
taskforge plugin install PLUGIN [OPTIONS]

Options:
  --from-file PATH      Install from local file
  --from-url URL        Install from URL
  --version VERSION     Install specific version
  --enable              Enable after installation
```

### `taskforge plugin enable`

Enable a plugin.

```bash
taskforge plugin enable PLUGIN_NAME
```

### `taskforge plugin disable`

Disable a plugin.

```bash
taskforge plugin disable PLUGIN_NAME
```

### `taskforge plugin configure`

Configure a plugin.

```bash
taskforge plugin configure PLUGIN_NAME [OPTIONS]

Options:
  --interactive         Interactive configuration
  --config-file PATH    Use configuration file
  --set KEY=VALUE       Set specific configuration value
```

## Advanced Usage Examples

### Bulk Operations

```bash
# Complete multiple tasks
taskforge task list --tags "quick-fix" --format json | \
  jq -r '.[].id' | \
  xargs -I {} taskforge task complete {}

# Update priority for all overdue tasks
taskforge task list --overdue --format json | \
  jq -r '.[].id' | \
  xargs -I {} taskforge task update {} --priority high
```

### Custom Queries

```bash
# Tasks assigned to team members, grouped by project
taskforge task list --assigned-to alice@company.com --format json | \
  jq 'group_by(.project_id) | map({project: .[0].project_name, tasks: map(.title)})'

# Weekly productivity summary
for user in alice@company.com bob@company.com; do
  echo "=== $user ==="
  taskforge report weekly --user $user --format table
done
```

### Automation Scripts

```bash
#!/bin/bash
# Daily standup report generator

echo "# Daily Standup Report - $(date +%Y-%m-%d)"
echo ""

for member in alice@company.com bob@company.com charlie@company.com; do
  echo "## $member"
  
  echo "### Completed Yesterday:"
  taskforge task list --assigned-to $member --status completed \
    --created-after $(date -d "1 day ago" +%Y-%m-%d) \
    --format table --quiet
  
  echo "### Working on Today:"
  taskforge task list --assigned-to $member --status in-progress \
    --format table --quiet
  
  echo "### Blockers:"
  taskforge task list --assigned-to $member --tags blocker \
    --status todo,in-progress --format table --quiet
  
  echo ""
done
```

### Pipeline Integration

```bash
# GitLab CI/CD integration
taskforge task add "Deploy version $CI_COMMIT_TAG" \
  --project "$CI_PROJECT_NAME" \
  --priority high \
  --custom-field "pipeline_id=$CI_PIPELINE_ID" \
  --custom-field "commit_sha=$CI_COMMIT_SHA"
```

## Exit Codes

TaskForge uses standard exit codes:
- `0` - Success
- `1` - General error
- `2` - Misuse of command (invalid arguments)
- `3` - Resource not found (task, project, user)
- `4` - Permission denied
- `5` - Configuration error
- `6` - Network/connection error

## Environment Variables

- `TASKFORGE_CONFIG` - Path to configuration file
- `TASKFORGE_DATA_DIR` - Data directory path
- `TASKFORGE_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `TASKFORGE_NO_COLOR` - Disable colored output
- `DATABASE_URL` - Database connection string
- `TASKFORGE_API_URL` - API server URL for CLI commands

## Configuration File Reference

```json
{
  "storage": {
    "type": "json|postgresql|mysql",
    "path": "./data",
    "url": "postgresql://user:pass@host:5432/db"
  },
  "user": {
    "name": "Your Name",
    "email": "you@example.com",
    "timezone": "UTC"
  },
  "server": {
    "host": "127.0.0.1",
    "port": 8000,
    "workers": 1
  },
  "notifications": {
    "email": {
      "enabled": false,
      "smtp_host": "smtp.gmail.com",
      "smtp_port": 587
    },
    "slack": {
      "enabled": false,
      "webhook_url": "",
      "channel": "#general"
    }
  },
  "integrations": {
    "github": {
      "token": "",
      "repos": []
    },
    "trello": {
      "api_key": "",
      "token": ""
    }
  },
  "preferences": {
    "date_format": "YYYY-MM-DD",
    "time_format": "24h",
    "theme": "auto",
    "default_priority": "medium"
  }
}
```

For more detailed information, visit the [TaskForge Documentation](https://docs.taskforge.dev).