# API Reference

*TODO: This documentation is under construction. It will provide comprehensive API documentation for TaskForge.*

## Overview

TaskForge provides a comprehensive REST API for all task management operations. The API is built with FastAPI and follows RESTful principles.

## Base URL

```
Production: https://api.taskforge.dev/v1
Development: http://localhost:8000/v1
```

## Authentication

### JWT Token Authentication

All API endpoints (except authentication endpoints) require a valid JWT token.

```http
Authorization: Bearer <your-jwt-token>
```

### Getting a Token

```bash
curl -X POST "http://localhost:8000/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your-password"
  }'
```

## Endpoints

### Authentication

#### Login
```http
POST /v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Refresh Token
```http
POST /v1/auth/refresh
Authorization: Bearer <refresh-token>
```

#### Logout
```http
POST /v1/auth/logout
Authorization: Bearer <access-token>
```

### Tasks

#### List Tasks
```http
GET /v1/tasks?status=todo&priority=high&limit=20&offset=0
Authorization: Bearer <token>
```

**Response:**
```json
{
  "items": [
    {
      "id": "task-123",
      "title": "Complete documentation",
      "description": "Write comprehensive API docs",
      "status": "todo",
      "priority": "high",
      "project_id": "proj-456",
      "assigned_to": "user-789",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z",
      "due_date": "2024-01-20T23:59:59Z",
      "tags": ["documentation", "api"],
      "progress": 0
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Create Task
```http
POST /v1/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "New task title",
  "description": "Task description",
  "priority": "medium",
  "project_id": "proj-456",
  "assigned_to": "user-789",
  "due_date": "2024-01-20T23:59:59Z",
  "tags": ["tag1", "tag2"]
}
```

#### Get Task
```http
GET /v1/tasks/{task_id}
Authorization: Bearer <token>
```

#### Update Task
```http
PUT /v1/tasks/{task_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Updated task title",
  "status": "in_progress",
  "progress": 50
}
```

#### Delete Task
```http
DELETE /v1/tasks/{task_id}
Authorization: Bearer <token>
```

### Projects

#### List Projects
```http
GET /v1/projects
Authorization: Bearer <token>
```

#### Create Project
```http
POST /v1/projects
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "New Project",
  "description": "Project description",
  "team_members": ["user-789", "user-456"]
}
```

#### Get Project
```http
GET /v1/projects/{project_id}
Authorization: Bearer <token>
```

#### Update Project
```http
PUT /v1/projects/{project_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated project name",
  "description": "Updated description"
}
```

#### Delete Project
```http
DELETE /v1/projects/{project_id}
Authorization: Bearer <token>
```

### Users

#### Get Current User
```http
GET /v1/users/me
Authorization: Bearer <token>
```

#### Update User Profile
```http
PUT /v1/users/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Name",
  "email": "updated@example.com"
}
```

### Statistics

#### Get Task Statistics
```http
GET /v1/stats/tasks?project_id={project_id}&user_id={user_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_tasks": 100,
  "completed_tasks": 60,
  "in_progress_tasks": 25,
  "todo_tasks": 15,
  "overdue_tasks": 5,
  "completion_rate": 0.6,
  "average_completion_time": "2.5 days"
}
```

#### Get Productivity Metrics
```http
GET /v1/stats/productivity?period=30d
Authorization: Bearer <token>
```

## Data Models

### Task

```json
{
  "id": "string (uuid)",
  "title": "string (required, max 200 chars)",
  "description": "string (optional, max 2000 chars)",
  "status": "todo|in_progress|review|done|cancelled|blocked",
  "priority": "low|medium|high|critical",
  "project_id": "string (uuid, optional)",
  "assigned_to": "string (uuid, optional)",
  "created_by": "string (uuid)",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)",
  "due_date": "datetime (ISO 8601, optional)",
  "completed_at": "datetime (ISO 8601, optional)",
  "tags": ["string"],
  "progress": "integer (0-100)",
  "dependencies": ["string (uuid)"],
  "custom_fields": "object (optional)"
}
```

### Project

```json
{
  "id": "string (uuid)",
  "name": "string (required, max 100 chars)",
  "description": "string (optional, max 1000 chars)",
  "owner_id": "string (uuid)",
  "team_members": ["string (uuid)"],
  "status": "active|completed|archived",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)",
  "start_date": "datetime (ISO 8601, optional)",
  "end_date": "datetime (ISO 8601, optional)",
  "budget": "number (optional)",
  "settings": "object (optional)"
}
```

### User

```json
{
  "id": "string (uuid)",
  "email": "string (required, unique)",
  "name": "string (required)",
  "role": "admin|manager|member|viewer",
  "avatar_url": "string (optional)",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)",
  "last_login": "datetime (ISO 8601, optional)",
  "settings": "object (optional)",
  "is_active": "boolean"
}
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with ID 'task-123' not found",
    "details": {
      "task_id": "task-123",
      "user_id": "user-789"
    }
  }
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `UNAUTHORIZED` | Invalid or missing authentication | 401 |
| `FORBIDDEN` | Insufficient permissions | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `VALIDATION_ERROR` | Invalid input data | 422 |
| `TASK_NOT_FOUND` | Task not found | 404 |
| `PROJECT_NOT_FOUND` | Project not found | 404 |
| `USER_NOT_FOUND` | User not found | 404 |
| `DUPLICATE_TASK` | Task already exists | 409 |
| `DEPENDENCY_CYCLE` | Task dependency would create a cycle | 400 |

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Standard tier**: 1000 requests per hour
- **Premium tier**: 10,000 requests per hour
- **Enterprise tier**: Unlimited requests

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642694400
```

## Pagination

List endpoints support pagination using `limit` and `offset` parameters:

- `limit`: Number of items to return (default: 20, max: 100)
- `offset`: Number of items to skip (default: 0)

## Filtering and Sorting

### Filtering
Many endpoints support filtering via query parameters:

```http
GET /v1/tasks?status=todo&priority=high&assigned_to=user-123
```

### Sorting
Sort results using the `sort` parameter:

```http
GET /v1/tasks?sort=created_at:desc,priority:asc
```

## Webhooks

TaskForge can send webhook notifications for events:

### Register Webhook

```http
POST /v1/webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["task.created", "task.completed", "project.updated"],
  "secret": "your-webhook-secret"
}
```

### Webhook Payload

```json
{
  "event": "task.created",
  "data": {
    "task": { /* Task object */ },
    "user": { /* User object */ }
  },
  "timestamp": "2024-01-15T10:00:00Z"
}
```

## SDKs and Libraries

### Python SDK

```python
from taskforge import TaskForgeClient

client = TaskForgeClient(api_key="your-api-key")

# Create a task
task = client.tasks.create(
    title="New task",
    description="Task description",
    priority="high"
)

# List tasks
tasks = client.tasks.list(status="todo")
```

### JavaScript SDK

```javascript
import { TaskForgeClient } from '@taskforge/sdk';

const client = new TaskForgeClient({ apiKey: 'your-api-key' });

// Create a task
const task = await client.tasks.create({
  title: 'New task',
  description: 'Task description',
  priority: 'high'
});

// List tasks
const tasks = await client.tasks.list({ status: 'todo' });
```

## Support

- **Documentation**: [docs.taskforge.dev](https://docs.taskforge.dev)
- **API Issues**: [GitHub Issues](https://github.com/taskforge-community/taskforge/issues)
- **Community**: [Discord Server](https://discord.gg/taskforge)
- **Email**: api-support@taskforge.dev

---

*This API reference is actively being developed. Check back for the latest updates!*