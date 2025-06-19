from typing import Any

from pydantic import BaseModel


# Shared Pydantic schemas
class TargetedMessage(BaseModel):
    """Schema for targeted SSE messages."""

    message: dict[str, Any]
