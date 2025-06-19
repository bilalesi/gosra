from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db.story_task import Task, TaskCollaborator


async def validate_subtask_duration(
    session: AsyncSession, task_id: str, new_duration: int | None = None
) -> bool:
    """Validate that subtask durations sum up to parent task duration."""
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task or not task.parent_task_id:
        return True  # Not a subtask or task doesn't exist

    # Get parent task
    result = await session.execute(select(Task).where(Task.id == task.parent_task_id))
    parent_task = result.scalar_one_or_none()

    if not parent_task:
        return True  # Parent doesn't exist

    # Get all subtasks
    result = await session.execute(
        select(func.sum(Task.duration)).where(
            and_(Task.parent_task_id == task.parent_task_id, Task.id != task_id)
        )
    )
    other_subtasks_duration = result.scalar() or 0

    current_duration = new_duration if new_duration is not None else task.duration
    total_subtasks_duration = other_subtasks_duration + current_duration

    return total_subtasks_duration == parent_task.duration


async def check_task_access(
    session: AsyncSession,
    task_id: str,
    user_id: str,
    required_permissions: list[str] | None = None,
) -> bool:
    """Check if user has access to a task with required permissions."""
    if required_permissions is None:
        required_permissions = ["collaborator", "maintainer"]

    # Check if user is maintainer
    result = await session.execute(
        select(Task).where(and_(Task.id == task_id, Task.maintainer_id == user_id))
    )
    if result.scalar_one_or_none():
        return True

    # Check if user is collaborator
    result = await session.execute(
        select(TaskCollaborator).where(
            and_(
                TaskCollaborator.task_id == task_id,
                TaskCollaborator.user_id == user_id,
                TaskCollaborator.role.in_(required_permissions),
            )
        )
    )
    collaborator = result.scalar_one_or_none()

    return collaborator is not None
