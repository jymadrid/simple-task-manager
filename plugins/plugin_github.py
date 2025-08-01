"""
Example plugin: GitHub integration for TaskForge
"""

import asyncio
from typing import Dict, Any, List, Optional
from github import Github
from github.GithubException import GithubException

from taskforge.plugins import IntegrationPlugin, PluginMetadata, PluginHook
from taskforge.core.task import Task, TaskStatus, TaskPriority, TaskType
from taskforge.core.user import User


class GitHubIntegrationPlugin(IntegrationPlugin):
    """Plugin for GitHub Issues integration"""
    
    def __init__(self):
        super().__init__()
        self.github_client = None
        self.settings = {
            'access_token': '',
            'default_repo': '',
            'sync_labels': True,
            'auto_close_issues': True,
            'create_branches': False,
            'label_mapping': {
                'critical': 'priority: critical',
                'high': 'priority: high',
                'medium': 'priority: medium',
                'low': 'priority: low',
                'bug': 'type: bug',
                'feature': 'type: feature',
                'documentation': 'type: docs'
            }
        }
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="GitHub Integration",
            version="1.0.0",
            description="Sync tasks with GitHub Issues and create branches",
            author="TaskForge Community",
            email="plugins@taskforge.dev",
            website="https://github.com/taskforge-community/plugin-github",
            dependencies=["PyGithub>=1.58.0"],
            min_taskforge_version="1.0.0"
        )
    
    def on_activate(self):
        """Initialize GitHub client when plugin is activated"""
        if self.settings['access_token']:
            self.github_client = Github(self.settings['access_token'])
    
    def configure(self, settings: Dict[str, Any]):
        """Configure plugin settings"""
        self.settings.update(settings)
        if self.enabled and self.settings['access_token']:
            self.github_client = Github(self.settings['access_token'])
    
    @PluginHook('task_created', priority=100)
    def on_task_created(self, task: Task, user: User, **kwargs):
        """Create GitHub issue when task is created"""
        if not self.github_client or not self.settings['default_repo']:
            return
        
        try:
            repo = self.github_client.get_repo(self.settings['default_repo'])
            
            # Create issue
            issue = repo.create_issue(
                title=task.title,
                body=self._format_issue_body(task),
                labels=self._get_labels_for_task(task)
            )
            
            # Store GitHub issue reference
            task.external_links['github'] = issue.html_url
            task.integration_data['github_issue_id'] = issue.number
            
            # Create branch if enabled
            if self.settings['create_branches']:
                self._create_branch_for_task(repo, task, issue)
            
            return {'github_issue_id': issue.number, 'github_url': issue.html_url}
            
        except GithubException as e:
            print(f"GitHub API Error: {e}")
            return {'error': str(e)}
    
    @PluginHook('task_updated', priority=100)
    def on_task_updated(self, task: Task, old_task: Task, user: User, **kwargs):
        """Update GitHub issue when task is updated"""
        if not self.github_client or 'github_issue_id' not in task.integration_data:
            return
        
        try:
            repo = self.github_client.get_repo(self.settings['default_repo'])
            issue = repo.get_issue(task.integration_data['github_issue_id'])
            
            # Update issue title and body
            issue.edit(
                title=task.title,
                body=self._format_issue_body(task),
                labels=self._get_labels_for_task(task)
            )
            
            # Close issue if task is done
            if (task.status == TaskStatus.DONE and 
                old_task.status != TaskStatus.DONE and 
                self.settings['auto_close_issues']):
                issue.edit(state='closed')
                issue.create_comment("Task completed in TaskForge ✅")
            
            # Reopen issue if task is no longer done
            elif (task.status != TaskStatus.DONE and 
                  old_task.status == TaskStatus.DONE):
                issue.edit(state='open')
                issue.create_comment("Task reopened in TaskForge 🔄")
            
        except GithubException as e:
            print(f"GitHub API Error: {e}")
    
    @PluginHook('task_status_changed', priority=100)
    def on_task_status_changed(self, task: Task, old_status: str, new_status: str, user: User, **kwargs):
        """Add comment to GitHub issue when status changes"""
        if not self.github_client or 'github_issue_id' not in task.integration_data:
            return
        
        try:
            repo = self.github_client.get_repo(self.settings['default_repo'])
            issue = repo.get_issue(task.integration_data['github_issue_id'])
            
            status_emoji = {
                'todo': '📋',
                'in_progress': '🔄',
                'blocked': '🚫',
                'review': '👀',
                'done': '✅',
                'cancelled': '❌'
            }
            
            emoji = status_emoji.get(new_status, '🔄')
            comment = f"{emoji} Status changed from `{old_status}` to `{new_status}` by {user.username}"
            
            if task.progress > 0:
                comment += f" (Progress: {task.progress}%)"
            
            issue.create_comment(comment)
            
        except GithubException as e:
            print(f"GitHub API Error: {e}")
    
    def sync_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """Sync tasks with GitHub issues"""
        if not self.github_client or not self.settings['default_repo']:
            return {'error': 'GitHub client not configured'}
        
        try:
            repo = self.github_client.get_repo(self.settings['default_repo'])
            synced_count = 0
            errors = []
            
            for task in tasks:
                try:
                    if 'github_issue_id' in task.integration_data:
                        # Update existing issue
                        issue = repo.get_issue(task.integration_data['github_issue_id'])
                        issue.edit(
                            title=task.title,
                            body=self._format_issue_body(task),
                            labels=self._get_labels_for_task(task),
                            state='closed' if task.status == TaskStatus.DONE else 'open'
                        )
                    else:
                        # Create new issue
                        issue = repo.create_issue(
                            title=task.title,
                            body=self._format_issue_body(task),
                            labels=self._get_labels_for_task(task)
                        )
                        task.integration_data['github_issue_id'] = issue.number
                        task.external_links['github'] = issue.html_url
                    
                    synced_count += 1
                    
                except GithubException as e:
                    errors.append(f"Task {task.id[:8]}: {e}")
            
            return {
                'synced_count': synced_count,
                'errors': errors
            }
            
        except GithubException as e:
            return {'error': str(e)}
    
    def import_tasks(self) -> List[Task]:
        """Import GitHub issues as tasks"""
        if not self.github_client or not self.settings['default_repo']:
            return []
        
        try:
            repo = self.github_client.get_repo(self.settings['default_repo'])
            issues = repo.get_issues(state='open')
            
            imported_tasks = []
            
            for issue in issues:
                # Skip pull requests
                if issue.pull_request:
                    continue
                
                task = Task(
                    title=issue.title,
                    description=issue.body or "",
                    priority=self._extract_priority_from_labels(issue.labels),
                    task_type=self._extract_type_from_labels(issue.labels),
                    status=TaskStatus.TODO
                )
                
                # Set integration data
                task.integration_data['github_issue_id'] = issue.number
                task.external_links['github'] = issue.html_url
                
                # Extract assignee
                if issue.assignee:
                    task.assigned_to = issue.assignee.login
                
                # Extract due date from milestone
                if issue.milestone and issue.milestone.due_on:
                    task.due_date = issue.milestone.due_on
                
                imported_tasks.append(task)
            
            return imported_tasks
            
        except GithubException as e:
            print(f"GitHub API Error: {e}")
            return []
    
    def _format_issue_body(self, task: Task) -> str:
        """Format task as GitHub issue body"""
        body = task.description or ""
        
        if task.due_date:
            body += f"\n\n**Due Date:** {task.due_date.strftime('%Y-%m-%d %H:%M')}"
        
        if task.progress > 0:
            body += f"\n**Progress:** {task.progress}%"
        
        if task.tags:
            body += f"\n**Tags:** {', '.join(task.tags)}"
        
        body += f"\n\n---\n*Managed by TaskForge*"
        
        return body
    
    def _get_labels_for_task(self, task: Task) -> List[str]:
        """Get GitHub labels for a task"""
        labels = []
        
        # Priority label
        priority_label = self.settings['label_mapping'].get(task.priority.value)
        if priority_label:
            labels.append(priority_label)
        
        # Type label
        type_label = self.settings['label_mapping'].get(task.task_type.value)
        if type_label:
            labels.append(type_label)
        
        # Status label
        labels.append(f"status: {task.status.value}")
        
        # Custom tags
        if self.settings['sync_labels']:
            labels.extend(task.tags)
        
        return labels
    
    def _extract_priority_from_labels(self, labels) -> TaskPriority:
        """Extract priority from GitHub labels"""
        priority_map = {
            'priority: critical': TaskPriority.CRITICAL,
            'priority: high': TaskPriority.HIGH,
            'priority: medium': TaskPriority.MEDIUM,
            'priority: low': TaskPriority.LOW
        }
        
        for label in labels:
            if label.name in priority_map:
                return priority_map[label.name]
        
        return TaskPriority.MEDIUM
    
    def _extract_type_from_labels(self, labels) -> TaskType:
        """Extract type from GitHub labels"""
        type_map = {
            'type: bug': TaskType.BUG,
            'type: feature': TaskType.FEATURE,
            'type: docs': TaskType.DOCUMENTATION
        }
        
        for label in labels:
            if label.name in type_map:
                return type_map[label.name]
        
        return TaskType.OTHER
    
    def _create_branch_for_task(self, repo, task: Task, issue):
        """Create a branch for the task"""
        try:
            # Get default branch
            default_branch = repo.get_branch(repo.default_branch)
            
            # Create branch name
            branch_name = f"task/{issue.number}-{task.title.lower().replace(' ', '-')[:30]}"
            
            # Create branch
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=default_branch.commit.sha
            )
            
            # Add comment with branch info
            issue.create_comment(f"🌿 Created branch: `{branch_name}`")
            
            # Store branch reference
            task.integration_data['github_branch'] = branch_name
            
        except GithubException as e:
            print(f"Failed to create branch: {e}")


# Plugin entry point
def get_plugin_class():
    """Entry point for plugin loading"""
    return GitHubIntegrationPlugin