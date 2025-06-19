# Task-Based Story System Implementation Summary

## Overview

The SSE application has been enhanced with a comprehensive task-based story system that includes:

1. **Task-Centric Stories**: Stories are now attached to tasks instead of being standalone
2. **Invitation System**: Task maintainers can invite collaborators
3. **Notification System**: Real-time notifications for all collaborative activities
4. **Role-Based Access Control**: Maintainer and collaborator roles with different permissions

## Database Schema Changes

### Updated Models

#### 1. User Model

- Added relationships for task maintenance, collaborations, invites, and notifications

```python
maintained_tasks: Mapped[List["Task"]] = relationship("Task", back_populates="maintainer")
task_collaborations: Mapped[List["TaskCollaborator"]] = relationship("TaskCollaborator", back_populates="user")
sent_invites: Mapped[List["Invite"]] = relationship("Invite", foreign_keys="Invite.inviter_id", back_populates="inviter")
received_invites: Mapped[List["Invite"]] = relationship("Invite", foreign_keys="Invite.invitee_id", back_populates="invitee")
notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user")
```

#### 2. Task Model

- Added `maintainer_id` field (required)
- Added relationships for stories, collaborators, and invites

```python
maintainer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
maintainer: Mapped["User"] = relationship("User", back_populates="maintained_tasks")
stories: Mapped[List["Story"]] = relationship("Story", back_populates="task")
collaborators: Mapped[List["TaskCollaborator"]] = relationship("TaskCollaborator", back_populates="task")
invites: Mapped[List["Invite"]] = relationship("Invite", back_populates="task")
```

#### 3. Story Model

- Changed from `owner_id` to `task_id` and `created_by`
- Removed `is_public` field (access controlled via task permissions)

```python
task_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tasks.id"), nullable=False)
created_by: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
task: Mapped["Task"] = relationship("Task", back_populates="stories")
creator: Mapped["User"] = relationship("User")
```

### New Models

#### 4. TaskCollaborator

```python
class TaskCollaborator(Base):
    __tablename__ = "task_collaborators"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    role: Mapped[str] = mapped_column(String(50), default="collaborator")  # maintainer, collaborator
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    task_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tasks.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)

    task: Mapped["Task"] = relationship("Task", back_populates="collaborators")
    user: Mapped["User"] = relationship("User", back_populates="task_collaborations")
```

#### 5. Invite

```python
class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, accepted, rejected, expired
    message: Mapped[Optional[str]] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(50), default="collaborator")
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    task_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("tasks.id"), nullable=False)
    inviter_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    invitee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)

    task: Mapped["Task"] = relationship("Task", back_populates="invites")
    inviter: Mapped["User"] = relationship("User", foreign_keys=[inviter_id], back_populates="sent_invites")
    invitee: Mapped["User"] = relationship("User", foreign_keys=[invitee_id], back_populates="received_invites")
```

#### 6. Notification

```python
class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # invite, system, story_update, comment, task_update
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[Optional[str]] = mapped_column(Text)  # JSON data for additional context
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    related_task_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("tasks.id"))
    related_story_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("stories.id"))

    user: Mapped["User"] = relationship("User", back_populates="notifications")
    related_task: Mapped[Optional["Task"]] = relationship("Task")
    related_story: Mapped[Optional["Story"]] = relationship("Story")
```

## Updated Pydantic Schemas

### Task Schemas

```python
class TaskCreate(TaskBase):
    event_id: str
    parent_task_id: Optional[str] = None
    maintainer_id: str  # New required field

class TaskResponse(TaskBase):
    id: str
    event_id: str
    parent_task_id: Optional[str]
    maintainer_id: str  # New field
    is_complete: bool
    created_at: datetime
    updated_at: datetime
```

### Story Schemas

```python
class StoryCreate(StoryBase):
    task_id: str  # Changed from being standalone

class StoryResponse(StoryBase):
    id: str
    task_id: str  # Changed from owner_id
    created_by: str  # New field
    created_at: datetime
    updated_at: datetime
```

### New Schemas

