from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .task import TaskResponse
    from .user import UserResponse


class InviteBase(BaseModel):
    message: str | None = None
    role: str = Field(..., pattern=r"^(maintainer|collaborator)$")
    expires_at: datetime | None = None


class InviteCreate(InviteBase):
    task_id: str
    invitee_id: str


class InviteUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(pending|accepted|rejected|expired)$")


class InviteResponse(InviteBase):
    id: str
    task_id: str
    inviter_id: str
    invitee_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    inviter: "UserResponse"
    invitee: "UserResponse"
    task: "TaskResponse"

    class Config:
        from_attributes = True
