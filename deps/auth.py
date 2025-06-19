from typing import Annotated

from fastapi import HTTPException, Header, status


async def get_current_user_id(
    x_user_id: Annotated[str | None, Header(alias="X-User-ID")] = None,
) -> str:
    """Dependency to get the current user ID from the X-User-ID header."""
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-User-ID header is missing",
        )
    return x_user_id
