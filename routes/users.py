import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from deps import get_db
from models.db.user import User
from models.schemas.response import Ok
from models.schemas.user import UserCreate, UserResponse, UserUpdate

logger = logging.getLogger("sse-server")

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_model=Ok[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_data: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]
):
    """Create a new user."""
    try:
        # Check if email already exists
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
            )

        new_user = User(**user_data.model_dump())
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return Ok(status="ok", message="User created successfully.", data=new_user)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/{user_id}", response_model=Ok[UserResponse])
async def get_user(user_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return Ok(status="ok", message="User retrieved successfully.", data=user)


@router.put("/{user_id}", response_model=Ok[UserResponse])
async def update_user(
    user_id: str, user_data: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]
):
    """Update user information."""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check if email is being updated and already exists
        if user_data.email and user_data.email != user.email:
            email_result = await db.execute(
                select(User).where(User.email == user_data.email)
            )
            if email_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists",
                )

        # Update user fields
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        user.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(user)
        return Ok(status="ok", message="User updated successfully.", data=user)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
