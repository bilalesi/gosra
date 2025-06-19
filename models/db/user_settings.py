from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, ForeignKey, types
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.db.base import Base

if TYPE_CHECKING:
    from models.db.user import User


class UserSettings(Base):
    """Stores user-specific settings for notifications and UI preferences."""

    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        default=uuid.uuid4,
    )

    # General Notification Settings
    disable_all_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Globally disable all in-app notifications.",
    )
    disabled_notification_types: Mapped[list[str]] = mapped_column(
        types.JSON,
        nullable=False,
        default=[],
        doc="List of notification types (e.g., 'new_comment') to disable.",
    )
    task_specific_settings: Mapped[dict[str, Any]] = mapped_column(
        types.JSON,
        nullable=False,
        default={},
        doc="JSON object mapping task_ids to specific settings, e.g., "
        "{'task_id_1': {'disable_all': True}, "
        "'task_id_2': {'disabled_types': ['new_comment']}}.",
    )

    # Email Notification Settings (for future use)
    disable_all_email_notifications: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Globally disable all email notifications.",
    )

    # UI Preferences
    ui_preferences: Mapped[dict[str, Any]] = mapped_column(
        types.JSON,
        nullable=False,
        default=lambda: {
            "theme": "system",
            "language": "en",
            "dashboard_layout": "compact",
        },
        doc="JSON object for user interface preferences.",
    )

    # Relationship to User
    user: Mapped[User] = relationship("User", back_populates="settings")
