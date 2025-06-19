# SSE Server - Server-Sent Events Collaboration Platform

A comprehensive real-time collaboration platform built with FastAPI, PostgreSQL, and Server-Sent Events (SSE) for instant notifications.

## 🏗️ Architecture

This project follows a modular architecture with clear separation of concerns:

### 📁 Project Structure

```
sse/
├── models/                    # Database models and Pydantic schemas (grouped by domain)
│   ├── shared.py             # Base model and shared schemas
│   ├── user.py               # User model and schemas
│   ├── event.py              # Event model and schemas
│   ├── task.py               # Task and TaskCollaborator models/schemas
│   ├── story.py              # Story and StoryTextRevision models/schemas
│   ├── comment.py            # Comment and CommentHistory models/schemas
│   ├── invite.py             # Invite model and schemas
│   ├── notification.py       # Notification model and schemas
│   └── __init__.py           # Package exports
├── helpers/                  # Helper functions (organized by type)
│   ├── db/                   # Database-related helper functions
│   ├── utility/              # Utility/general helper functions
│   ├── db.py                 # Database validation and access control
│   ├── utility.py            # SSE notifications and utilities
│   └── __init__.py           # Package exports
├── routes/                   # API route modules
│   ├── sse.py               # Server-Sent Events endpoints
│   ├── users.py             # User CRUD operations
│   ├── events.py            # Event CRUD and task listing
│   ├── tasks.py             # Task CRUD, collaboration, completion
│   ├── stories.py           # Story CRUD, content updates, revisions
│   ├── comments.py          # Comment CRUD and history
│   └── invites.py           # Invitation system and notifications
├── application.py           # App configuration and database setup
├── routes.py               # Route aggregation and health checks
├── main.py                 # Application entry point
├── settings.py             # Configuration management
├── pyproject.toml          # Project configuration and dependencies
└── uv.lock                 # Dependency lockfile
```

### 🔧 Key Architectural Principles

1. **Domain-Driven Design**: Models and schemas are grouped by business domain (User, Task, Story, etc.)
2. **Separation of Concerns**: Helper functions are categorized as database or utility functions
3. **Type Safety**: Full TypeScript-style type hints with forward references
4. **Modular Routes**: Each feature has its own route module
5. **Dependency Injection**: Consistent use of FastAPI's dependency system

## ✨ Features

### 🔄 Real-Time Collaboration

- **Server-Sent Events (SSE)** for instant notifications
- **Redis pub/sub** for scaling across multiple server instances
- **Real-time updates** for task changes, story updates, and comments

### 👥 User Management

- User registration and profile management
- Event creation and ownership
- Access control and permissions

### 📋 Task Management

- **Hierarchical tasks** with parent-child relationships
- **Duration validation** ensuring subtasks sum to parent duration
- **Collaboration system** with maintainers and collaborators
- **Task completion tracking** with status updates

### 📖 Story System

- **Markdown content** support for rich text stories
- **Revision tracking** with complete edit history using difflib
- **Real-time collaboration** on story content
- **Version control** for content changes

### 💬 Comment System

- **Threaded comments** on stories
- **Comment history** with audit trails
- **Soft delete** functionality
- **Real-time comment notifications**

### 📨 Invitation System

- **Role-based invitations** (maintainer/collaborator)
- **Invitation status tracking** (pending/accepted/rejected/expired)
- **Automatic notifications** for invitation events
- **Expiration handling** for time-limited invites

### 🔔 Notification System

- **Comprehensive notification types**: invites, system, story updates, comments, task updates
- **Real-time delivery** via SSE
- **Notification history** and read status tracking
- **Contextual data** for rich notification content

## 🛠️ Technical Implementation

### Database Models (SQLAlchemy + Pydantic)

Each model group includes:

- **SQLAlchemy ORM models** for database operations
- **Pydantic schemas** for API validation and serialization
- **Type-safe relationships** with forward references
- **Comprehensive constraints** and validations

### Helper Functions

- **Database Helpers** (`helpers/db.py`):

  - Access control validation
  - Data integrity checks
  - Audit trail creation
  - Collaborative notification management

- **Utility Helpers** (`helpers/utility.py`):
  - SSE message broadcasting
  - Path parameter extraction
  - General utility functions

### Route Organization

Each route module handles:

- **CRUD operations** for its domain
- **Business logic** validation
- **Real-time notifications** for changes
- **Access control** enforcement

## 🚀 Getting Started

### Prerequisites

- Python 3.11+ (will be installed automatically by uv)
- PostgreSQL 12+
- Redis 6+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

1. **Install uv** (if not already installed)

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

2. **Clone the repository**

