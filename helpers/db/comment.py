from sqlalchemy.ext.asyncio import AsyncSession

from models.db.comment import CommentHistory


async def create_comment_history(
    db: AsyncSession, comment_id: str, user_id: str, content: str, action_type: str
) -> CommentHistory:
    """
    Creates a historical record for a comment action (create, update).

    Args:
        db: The database session.
        comment_id: The ID of the comment being modified.
        user_id: The ID of the user performing the action.
        content: The new content of the comment.
        action_type: The type of action (e.g., 'create', 'update').

    Returns:
        The created CommentHistory object.
    """
    history_entry = CommentHistory(
        comment_id=comment_id,
        user_id=user_id,
        content=content,
        action_type=action_type,
    )
    db.add(history_entry)
    return history_entry
