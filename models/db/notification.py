import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.db.base import Base
from models.db.task import Story, Task
from models.db.user import User


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # invite, system, story_update, comment, task_update
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[str | None] = mapped_column(Text)  # JSON data for additional context
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    # Foreign Keys
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )
    related_task_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("tasks.id")
    )
    related_story_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("stories.id")
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    related_task: Mapped[Optional["Task"]] = relationship("Task")
    related_story: Mapped[Optional["Story"]] = relationship("Story")
