import difflib
import json

from sqlalchemy.ext.asyncio import AsyncSession

from models.db.story_task import StoryTextRevision


async def create_story_revision(
    session: AsyncSession,
    story_id: str,
    user_id: str,
    old_content: str,
    new_content: str,
):
    """Create a story text revision for auditing."""
    # Create simple diff
    diff = list(
        difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile="old",
            tofile="new",
        )
    )

    revision = StoryTextRevision(
        story_id=story_id,
        user_id=user_id,
        content_diff=json.dumps(diff),
        full_content=new_content,
        change_type="edit",
    )
    session.add(revision)
    return revision
