# User Guide

*TODO: This guide is under construction. It will provide comprehensive documentation for end users.*

## Getting Started with TaskForge

TaskForge is a comprehensive task management platform designed for developers and teams.

### Installation

```bash
# Install using pip
pip install taskforge

# Or install from source
git clone https://github.com/taskforge-community/taskforge.git
cd taskforge
pip install -e .
```

### Basic Usage

#### Creating Your First Task

```bash
# Create a simple task
taskforge task add "Complete project documentation"

# Create a task with priority and due date
taskforge task add "Fix critical bug" --priority critical --due 2024-12-31

# Create a task in a specific project
taskforge task add "Design new feature" --project "Web App" --priority high
```

#### Managing Projects

```bash
# Create a new project
taskforge project create "My Web App" --description "Personal portfolio website"

# List all projects
taskforge project list

# View project details
taskforge project show <project-id>
```

#### Viewing Tasks

```bash
# List all tasks
taskforge task list

# List tasks with filters
taskforge task list --status todo --priority high

# Show overdue tasks
taskforge task list --overdue

# View task details
taskforge task show <task-id>
```

## Advanced Features

### Task Dependencies

```bash
# Create tasks with dependencies
taskforge task add "Implement feature" --project "Web App"
taskforge task add "Write tests" --depends "Implement feature"
```

### Team Collaboration

```bash
# Assign tasks to team members
taskforge task update <task-id> --assigned "team-member@example.com"

# Share projects with your team
taskforge project share <project-id> --member "team-member@example.com"
```

### Integrations

TaskForge integrates with popular tools:
- **Git**: Link tasks to commits and branches
- **Slack**: Get notifications about task updates
- **GitHub**: Sync issues with tasks
- **Calendar**: Sync due dates with your calendar

## Configuration

### Global Configuration

```bash
# Configure your default settings
taskforge config set user.name "Your Name"
taskforge config set user.email "your.email@example.com"
```

### Project Configuration

Each project can have its own configuration file for custom settings.

## Troubleshooting

### Common Issues

1. **Tasks not showing**: Check your filters and project selection
2. **Sync issues**: Verify your internet connection and authentication
3. **Performance**: Use local storage for better performance

### Getting Help

- Check our [FAQ](../faq.md)
- Join our [Discord community](https://discord.gg/taskforge)
- Create an issue on [GitHub](https://github.com/taskforge-community/taskforge/issues)

---

*This user guide is actively being developed. Check back soon for more detailed documentation!*