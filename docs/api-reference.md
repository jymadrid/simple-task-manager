# TaskForge API Documentation

Complete REST API reference for TaskForge task management system. The API provides programmatic access to all TaskForge functionality, enabling custom integrations and third-party applications.

## Base Information

- **Base URL**: `https://api.taskforge.dev/v1` (or your self-hosted instance)
- **Protocol**: HTTPS only
- **Authentication**: JWT tokens
- **Content Type**: `application/json`
- **Rate Limiting**: 1000 requests/hour per API key (configurable)

## Authentication

### JWT Authentication

TaskForge uses JWT (JSON Web Tokens) for API authentication. Include the token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Obtaining Access Tokens

#### Login with Credentials

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "username": "username"
  }
}
```

#### Refresh Token

```http
POST /auth/refresh
Content-Type: application/json
Authorization: Bearer <refresh-token>
```

#### API Key Authentication (Alternative)

For server-to-server integrations, you can use API keys:

```http
X-API-Key: <your-api-key>
```

## Error Handling

### HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required or invalid
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation errors
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid parameters",
    "details": {
      "title": ["This field is required"],
      "due_date": ["Invalid date format"]
    },
    "request_id": "req_123456789"
  }
}
```

## Pagination

List endpoints support cursor-based pagination:

### Request Parameters

- `limit` - Number of items per page (default: 50, max: 100)
- `cursor` - Pagination cursor from previous response

### Response Format

```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTIzNDU2fQ==",
    "prev_cursor": null,
    "has_more": true,
    "limit": 50,
    "total_count": 1247
  }
}
```

## Tasks API

### Create Task

Create a new task with comprehensive metadata and relationships.

```http
POST /tasks
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "Implement user authentication",
  "description": "Add JWT-based authentication with role-based access control",
  "priority": "high",
  "status": "todo",
  "project_id": "proj-uuid",
  "assigned_to": "user-uuid",
  "due_date": "2024-03-15T17:00:00Z",
  "estimated_hours": 8.5,
  "tags": ["authentication", "security", "backend"],
  "custom_fields": {
    "client": "Acme Corp",
    "billable": true,
    "story_points": 5
  },
  "attachments": [
    {
      "name": "requirements.pdf",
      "url": "https://files.taskforge.dev/attachments/abc123"
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": "task-uuid",
  "title": "Implement user authentication",
  "description": "Add JWT-based authentication with role-based access control",
  "priority": "high",
  "status": "todo",
  "project": {
    "id": "proj-uuid",
    "name": "Web Application"
  },
  "assigned_to": {
    "id": "user-uuid",
    "username": "johndoe",
    "email": "john@example.com"
  },
  "created_by": {
    "id": "creator-uuid",
    "username": "janedoe",
    "email": "jane@example.com"
  },
  "due_date": "2024-03-15T17:00:00Z",
  "estimated_hours": 8.5,
  "actual_hours": 0,
  "completion_percentage": 0,
  "tags": ["authentication", "security", "backend"],
  "custom_fields": {
    "client": "Acme Corp",
    "billable": true,
    "story_points": 5
  },
  "attachments": [
    {
      "id": "attachment-uuid",
      "name": "requirements.pdf",
      "url": "https://files.taskforge.dev/attachments/abc123",
      "size": 102400,
      "mime_type": "application/pdf"
    }
  ],
  "created_at": "2024-02-01T10:30:00Z",
  "updated_at": "2024-02-01T10:30:00Z",
  "url": "https://api.taskforge.dev/v1/tasks/task-uuid"
}
```

### List Tasks

Retrieve tasks with comprehensive filtering and sorting options.

```http
GET /tasks?status=todo,in_progress&priority=high&project_id=proj-uuid&assigned_to=user-uuid&tags=backend&limit=50&cursor=eyJpZCI6MTIzfQ==
Authorization: Bearer <token>
```

**Query Parameters:**