- `TaskCollaboratorBase`, `TaskCollaboratorCreate`, `TaskCollaboratorUpdate`, `TaskCollaboratorResponse`
- `InviteBase`, `InviteCreate`, `InviteUpdate`, `InviteResponse`
- `NotificationBase`, `NotificationCreate`, `NotificationUpdate`, `NotificationResponse`

## Utility Functions

### New Access Control Functions

```python
async def check_task_access(session: AsyncSession, task_id: str, user_id: str, required_permissions: List[str] = None) -> bool:
    """Check if user has access to a task with required permissions"""
    # Checks if user is maintainer or collaborator with appropriate role

async def check_story_access(session: AsyncSession, story_id: str, user_id: str) -> bool:
    """Check if user has access to a story (through task access)"""
    # Access controlled via task permissions
```

### Notification Functions

```python
async def create_notification(session: AsyncSession, user_id: str, notification_type: str, title: str, message: str, ...):
    """Create a notification for a user"""

async def notify_task_collaborators(session: AsyncSession, task_id: str, notification_type: str, title: str, message: str, ...):
    """Send notifications to all task collaborators"""

async def send_sse_notification(notification_data: Dict[str, Any], user_ids: List[str]):
    """Send SSE notification to multiple users"""
```

## New API Endpoints

### Task Collaboration

- `POST /tasks/{task_id}/collaborators` - Add collaborator (maintainer only)
- `GET /tasks/{task_id}/collaborators` - List task collaborators
- `DELETE /tasks/{task_id}/collaborators/{collaborator_id}` - Remove collaborator

### Invitations

- `POST /invites` - Create invitation (maintainer only)
- `GET /invites/received/{user_id}` - List received invitations
- `PATCH /invites/{invite_id}` - Accept/reject invitation

### Notifications

- `GET /notifications/{user_id}` - List user notifications
- `PATCH /notifications/{notification_id}` - Mark notification as read/unread

### Enhanced Endpoints

- `GET /tasks/{task_id}/stories` - List stories within a task
- `GET /events/{event_id}/tasks` - List tasks within an event

## Updated Existing Endpoints

### Story Creation

- Now requires `task_id` and user access to the task
- Creates notifications for all task collaborators
- Sends SSE notifications for real-time updates

### Story Updates/Comments

- Access controlled via task permissions
- Notifications sent to all task collaborators
- SSE events for real-time collaboration

### Task Creation

- Now requires `maintainer_id`
- Validates maintainer exists

## Key Features

### 1. Permission System

- **Task Maintainer**: Can invite collaborators, manage task, full access to all stories
- **Task Collaborator**: Can create/edit stories, comment, view all task content
- **Access Control**: Story access is inherited from task permissions

### 2. Invitation Workflow

1. Maintainer creates invite with role and optional message
2. Invitee receives notification and SSE event
3. Invitee accepts/rejects invitation
4. If accepted, becomes collaborator with specified role
5. All task collaborators notified of new member

### 3. Notification Types

- `invite`: Task invitation received
- `system`: System messages
- `story_update`: Story created/updated
- `comment`: New comment on story
- `task_update`: Task changes, new collaborators

### 4. Real-Time Features

- SSE notifications for all collaborative activities
- Live updates when stories are created/updated
- Immediate notification of invitations and responses

## Migration Considerations

### Database Migration

1. Add new tables: `task_collaborators`, `invites`, `notifications`
2. Add `maintainer_id` to `tasks` table
3. Update `stories` table: remove `owner_id`, `is_public`; add `task_id`, `created_by`
4. Update foreign key constraints

### Data Migration

1. Assign existing tasks to maintainers (could be event owners)
2. Migrate existing stories to be associated with tasks
3. Create initial notifications for existing data if needed

## Benefits

1. **Better Organization**: Stories are organized within tasks
2. **Clear Ownership**: Task maintainers have clear responsibility
3. **Controlled Collaboration**: Invitation-based access control
4. **Real-Time Awareness**: SSE notifications for all activities
5. **Audit Trail**: Complete notification history
6. **Scalable Permissions**: Role-based access that can be extended

This implementation provides a robust foundation for collaborative task management with stories, featuring proper access control, real-time notifications, and a clear permission hierarchy.
