import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.db.base import Base

if TYPE_CHECKING:
    from models.db.story_task import Story
    from models.db.user import User


class CommentHistory(Base):
    __tablename__ = "comment_history"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    action_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # create, update, delete
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    # Foreign Keys
    comment_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("comments.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    comment: Mapped["Comment"] = relationship("Comment", back_populates="history")
    user: Mapped["User"] = relationship("User", back_populates="comment_histories")


class Comment(Base):
    __versioned__ = {}
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Foreign Keys
    story_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("stories.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    story: Mapped["Story"] = relationship("Story", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="comments")
    history: Mapped[list["CommentHistory"]] = relationship(
        "CommentHistory", back_populates="comment", cascade="all, delete-orphan"
    )
