import logging
from typing import Annotated
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from deps import get_current_user_id, get_db, get_redis
from helpers import notify_task_collaborators
from helpers.db.comment import create_comment_history
from models.db.comment import Comment
from models.db.story_task import Story
from models.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from models.schemas.response import ListResponse, Ok, Pagination

logger = logging.getLogger("sse-server")

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post(
    "/", response_model=Ok[CommentResponse], status_code=status.HTTP_201_CREATED
)
async def create_comment(
    comment_data: CommentCreate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis_client: Annotated[aioredis.Redis, Depends(get_redis)],
):
    """Create a new comment on a story."""
    try:
        comment = Comment(
            content=comment_data.content,
            story_id=comment_data.story_id,
            user_id=user_id,
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)

        # Get story for notification context
        story_result = await db.execute(
            select(Story)
            .options(selectinload(Story.task))
            .where(Story.id == comment.story_id)
        )
        story = story_result.scalar_one_or_none()

        if story and story.task:
            # Create DB notifications for all collaborators
            await notify_task_collaborators(
                db=db,
                redis_client=redis_client,
                exclude_user_id=UUID(user_id),
                task_id=UUID(story.task_id),
                message=f"New comment on story '{story.title}'",
                notification_type="new_comment",
                story_id=UUID(story.id),
            )
            await db.commit()

        await db.refresh(comment)
        logger.info(f"Created comment {comment.id} on story {comment.story_id}")
        return Ok(status="ok", message="Comment created successfully.", data=comment)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating comment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/{comment_id}", response_model=Ok[CommentResponse])
async def get_comment(
    comment_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific comment by ID."""
    try:
        result = await db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()

        if not comment or comment.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )

        return Ok(status="ok", message="Comment retrieved successfully.", data=comment)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.put("/{comment_id}", response_model=Ok[CommentResponse])
async def update_comment(
    comment_id: str,
    comment_data: CommentUpdate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a comment."""
    try:
        result = await db.execute(select(Comment).where(Comment.id == comment_id))
        comment = result.scalar_one_or_none()

        if not comment or comment.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )

        if comment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the author can edit the comment",
            )

        comment.content = comment_data.content
        comment.is_edited = True

        await create_comment_history(
            db=db,
            comment_id=comment.id,
            user_id=user_id,
            content=comment.content,
            action_type="update",
        )

        await db.commit()
        await db.refresh(comment)

        logger.info(f"Updated comment {comment.id}")
        return Ok(status="ok", message="Comment updated successfully.", data=comment)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating comment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/story/{story_id}", response_model=ListResponse[CommentResponse])
async def get_comments_for_story(
    story_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 50,
):
    """Retrieve all comments for a specific story."""
    result = await db.execute(select(Comment).where(Comment.story_id == story_id))
    comments = result.scalars().all()
    count_result = await db.execute(
        select(func.count(Comment.id)).where(Comment.story_id == story_id)
    )
    total = count_result.scalar_one()
    return ListResponse(
        status="ok",
        message="Comments retrieved successfully.",
        data=list(comments),
        pagination=Pagination(
            page=skip // limit + 1,
            total_pages=total // limit + 1,
            page_size=limit,
            total_items=total,
        ),
    )


@router.delete("/{comment_id}", response_model=Ok)
async def delete_comment(comment_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    """Delete a comment."""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    await db.delete(comment)
    await db.commit()
    return {"ok": True}
