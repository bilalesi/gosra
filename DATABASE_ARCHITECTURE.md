# Database Architecture

This document outlines the database schema for the SSE application. It includes details on each table and a diagram illustrating the relationships between them.

## Table Relationships

- **users**: The central table for user accounts.
- **events**: Represents high-level events or milestones. Each event is owned by a single **user**.
- **tasks**: The core unit of work.
  - Each task belongs to one **event**.
  - Each task has one **user** as a maintainer.
  - Tasks can be hierarchical, with a task having a `parent_task_id` that points to another task.
- **task_collaborators**: A many-to-many join table between **tasks** and **users**, defining which users are collaborators on which tasks and their role.
- **stories**: Represents a document or narrative associated with a **task**. Each story is created by a **user**.
- **story_text_revisions**: Stores the change history for a **story**, linking each revision to the **user** who made it.
- **comments**: Holds user comments on a **story**. Each comment is made by a **user**.
-
- **comment_history**: Stores the edit/deletion history of a **comment**, linking each history entry to the **user** who performed the action.
- **invites**: Manages invitations for **users** to collaborate on **tasks**. It tracks the inviter, the invitee, and the status of the invitation.
- **notifications**: Stores notifications for **users**. Notifications can be optionally linked to a `related_task_id` or `related_story_id`.

## Entity-Relationship Diagram

```mermaid
erDiagram
    users {
        string id PK
        string name
        string email
        datetime created_at
        datetime updated_at
    }

    events {
        string id PK
        string user_id FK
        string title
        datetime start_date
        datetime end_date
    }

    tasks {
        string id PK
        string event_id FK
        string maintainer_id FK
        string parent_task_id FK
        string title
        int duration
        bool is_complete
    }

    task_collaborators {
        string id PK
        string task_id FK
        string user_id FK
        string role
    }

    stories {
        string id PK
        string task_id FK
        string created_by FK
        string title
        text content
        bool is_deleted
    }

    story_text_revisions {
        string id PK
        string story_id FK
        string user_id FK
        text content_diff
    }

    comments {
        string id PK
        string story_id FK
        string user_id FK
        text content
        bool is_deleted
    }

    comment_history {
        string id PK
        string comment_id FK
        string user_id FK
        text content
        string action_type
    }

    invites {
        string id PK
        string task_id FK
        string inviter_id FK
        string invitee_id FK
        string status
        string role
    }

    notifications {
        string id PK
        string user_id FK
        string related_task_id FK
        string related_story_id FK
        string title
        string message
        bool is_read
    }

    users ||--o{ events : "has"
    users ||--o{ tasks : "maintains"
    users ||--o{ task_collaborators : "collaborates on"
    users ||--o{ stories : "creates"
    users ||--o{ story_text_revisions : "revises"
    users ||--o{ comments : "writes"
    users ||--o{ comment_history : "audits"
    users ||--o{ invites : "sends/receives"
    users ||--o{ notifications : "receives"
    events ||--|{ tasks : "contains"
    tasks ||--o{ stories : "contains"
    tasks ||--o{ task_collaborators : "has"
    tasks ||--o{ invites : "is subject of"
    tasks ||--o{ notifications : "is related to"
    tasks ||--o{ tasks : "is parent of"
    stories ||--o{ story_text_revisions : "has"
    stories ||--o{ comments : "has"
    stories ||--o{ notifications : "is related to"
    comments ||--o{ comment_history : "has"

```