- `status` - Filter by status (comma-separated): `todo`, `in_progress`, `completed`, `cancelled`
- `priority` - Filter by priority (comma-separated): `low`, `medium`, `high`
- `project_id` - Filter by project UUID
- `assigned_to` - Filter by assigned user UUID
- `created_by` - Filter by creator UUID
- `tags` - Filter by tags (comma-separated)
- `due_before` - Tasks due before date (ISO 8601)
- `due_after` - Tasks due after date (ISO 8601)
- `created_after` - Tasks created after date (ISO 8601)
- `created_before` - Tasks created before date (ISO 8601)
- `search` - Full-text search in title and description
- `sort_by` - Sort field: `created_at`, `updated_at`, `due_date`, `priority`, `title`
- `sort_order` - Sort order: `asc`, `desc` (default: `desc`)
- `include_completed` - Include completed tasks (default: `false`)

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "task-uuid-1",
      "title": "Implement user authentication",
      "description": "Add JWT-based authentication...",
      "priority": "high",
      "status": "in_progress",
      "project": {
        "id": "proj-uuid",
        "name": "Web Application"
      },
      "assigned_to": {
        "id": "user-uuid",
        "username": "johndoe"
      },
      "progress": {
        "completion_percentage": 65,
        "time_spent_hours": 5.25,
        "last_activity": "2024-02-15T14:30:00Z"
      },
      "due_date": "2024-03-15T17:00:00Z",
      "tags": ["authentication", "security", "backend"],
      "created_at": "2024-02-01T10:30:00Z",
      "updated_at": "2024-02-15T14:30:00Z"
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6MTIzNDU2fQ==",
    "has_more": true,
    "limit": 50,
    "total_count": 127
  }
}
```

### Get Single Task

Retrieve detailed information about a specific task.

```http
GET /tasks/{task_id}?include=notes,time_logs,dependencies,watchers
Authorization: Bearer <token>
```

**Query Parameters:**

- `include` - Additional data to include (comma-separated):
  - `notes` - Task comments and notes
  - `time_logs` - Time tracking entries
  - `dependencies` - Task dependencies
  - `watchers` - Users watching the task
  - `attachments` - File attachments
  - `history` - Task change history

**Response (200 OK):**
```json
{
  "id": "task-uuid",
  "title": "Implement user authentication",
  "description": "Add JWT-based authentication with role-based access control",
  "priority": "high",
  "status": "in_progress",
  "project": {
    "id": "proj-uuid",
    "name": "Web Application",
    "url": "https://api.taskforge.dev/v1/projects/proj-uuid"
  },
  "assigned_to": {
    "id": "user-uuid",
    "username": "johndoe",
    "email": "john@example.com",
    "avatar_url": "https://avatars.taskforge.dev/johndoe.jpg"
  },
  "created_by": {
    "id": "creator-uuid",
    "username": "janedoe",
    "email": "jane@example.com"
  },
  "due_date": "2024-03-15T17:00:00Z",
  "estimated_hours": 8.5,
  "actual_hours": 5.25,
  "completion_percentage": 65,
  "tags": ["authentication", "security", "backend"],
  "custom_fields": {
    "client": "Acme Corp",
    "billable": true,
    "story_points": 5
  },
  "notes": [
    {
      "id": "note-uuid-1",
      "content": "Started implementing JWT middleware",
      "author": {
        "id": "user-uuid",
        "username": "johndoe"
      },
      "created_at": "2024-02-10T09:15:00Z",
      "type": "progress_update"
    },
    {
      "id": "note-uuid-2",
      "content": "Need clarification on role hierarchy",
      "author": {
        "id": "user-uuid",
        "username": "johndoe"
      },
      "created_at": "2024-02-12T16:45:00Z",
      "type": "question"
    }
  ],
  "time_logs": [
    {
      "id": "time-log-uuid-1",
      "duration_minutes": 120,
      "description": "Set up JWT infrastructure",
      "logged_by": {
        "id": "user-uuid",
        "username": "johndoe"
      },
      "logged_at": "2024-02-10T11:30:00Z",
      "date": "2024-02-10"
    }
  ],
  "dependencies": {
    "blocking": [
      {
        "id": "task-uuid-dependency",
        "title": "Database schema design",
        "status": "completed"
      }
    ],
    "blocked_by": [
      {
        "id": "task-uuid-blocked",
        "title": "Security audit requirements",
        "status": "todo"
      }
    ]
  },
  "watchers": [
    {
      "id": "watcher-uuid",
      "username": "projectmanager",
      "email": "pm@example.com"
    }
  ],
  "created_at": "2024-02-01T10:30:00Z",
  "updated_at": "2024-02-15T14:30:00Z",
  "url": "https://api.taskforge.dev/v1/tasks/task-uuid"
}
```

### Update Task

Update task properties with partial data.

```http
PATCH /tasks/{task_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "status": "in_progress",
  "completion_percentage": 75,
  "actual_hours": 6.5,
  "notes": "Made significant progress on role-based permissions"
}
```

**Response (200 OK):**
```json
{
  "id": "task-uuid",
  "title": "Implement user authentication",
  "status": "in_progress",
  "completion_percentage": 75,
  "actual_hours": 6.5,
  "updated_at": "2024-02-16T10:15:00Z",
  "url": "https://api.taskforge.dev/v1/tasks/task-uuid"
}
```

### Delete Task

```http
DELETE /tasks/{task_id}
Authorization: Bearer <token>
```

**Response (204 No Content)**

### Task Actions

#### Start Task

Begin working on a task (sets status to in_progress and starts time tracking).

```http
POST /tasks/{task_id}/start
Content-Type: application/json
Authorization: Bearer <token>