```bash
git clone <repository-url>
cd sse
```

3. **Install dependencies**

```bash
# This will automatically create a virtual environment and install all dependencies
uv sync
```

4. **Configure environment**

```bash
# Set environment variables or modify settings.py
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/sse_db"
export REDIS_URL="redis://localhost:6379"
```

5. **Run the application**

```bash
# Run with uv (recommended)
uv run python main.py

# Or activate the virtual environment and run directly
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python main.py
```

### Development Commands

Using the included Makefile with uv:

```bash
# Sync dependencies (install/update)
make sync

# Run linting
make lint

# Run formatting
make format

# Run type checking
make type-check

# Run tests
make test

# Run all checks
make all

# Clean cache files
make clean
```

The server will start on `http://localhost:8000` with automatic API documentation at `/docs`.

## 📦 Package Management with uv

This project uses [uv](https://docs.astral.sh/uv/) for fast and reliable Python package management. Here are common commands:

### Basic Commands

```bash
# Install dependencies (creates .venv if needed)
uv sync

# Install only production dependencies
uv sync --no-dev

# Add a new dependency
uv add fastapi

# Add a development dependency
uv add --dev pytest

# Remove a dependency
uv remove package-name

# Update dependencies
uv lock --upgrade

# Run a command in the virtual environment
uv run python main.py
uv run pytest
uv run ruff check .

# Activate the virtual environment manually
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

### Environment Management

```bash
# Create a new virtual environment with specific Python version
uv venv --python 3.11

# Use a different Python version
uv python install 3.12
uv venv --python 3.12

# Show current environment info
uv info
```

### Dependency Management

The project dependencies are defined in `pyproject.toml`:

- **Production dependencies**: Listed under `[project.dependencies]`
- **Development dependencies**: Listed under `[project.optional-dependencies.dev]`
- **Lockfile**: `uv.lock` contains exact versions for reproducible builds

## 📚 API Documentation

### Core Endpoints

#### 🔄 Server-Sent Events

- `GET /sse/{user_id}` - Subscribe to real-time events for a user
- `POST /sse/send-message` - Send targeted messages to users

#### 👤 Users

- `POST /users/` - Create user
- `GET /users/{user_id}` - Get user details
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user

#### 📅 Events

- `POST /events/` - Create event
- `GET /events/{event_id}` - Get event details
- `PUT /events/{event_id}` - Update event
- `DELETE /events/{event_id}` - Delete event
- `GET /events/{event_id}/tasks` - List event tasks

#### 📋 Tasks

- `POST /tasks/` - Create task
- `GET /tasks/{task_id}` - Get task details
- `PUT /tasks/{task_id}` - Update task
- `PATCH /tasks/{task_id}/completion` - Toggle completion
- `POST /tasks/{task_id}/collaborators` - Add collaborator
- `GET /tasks/{task_id}/collaborators` - List collaborators
- `GET /tasks/{task_id}/stories` - List task stories

#### 📖 Stories

- `POST /stories/` - Create story
- `GET /stories/{story_id}` - Get story details
- `PUT /stories/{story_id}` - Update story
- `PATCH /stories/{story_id}/content` - Update content only
- `GET /stories/{story_id}/revisions` - List revisions

#### 💬 Comments

- `POST /comments/` - Create comment
- `GET /comments/{comment_id}` - Get comment details
- `PUT /comments/{comment_id}` - Update comment
- `DELETE /comments/{comment_id}` - Soft delete comment
- `GET /comments/{comment_id}/history` - Comment history

#### 📨 Invitations

- `POST /invites` - Create invitation
- `GET /invites/received/{user_id}` - List received invites
- `PATCH /invites/{invite_id}` - Respond to invitation

#### 🔔 Notifications

- `GET /notifications/{user_id}` - List notifications
- `PATCH /notifications/{notification_id}` - Mark as read

## 🧪 Testing

### Example curl commands:

```bash
# Create a user
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

# Create an event
curl -X POST "http://localhost:8000/events/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Meeting",
    "description": "Weekly sync",
    "start_date": "2024-01-15T10:00:00",
    "end_date": "2024-01-15T11:00:00",
    "user_id": "user-uuid-here"
  }'

# Subscribe to SSE events
curl -N "http://localhost:8000/sse/user-uuid-here"
```

## 🔍 Monitoring

Health check endpoint:

```bash
curl "http://localhost:8000/health"
```

Returns database and Redis connection status.

## 🤝 Contributing

1. Follow the modular architecture principles
2. Group related models and schemas in the same file
3. Categorize helper functions appropriately
4. Add comprehensive type hints
5. Include proper error handling
6. Write meaningful commit messages

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
