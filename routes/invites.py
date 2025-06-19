import logging
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from deps import get_current_user_id, get_db, get_redis
from helpers.db.db import notify_task_collaborators
from models.db.invite import Invite
from models.db.story_task import Task
from models.db.user import User
from models.schemas.invite import InviteCreate, InviteResponse, InviteUpdate
from models.schemas.response import Ok

logger = logging.getLogger("sse-server")

router = APIRouter(prefix="/invites", tags=["invites"])


@router.post(
    "/", response_model=Ok[InviteResponse], status_code=status.HTTP_201_CREATED
)
async def create_invite(
    invite_data: InviteCreate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    """Create an invite for a user to collaborate on a task."""
    try:
        # Verify that the inviter has access to the task
        task_result = await db.execute(
            select(Task).where(Task.id == invite_data.task_id)
        )
        task = task_result.scalar_one_or_none()
        if not task or task.maintainer_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No access to this task",
            )

        # Verify that the invitee exists
        invitee_result = await db.execute(
            select(User).where(User.id == invite_data.invitee_id)
        )
        if not invitee_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invitee not found"
            )

        # Create the invite
        new_invite = Invite(
            task_id=invite_data.task_id,
            inviter_id=user_id,
            invitee_id=invite_data.invitee_id,
            role=invite_data.role,
            message=invite_data.message,
            expires_at=invite_data.expires_at,
        )
        db.add(new_invite)
        await db.commit()
        await db.refresh(new_invite)

        # Send notification
        await notify_task_collaborators(
            db=db,
            redis_client=redis,
            task_id=UUID(invite_data.task_id),
            message=f"You have a new invite for task: {task.title}",
            notification_type="invite",
            exclude_user_id=UUID(user_id),
        )

        logger.info(
            f"Invite created from {user_id} to {invite_data.invitee_id} for task {invite_data.task_id}"
        )
        return Ok(status="ok", message="Invite created successfully.", data=new_invite)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating invite: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create invite",
        ) from e


@router.get("/{invite_id}", response_model=Ok[InviteResponse])
async def get_invite(
    invite_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get an invite by its ID."""
    try:
        result = await db.execute(select(Invite).where(Invite.id == invite_id))
        invite = result.scalar_one_or_none()

        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found"
            )

        # Check if the user is the inviter or invitee
        if user_id not in [invite.inviter_id, invite.invitee_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this invite",
            )

        return Ok(status="ok", message="Invite retrieved successfully.", data=invite)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting invite: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve invite",
        ) from e


@router.put("/{invite_id}", response_model=Ok[InviteResponse])
async def respond_to_invite(
    invite_id: str,
    invite_response: InviteUpdate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Respond to an invite (accept or reject)."""
    try:
        result = await db.execute(select(Invite).where(Invite.id == invite_id))
        invite = result.scalar_one_or_none()

        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found"
            )

        if invite.invitee_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to respond to this invite",
            )

        if invite.status != "pending" or (
            invite.expires_at and invite.expires_at < datetime.now(UTC)
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invite is no longer valid",
            )

        invite.status = invite_response.status
        await db.commit()
        await db.refresh(invite)
        logger.info(
            f"User {user_id} responded to invite {invite_id} with {invite_response.status}"
        )
        return Ok(status="ok", message="Invite responded to successfully.", data=invite)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error responding to invite: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not respond to invite",
        ) from e
