from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


# Shared Pydantic schemas
class TargetedMessage(BaseModel):
    """Schema for targeted SSE messages."""

    message: dict[str, Any]