{
  "note": "Starting work on authentication implementation"
}
```

#### Complete Task

Mark a task as completed.

```http
POST /tasks/{task_id}/complete
Content-Type: application/json
Authorization: Bearer <token>

{
  "completion_note": "Authentication system implemented and tested",
  "actual_hours": 8.75
}
```

#### Add Note

Add a comment or note to a task.

```http
POST /tasks/{task_id}/notes
Content-Type: application/json
Authorization: Bearer <token>

{
  "content": "Encountered issue with CORS configuration, will need to update settings",
  "type": "blocker",
  "notify_watchers": true
}
```

### Bulk Operations

#### Bulk Update Tasks

```http
PATCH /tasks/bulk
Content-Type: application/json
Authorization: Bearer <token>

{
  "task_ids": ["task-uuid-1", "task-uuid-2", "task-uuid-3"],
  "updates": {
    "priority": "high",
    "assigned_to": "user-uuid"
  }
}
```

#### Bulk Delete Tasks

```http
DELETE /tasks/bulk
Content-Type: application/json
Authorization: Bearer <token>

{
  "task_ids": ["task-uuid-1", "task-uuid-2", "task-uuid-3"]
}
```

## Projects API

### Create Project

```http
POST /projects
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "TaskForge Mobile App",
  "description": "Native mobile applications for iOS and Android",
  "tags": ["mobile", "react-native", "cross-platform"],
  "start_date": "2024-03-01",
  "end_date": "2024-08-31",
  "budget": 150000,
  "custom_fields": {
    "client": "Internal Project",
    "department": "Engineering",
    "priority_level": "P0"
  },
  "team_members": [
    {
      "user_id": "user-uuid-1",
      "role": "project_manager"
    },
    {
      "user_id": "user-uuid-2",
      "role": "developer"
    }
  ]
}
```

### List Projects

```http
GET /projects?status=active&tags=mobile&owner=user-uuid&limit=20
Authorization: Bearer <token>
```

### Get Project Details

```http
GET /projects/{project_id}?include=tasks,members,statistics
Authorization: Bearer <token>
```

**Response includes:**
```json
{
  "id": "proj-uuid",
  "name": "TaskForge Mobile App",
  "description": "Native mobile applications...",
  "status": "active",
  "progress": {
    "completion_percentage": 45,
    "tasks_completed": 23,
    "tasks_total": 51,
    "on_track": true
  },
  "budget": {
    "allocated": 150000,
    "spent": 67500,
    "remaining": 82500
  },
  "timeline": {
    "start_date": "2024-03-01",
    "end_date": "2024-08-31",
    "estimated_completion": "2024-08-15"
  },
  "team_members": [
    {
      "user": {
        "id": "user-uuid-1",
        "username": "alice",
        "email": "alice@company.com"
      },
      "role": "project_manager",
      "joined_at": "2024-02-15T09:00:00Z"
    }
  ],
  "statistics": {
    "total_time_spent": 456.75,
    "average_task_completion_time": 18.5,
    "productivity_trend": "increasing"
  }
}
```

## Users API

### Get Current User

```http
GET /users/me
Authorization: Bearer <token>
```

### List Users

```http
GET /users?role=developer&department=engineering&active=true
Authorization: Bearer <token>
```

### Get User Details

```http
GET /users/{user_id}?include=projects,statistics
Authorization: Bearer <token>
```

## Time Tracking API

### Log Time Entry

```http
POST /time-logs
Content-Type: application/json
Authorization: Bearer <token>

{
  "task_id": "task-uuid",
  "duration_minutes": 120,
  "description": "Implemented OAuth2 flow",
  "date": "2024-02-16",
  "billable": true,
  "tags": ["development", "oauth"]
}
```

### Get Time Logs

```http
GET /time-logs?user_id=user-uuid&date_from=2024-02-01&date_to=2024-02-28&billable=true
Authorization: Bearer <token>
```

### Time Tracking Reports

```http
GET /reports/time-tracking?user_id=user-uuid&period=month&year=2024&month=2
Authorization: Bearer <token>
```

## Search API

### Advanced Search

```http
GET /search?q=authentication&type=tasks,projects&filters[priority]=high&filters[status]=todo,in_progress
Authorization: Bearer <token>
```

**Response:**
```json
{
  "query": "authentication",
  "results": {
    "tasks": {
      "total": 15,
      "items": [...]
    },
    "projects": {
      "total": 3,
      "items": [...]
    }
  },
  "facets": {
    "priority": {
      "high": 8,
      "medium": 5,
      "low": 2
    },
    "status": {
      "todo": 6,
      "in_progress": 7,
      "completed": 2
    }
  }
}
```

## Reports & Analytics API

### Task Statistics

```http
GET /reports/task-statistics?user_id=user-uuid&period=month&date=2024-02
Authorization: Bearer <token>
```

### Project Progress Report

```http
GET /reports/project-progress/{project_id}?include_forecasting=true
Authorization: Bearer <token>
```

### Team Performance Dashboard

```http
GET /reports/team-performance?team_id=team-uuid&period=quarter&year=2024&quarter=1
Authorization: Bearer <token>
```

## Integrations API

### List Available Integrations

```http
GET /integrations
Authorization: Bearer <token>
```

### Configure Integration

```http
POST /integrations/{integration_type}/configure
Content-Type: application/json
Authorization: Bearer <token>

