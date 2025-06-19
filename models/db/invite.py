import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.db.base import Base

if TYPE_CHECKING:
    from models.db.story_task import Task
    from models.db.user import User


class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending, accepted, rejected, expired
    message: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(50), default="collaborator")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
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
    inviter_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )
    invitee_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="invites")
    inviter: Mapped["User"] = relationship(
        "User", foreign_keys=[inviter_id], back_populates="sent_invites"
    )
    invitee: Mapped["User"] = relationship(
        "User", foreign_keys=[invitee_id], back_populates="received_invites"
    )
