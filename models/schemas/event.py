from datetime import datetime

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    start_date: datetime
    end_date: datetime
    people: list[str] = Field(default_factory=list)
    planning: str | None = None

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: datetime, info: ValidationInfo) -> datetime:
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class EventCreate(EventBase):
    user_id: str


class EventUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    people: list[str] | None = None
    planning: str | None = None


class EventResponse(EventBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
