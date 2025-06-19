import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.db.base import Base
from models.db.comment import Comment
from models.db.event import Event
from models.db.invite import Invite
from models.db.user import User


class Story(Base):
    __versioned__ = {}
    __tablename__ = "stories"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, default="")  # Markdown content
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Foreign Keys
    task_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("tasks.id"), nullable=False
    )
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="stories")
    creator: Mapped["User"] = relationship("User")
    revisions: Mapped[list["StoryTextRevision"]] = relationship(
        "StoryTextRevision", back_populates="story", cascade="all, delete-orphan"
    )
    comments: Mapped[list[Comment]] = relationship(
        "Comment", back_populates="story", cascade="all, delete-orphan"
    )


class StoryTextRevision(Base):
    __tablename__ = "story_text_revisions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    content_diff: Mapped[str] = mapped_column(Text)  # JSON diff of changes
    full_content: Mapped[str] = mapped_column(Text)  # Full content snapshot
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    # Foreign Keys
    story_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("stories.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="revisions")
    user: Mapped["User"] = relationship("User", back_populates="story_revisions")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    people: Mapped[list[str]] = mapped_column(Text)  # JSON stored as text
    duration: Mapped[int] = mapped_column(Integer, nullable=False)  # in minutes
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Foreign Keys
    event_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("events.id"), nullable=False
    )
    parent_task_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("tasks.id")
    )
    maintainer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    event: Mapped[Event] = relationship("Event", back_populates="tasks")
    parent_task: Mapped[Optional["Task"]] = relationship(
        "Task", back_populates="sub_tasks", remote_side=[id]
    )
    sub_tasks: Mapped[list["Task"]] = relationship("Task", back_populates="parent_task")
    maintainer: Mapped[User] = relationship("User", back_populates="maintained_tasks")
    stories: Mapped[list[Story]] = relationship(
        "Story", back_populates="task", cascade="all, delete-orphan"
    )
    collaborators: Mapped[list["TaskCollaborator"]] = relationship(
        "TaskCollaborator", back_populates="task", cascade="all, delete-orphan"
    )
    invites: Mapped[list[Invite]] = relationship(
        "Invite", back_populates="task", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (CheckConstraint("duration > 0", name="check_positive_duration"),)


class TaskCollaborator(Base):
    __tablename__ = "task_collaborators"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    role: Mapped[str] = mapped_column(
        String(50), default="collaborator"
    )  # maintainer, collaborator
    added_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    # Foreign Keys
    task_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("tasks.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="collaborators")
    user: Mapped["User"] = relationship("User", back_populates="collaborations")

    # Constraints
    __table_args__ = (
        UniqueConstraint("task_id", "user_id", name="uq_task_collaborator"),
    )
