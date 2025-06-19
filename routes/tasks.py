import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from deps import get_current_user_id, get_db, get_redis
from helpers.db.task import check_task_access, validate_subtask_duration
from helpers.utility.utility import send_sse_notification
from models.db.story_task import Story, Task, TaskCollaborator
from models.db.user import User
from models.schemas.response import ListResponse, Ok, Pagination
from models.schemas.story import StoryResponse
from models.schemas.task import (
    TaskCollaboratorCreate,
    TaskCollaboratorResponse,
    TaskCompletionUpdate,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)

logger = logging.getLogger("sse-server")

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=Ok[TaskResponse], status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Creates a new task."""
    try:
        if task_data.parent_task_id and not await validate_subtask_duration(
            db, task_data.parent_task_id, task_data.duration
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subtask duration exceeds parent task's remaining duration",
            )

        task = Task(
            **task_data.model_dump(exclude={"maintainer_id"}), maintainer_id=user_id
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        logger.info(f"Task created: {task.id}")
        return Ok(status="ok", message="Task created successfully.", data=task)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error"
        ) from e


@router.get("/", response_model=ListResponse[TaskResponse])
async def list_tasks(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
):
    """Lists all tasks for a user, including those they collaborate on."""
    try:
        base_query = (
            select(Task)
            .outerjoin(Task.collaborators)
            .where(
                or_(
                    Task.maintainer_id == user_id,
                    TaskCollaborator.user_id == user_id,
                )
            )
            .distinct()
        )

        # Get the total count of tasks
        count_query = select(func.count()).select_from(base_query.alias())
        total_items = (await db.execute(count_query)).scalar_one()

        # Get the paginated list of tasks
        query = base_query.offset(skip).limit(limit)
        result = await db.execute(query)
        tasks = list(result.scalars().all())

        return ListResponse(
            status="ok",
            message="Tasks retrieved successfully.",
            data=tasks,
            pagination=Pagination(
                page=(skip // limit) + 1,
                total_pages=(total_items + limit - 1) // limit if limit > 0 else 0,
                page_size=limit,
                total_items=total_items,
            ),
        )
    except Exception as e:
        logger.error(f"Error listing tasks for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error"
        ) from e


@router.get("/{task_id}", response_model=Ok[TaskResponse])
async def get_task(
    task_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Gets a specific task by ID."""
    if not await check_task_access(db, task_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return Ok(status="ok", message="Task retrieved successfully.", data=task)


@router.put("/{task_id}", response_model=Ok[TaskResponse])
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    """Updates a task."""
    try:
        if not await check_task_access(
            db, task_id, user_id, required_permissions=["maintainer"]
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        update_data = task_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)
        task.updated_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(task)

        # Notify collaborators
        notification_data = {
            "type": "task_update",
            "message": f"Task '{task.title}' has been updated.",
            "task_id": task.id,
        }
        collaborators_result = await db.execute(
            select(TaskCollaborator.user_id).where(TaskCollaborator.task_id == task_id)
        )
        collaborator_ids = [row[0] for row in collaborators_result]
        await send_sse_notification(notification_data, collaborator_ids, redis)

        logger.info(f"Task {task_id} updated by {user_id}")
        return Ok(status="ok", message="Task updated successfully.", data=task)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating task {task_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error"
        ) from e


@router.patch("/{task_id}/completion", response_model=Ok[TaskResponse])
async def update_task_completion(
    task_id: str,
    completion_data: TaskCompletionUpdate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Updates the completion status of a task."""
    if not await check_task_access(db, task_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    task.is_complete = completion_data.is_complete
    task.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(task)
    logger.info(f"Task {task_id} completion status updated to {task.is_complete}")
    return Ok(
        status="ok", message="Task completion status updated successfully.", data=task
    )


@router.post(
    "/{task_id}/collaborators",
    response_model=Ok[TaskCollaboratorResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_collaborator(
    task_id: str,
    collaborator_data: TaskCollaboratorCreate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Adds a collaborator to a task."""
    if not await check_task_access(
        db, task_id, user_id, required_permissions=["maintainer"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only maintainer can add"
        )
    # Check if user to be added exists
    user_to_add_result = await db.execute(
        select(User).where(User.id == collaborator_data.user_id)
    )
    if not user_to_add_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User to add not found")

    collaborator = TaskCollaborator(task_id=task_id, **collaborator_data.model_dump())
    db.add(collaborator)
    await db.commit()
    await db.refresh(collaborator)
    logger.info(f"Added collaborator {collaborator.user_id} to task {task_id}")
    return Ok(
        status="ok", message="Collaborator added successfully.", data=collaborator
    )


@router.get("/{task_id}/stories", response_model=ListResponse[StoryResponse])
async def list_stories_for_task(
    task_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
):
    """Lists all non-deleted stories for a specific task with pagination.

    The stories are ordered by their creation date in descending order.
    """
    if not await check_task_access(db, task_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Get the total number of stories for the task
    count_query = select(func.count(Story.id)).where(
        Story.task_id == task_id, Story.is_deleted.is_(False)
    )
    total_items = (await db.execute(count_query)).scalar_one()

    # Get the paginated list of stories
    query = (
        select(Story)
        .where(Story.task_id == task_id, Story.is_deleted.is_(False))
        .order_by(Story.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    stories = list(result.scalars().all())

    return ListResponse(
        status="ok",
        message="Stories retrieved successfully",
        data=stories,
        pagination=Pagination(
            page=(skip // limit) + 1,
            total_pages=(total_items + limit - 1) // limit if limit > 0 else 0,
            page_size=limit,
            total_items=total_items,
        ),
    )
