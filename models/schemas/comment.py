from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .user import UserResponse


# Pydantic Schemas
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


class CommentCreate(CommentBase):
    story_id: str


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


class CommentResponse(CommentBase):
    id: str
    story_id: str
    user_id: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    user: "UserResponse"

    class Config:
        from_attributes = True


class CommentHistoryResponse(BaseModel):
    id: str
    comment_id: str
    user_id: str
    content: str
    action_type: str
    created_at: datetime
    user: "UserResponse"

    class Config:
        from_attributes = True
