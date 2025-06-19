from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NotificationBase(BaseModel):
    type: str = Field(
        ..., pattern=r"^(invite|system|story_update|comment|task_update)$"
    )
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    data: dict[str, Any] | None = None


class NotificationCreate(NotificationBase):
    user_id: str
    related_task_id: str | None = None
    related_story_id: str | None = None


class NotificationUpdate(BaseModel):
    is_read: bool


class NotificationResponse(NotificationBase):
    id: str
    user_id: str
    related_task_id: str | None
    related_story_id: str | None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