{
  "settings": {
    "github_token": "ghp_xxxxx",
    "repository": "company/project",
    "sync_issues": true,
    "create_branches": true
  }
}
```

### Sync Integration

```http
POST /integrations/{integration_type}/sync
Authorization: Bearer <token>
```

## Webhooks API

### Create Webhook

```http
POST /webhooks
Content-Type: application/json
Authorization: Bearer <token>

{
  "url": "https://your-app.com/taskforge-webhook",
  "events": ["task.created", "task.updated", "task.completed"],
  "secret": "your-webhook-secret",
  "active": true,
  "filters": {
    "project_id": "proj-uuid"
  }
}
```

### Webhook Events

Available webhook events:
- `task.created`
- `task.updated` 
- `task.completed`
- `task.deleted`
- `project.created`
- `project.updated`
- `user.assigned`
- `comment.added`

**Webhook Payload Example:**
```json
{
  "event": "task.completed",
  "timestamp": "2024-02-16T15:30:00Z",
  "data": {
    "task": {
      "id": "task-uuid",
      "title": "Implement user authentication",
      "status": "completed",
      "completed_by": {
        "id": "user-uuid",
        "username": "johndoe"
      }
    }
  },
  "webhook_id": "webhook-uuid"
}
```

## Rate Limiting

### Rate Limit Headers

Every API response includes rate limiting information:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 3600
```

### Rate Limit Exceeded

When rate limit is exceeded, API returns:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "API rate limit exceeded. Try again in 3600 seconds.",
    "retry_after": 3600
  }
}
```

## SDK Examples

### Python SDK

```python
from taskforge_client import TaskForgeClient

# Initialize client
client = TaskForgeClient(
    api_key="your-api-key",
    base_url="https://api.taskforge.dev/v1"
)

# Create a task
task = client.tasks.create(
    title="Implement user authentication",
    description="Add JWT-based authentication",
    priority="high",
    project_id="proj-uuid",
    tags=["authentication", "security"]
)

# List tasks
tasks = client.tasks.list(
    status=["todo", "in_progress"],
    assigned_to="user-uuid",
    limit=50
)

# Update task
client.tasks.update(task.id, {
    "status": "in_progress",
    "completion_percentage": 25
})

# Add time log
client.time_logs.create(
    task_id=task.id,
    duration_minutes=120,
    description="Initial implementation work"
)
```

### JavaScript SDK

```javascript
import { TaskForgeClient } from '@taskforge/client';

const client = new TaskForgeClient({
  apiKey: 'your-api-key',
  baseURL: 'https://api.taskforge.dev/v1'
});

// Create a task
const task = await client.tasks.create({
  title: 'Implement user authentication',
  description: 'Add JWT-based authentication',
  priority: 'high',
  projectId: 'proj-uuid',
  tags: ['authentication', 'security']
});

// List tasks with async iteration
for await (const task of client.tasks.list({ 
  status: ['todo', 'in_progress'],
  assignedTo: 'user-uuid'
})) {
  console.log(`Task: ${task.title} - ${task.status}`);
}

// Real-time updates with WebSocket
client.tasks.subscribe(task.id, (update) => {
  console.log('Task updated:', update);
});
```

## Testing & Development

### Sandbox Environment

Use our sandbox environment for testing:
- Base URL: `https://sandbox-api.taskforge.dev/v1`
- Test data is reset every 24 hours
- All API keys have `sandbox_` prefix

### Postman Collection

Import our Postman collection for easy testing:
```bash
curl -o taskforge-api.postman_collection.json \
  https://api.taskforge.dev/v1/postman-collection
```

### OpenAPI Specification

Full OpenAPI 3.0 specification available at:
```
https://api.taskforge.dev/v1/openapi.json
```

## Support & Resources

- **API Status Page**: [status.taskforge.dev](https://status.taskforge.dev)
- **Developer Documentation**: [docs.taskforge.dev/api](https://docs.taskforge.dev/api)
- **Community Forum**: [GitHub Discussions](https://github.com/taskforge-community/taskforge/discussions)
- **Support Email**: api-support@taskforge.dev

---

*Last Updated: February 2024*
*API Version: 1.0.0*