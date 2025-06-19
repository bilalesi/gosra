import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.db.base import Base

if TYPE_CHECKING:
    from models.task import Task  # type: ignore
    from models.user import User  # type: ignore


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    people: Mapped[list[str]] = mapped_column(Text)  # JSON stored as text
    planning: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Foreign Keys
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="events")
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="event", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("start_date <= end_date", name="check_event_dates"),
    )
