import json
import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from deps import get_current_user_id, get_db, get_redis
from models.db.event import Event
from models.db.story_task import Task
from models.db.user import User
from models.schemas.event import EventCreate, EventResponse, EventUpdate
from models.schemas.response import ListResponse, Ok, Pagination
from models.schemas.task import TaskResponse

logger = logging.getLogger("sse-server")

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=Ok[EventResponse], status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new event."""
    try:
        # Verify user exists
        result = await db.execute(select(User).where(User.id == user_id))
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        event = Event(
            title=event_data.title,
            description=event_data.description,
            start_date=event_data.start_date,
            end_date=event_data.end_date,
            people=json.dumps(event_data.people),
            planning=event_data.planning,
            user_id=user_id,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)

        # Parse people back to list for response
        event.people = (
            json.loads(event.people) if isinstance(event.people, str) else event.people
        )

        logger.info(f"Created event: {event.id}")
        return Ok(status="ok", message="Event created successfully.", data=event)
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating event: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/", response_model=ListResponse[EventResponse])
async def list_events(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
):
    """List all events for the user."""
    try:
        # Get total count
        count_query = select(func.count(Event.id)).where(Event.user_id == user_id)
        total_items = (await db.execute(count_query)).scalar_one()

        # Get paginated events
        query = (
            select(Event)
            .where(Event.user_id == user_id)
            .order_by(Event.created_at)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        events = list(result.scalars().all())

        # Parse people from JSON string for each event
        for event in events:
            event.people = (
                json.loads(event.people)
                if isinstance(event.people, str)
                else event.people
            )

        return ListResponse(
            status="ok",
            message="Events retrieved successfully.",
            data=events,
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
        logger.error(f"Error listing events: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/{event_id}", response_model=Ok[EventResponse])
async def get_event(
    event_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific event by ID."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    if event.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Parse people from JSON string
    event.people = (
        json.loads(event.people) if isinstance(event.people, str) else event.people
    )
    return Ok(status="ok", message="Event retrieved successfully.", data=event)


@router.put("/{event_id}", response_model=Ok[EventResponse])
async def update_event(
    event_id: str,
    event_data: EventUpdate,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    """Update an event."""
    try:
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
            )
        if event.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        # Update fields
        update_data = event_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "people" and value is not None:
                setattr(event, field, json.dumps(value))
            elif value is not None:
                setattr(event, field, value)

        event.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(event)

        # Parse people back to list for response
        event.people = (
            json.loads(event.people) if isinstance(event.people, str) else event.people
        )

        logger.info(f"Updated event: {event.id}")
        return Ok(status="ok", message="Event updated successfully.", data=event)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating event: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.delete(
    "/{event_id}", response_model=Ok[dict[str, str]], status_code=status.HTTP_200_OK
)
async def delete_event(
    event_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete an event."""
    try:
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
            )
        if event.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        await db.delete(event)
        await db.commit()

        logger.info(f"Deleted event: {event_id}")
        return Ok(
            status="ok",
            message="Event deleted successfully.",
            data={"id": event_id},
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting event: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/{event_id}/tasks", response_model=ListResponse[TaskResponse])
async def list_event_tasks(
    event_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
):
    """List tasks within an event."""
    try:
        # Check if event exists and user has access
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        if event.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )
        # Get total count
        count_query = select(func.count(Task.id)).where(Task.event_id == event_id)
        total_items = (await db.execute(count_query)).scalar_one()

        # Get paginated tasks
        query = (
            select(Task)
            .where(Task.event_id == event_id)
            .order_by(Task.created_at)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        tasks = list(result.scalars().all())

        # Parse people from JSON string for each task
        for task in tasks:
            task.people = (
                json.loads(task.people) if isinstance(task.people, str) else task.people
            )

        return ListResponse(
            status="ok",
            message="Event tasks retrieved successfully.",
            data=tasks,
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
        logger.error(f"Error listing event tasks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
