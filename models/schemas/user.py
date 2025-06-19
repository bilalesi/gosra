from datetime import datetime

from pydantic import BaseModel, Field


# Pydantic Schemas
class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    email: str | None = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$")


class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
