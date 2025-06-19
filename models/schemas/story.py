from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from models.schemas.user import UserResponse


class StoryBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class StoryCreate(StoryBase):
    task_id: str
    content: str


class StoryUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None


class StoryContentUpdate(BaseModel):
    content: str


class StoryResponse(StoryBase):
    id: str
    task_id: str
    created_by: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    content: str

    class Config:
        from_attributes = True


class StoryTextRevisionResponse(BaseModel):
    id: str
    story_id: str
    user_id: str
    change_type: str
    content_diff: str
    full_content: str
    created_at: datetime
    user: "UserResponse"

    class Config:
        from_attributes = True
