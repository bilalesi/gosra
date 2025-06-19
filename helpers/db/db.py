from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helpers.utility.utility import send_sse_notification
from models.db.notification import Notification
from models.db.story_task import TaskCollaborator
from models.db.user_settings import UserSettings

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger("sse-server")


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    message: str,
    notification_type: str,
    task_id: UUID | None = None,
    story_id: UUID | None = None,
    commit_id: str | None = None,
) -> Notification | None:
    """Creates a notification for a user, respecting their notification settings.

    Returns the notification object if created, otherwise None.
    """
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == str(user_id))
    )
    settings = result.scalar_one_or_none()

    if settings:
        if settings.disable_all_notifications is True:
            return None
        if notification_type in settings.disabled_notification_types:
            return None
        if task_id and settings.task_specific_settings:
            task_settings = settings.task_specific_settings.get(str(task_id))
            if isinstance(task_settings, dict):
                if task_settings.get("disable_all") is True:
                    return None
                if notification_type in task_settings.get("disabled_types", []):
                    return None

    notification = Notification(
        user_id=user_id,
        message=message,
        type=notification_type,
        task_id=task_id,
        story_id=story_id,
        commit_id=commit_id,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def notify_task_collaborators(
    db: AsyncSession,
    redis_client: Redis,
    task_id: UUID,
    message: str,
    notification_type: str,
    exclude_user_id: UUID,
    story_id: UUID | None = None,
    commit_id: str | None = None,
):
    """
    Creates and dispatches notifications to all collaborators of a task,
    excluding one user, and respecting each user's notification settings.

    Args:
        db: The database session.
        redis_client: The Redis client.
        task_id: The ID of the task.
        message: The message to send.
        notification_type: The type of notification.
        exclude_user_id: The ID of the user to exclude.
        story_id: The ID of the story.
        commit_id: The ID of the commit.

    Returns:
        None
    """
    result = await db.execute(
        select(TaskCollaborator).where(TaskCollaborator.task_id == task_id)
    )
    collaborators = result.scalars().all()

    for collaborator in collaborators:
        if collaborator.user_id != exclude_user_id:
            notification = await create_notification(
                db=db,
                user_id=UUID(collaborator.user_id),
                message=message,
                notification_type=notification_type,
                task_id=task_id,
                story_id=story_id,
                commit_id=commit_id,
            )
            if notification:
                await send_sse_notification(
                    notification_data={
                        "event": notification.type,
                        "data": {
                            "message": notification.message,
                            "task_id": str(task_id),
                            "story_id": str(story_id) if story_id else None,
                            "commit_id": commit_id,
                        },
                    },
                    user_ids=[str(collaborator.user_id)],
                    redis_client=redis_client,
                )
