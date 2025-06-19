from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Base(BaseModel):
    """Base class for all responses."""

    message: str = Field(..., description="A message indicating the outcome.")
    status: str = Field(..., description="The status of the response.")


class Ok(Base, Generic[T]):
    """Standard success response for single-item results."""

    data: T = Field(..., description="The data payload of the response.")


class Pagination(BaseModel):
    """Pagination details for list responses."""

    page: int = Field(..., description="The current page number.")
    total_pages: int = Field(..., description="The total number of pages.")
    page_size: int = Field(..., description="The number of items per page.")
    total_items: int = Field(..., description="The total number of items.")


class ListResponse(Base, Generic[T]):
    """Standard success response for paginated results."""

    data: list[T] = Field(..., description="The list of data items.")
    pagination: Pagination = Field(..., description="Pagination details for the list.")


class Err(Base):
    """Standard error response for exceptions."""

    error_code: str = Field(..., description="A unique code for the error.")
    details: Any = Field(None, description="Detailed information about the error.")
