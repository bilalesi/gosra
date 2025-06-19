from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, String, event, text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapped, Mapper, mapped_column, relationship

from models.db.base import Base
from models.db.comment import Comment, CommentHistory
from models.db.invite import Invite
from models.db.notification import Notification
from models.db.story_task import Story, StoryTextRevision, Task, TaskCollaborator
from models.db.user_settings import UserSettings


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Relationships
    tasks: Mapped[list[Task]] = relationship("Task", back_populates="maintainer")
    collaborations: Mapped[list[TaskCollaborator]] = relationship(
        "TaskCollaborator", back_populates="user"
    )
    comments: Mapped[list[Comment]] = relationship("Comment", back_populates="user")
    story_revisions: Mapped[list[StoryTextRevision]] = relationship(
        "StoryTextRevision", back_populates="user"
    )
    stories: Mapped[list[Story]] = relationship(
        "Story", back_populates="creator", cascade="all, delete-orphan"
    )
    comment_histories: Mapped[list[CommentHistory]] = relationship(
        "CommentHistory", back_populates="user"
    )
    sent_invites: Mapped[list[Invite]] = relationship(
        "Invite",
        foreign_keys="[Invite.inviter_id]",
        back_populates="inviter",
        cascade="all, delete-orphan",
    )
    received_invites: Mapped[list[Invite]] = relationship(
        "Invite",
        foreign_keys="[Invite.invitee_id]",
        back_populates="invitee",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list[Notification]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    settings: Mapped[UserSettings] = relationship(
        "UserSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


@event.listens_for(User, "after_insert")
def receive_after_insert(mapper: Mapper[User], connection: Connection, target: User):
    """Listen for after a user is created, and create a default settings entry."""
    connection.execute(
        text("INSERT INTO user_settings (user_id) VALUES (:user_id)"),
        {"user_id": target.id},
    )
