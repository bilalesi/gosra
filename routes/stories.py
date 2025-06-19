import logging
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from deps import get_current_user_id, get_db, get_redis
from helpers import notify_task_collaborators
from models.db.story_task import Story, StoryTextRevision
from models.db.user import User
from models.schemas.response import ListResponse, Ok, Pagination
from models.schemas.story import (
    StoryContentUpdate,
    StoryCreate,
    StoryResponse,
    StoryTextRevisionResponse,
    StoryUpdate,
)

logger = logging.getLogger("sse-server")

router = APIRouter(prefix="/stories", tags=["stories"])


@router.post("/", response_model=Ok[StoryResponse], status_code=status.HTTP_201_CREATED)
async def create_story(
    story_data: StoryCreate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis_client: Annotated[aioredis.Redis, Depends(get_redis)],
):
    """Create a new story within a task."""
    try:
        # Verify user exists
        result = await db.execute(select(User).where(User.id == user_id))
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        story = Story(
            title=story_data.title,
            description=story_data.description,
            content=story_data.content,
            task_id=story_data.task_id,
            created_by=user_id,
        )
        db.add(story)
        await db.commit()
        await db.refresh(story)

        # Notify task collaborators
        await notify_task_collaborators(
            db,
            redis_client=redis_client,
            task_id=UUID(story_data.task_id),
            message=f"A new story '{story.title}' was created in the task",
            notification_type="story_update",
            exclude_user_id=UUID(user_id),
        )

        await db.commit()

        logger.info(f"Created story: {story.id}")
        return Ok(status="ok", message="Story created successfully.", data=story)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating story: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/{story_id}", response_model=Ok[StoryResponse])
async def get_story(
    story_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get story by ID."""
    try:
        result = await db.execute(select(Story).where(Story.id == story_id))
        story = result.scalar_one_or_none()

        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Story not found"
            )

        return Ok(status="ok", message="Story retrieved successfully.", data=story)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting story: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.put("/{story_id}", response_model=Ok[StoryResponse])
async def update_story(
    story_id: str,
    story_data: StoryUpdate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update story."""
    try:
        result = await db.execute(select(Story).where(Story.id == story_id))
        story = result.scalar_one_or_none()

        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Story not found"
            )

        for field, value in story_data.model_dump(exclude_unset=True).items():
            setattr(story, field, value)

        story.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(story)

        logger.info(f"Updated story: {story.id}")
        return Ok(status="ok", message="Story updated successfully.", data=story)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating story: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.patch("/{story_id}/content", response_model=Ok[StoryResponse])
async def update_story_content(
    story_id: str,
    content_data: StoryContentUpdate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis_client: Annotated[aioredis.Redis, Depends(get_redis)],
):
    """Update story content with revision tracking."""
    try:
        result = await db.execute(select(Story).where(Story.id == story_id))
        story = result.scalar_one_or_none()

        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Story not found"
            )

        story.content = content_data.content
        story.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(story)

        await notify_task_collaborators(
            db=db,
            redis_client=redis_client,
            task_id=UUID(story.task_id),
            message=f"Story content updated for story '{story.title}'",
            notification_type="story_update",
            exclude_user_id=UUID(user_id),
        )
        logger.info(f"Updated story content: {story.id}")
        return Ok(
            status="ok", message="Story content updated successfully.", data=story
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating story content: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.delete("/{story_id}", response_model=Ok[StoryResponse])
async def delete_story(
    story_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a story."""
    try:
        # Check story access (only creator can delete)
        result = await db.execute(select(Story).where(Story.id == story_id))
        story = result.scalar_one_or_none()

        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Story not found"
            )

        if story.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the creator can delete the story",
            )

        story.is_deleted = True
        story.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(story)

        logger.info(f"Deleted story: {story.id}")
        return Ok(status="ok", message="Story deleted successfully.", data=story)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting story: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/{story_id}/revisions", response_model=ListResponse[StoryTextRevisionResponse]
)
async def get_story_revisions(
    story_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 50,
):
    """Get story revisions."""
    try:
        # Get total count
        count_query = select(func.count(StoryTextRevision.id)).where(
            StoryTextRevision.story_id == story_id
        )
        total_items = (await db.execute(count_query)).scalar_one()

        # Get paginated revisions
        query = (
            select(StoryTextRevision)
            .where(StoryTextRevision.story_id == story_id)
            .order_by(StoryTextRevision.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        revisions = list(result.scalars().all())

        return ListResponse(
            status="ok",
            message="Story revisions retrieved successfully.",
            data=revisions,
            pagination=Pagination(
                page=(skip // limit) + 1,
                total_pages=(total_items + limit - 1) // limit if limit > 0 else 0,
                page_size=limit,
                total_items=total_items,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting story revisions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
