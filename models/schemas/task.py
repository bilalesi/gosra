from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .user import UserResponse


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    people: list[str] = Field(default_factory=list)
    duration: int = Field(..., gt=0, description="Duration in minutes")


class TaskCreate(TaskBase):
    event_id: str
    parent_task_id: str | None = None
    maintainer_id: str


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    people: list[str] | None = None
    duration: int | None = Field(None, gt=0)
    is_complete: bool | None = None


class TaskCompletionUpdate(BaseModel):
    is_complete: bool


class TaskResponse(TaskBase):
    id: str
    event_id: str
    parent_task_id: str | None
    maintainer_id: str
    is_complete: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Task Collaboration Schemas
class TaskCollaboratorBase(BaseModel):
    role: str = Field(..., pattern=r"^(maintainer|collaborator)$")


class TaskCollaboratorCreate(TaskCollaboratorBase):
    user_id: str


class TaskCollaboratorUpdate(BaseModel):
    role: str = Field(..., pattern=r"^(maintainer|collaborator)$")


class TaskCollaboratorResponse(TaskCollaboratorBase):
    id: str
    task_id: str
    user_id: str
    added_at: datetime
    user: "UserResponse"

    class Config:
        from_attributes = True
