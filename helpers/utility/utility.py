import json
import logging
from typing import Any

logger = logging.getLogger("sse-server")


async def send_sse_notification(
    notification_data: dict[str, Any],
    user_ids: list[str],
    redis_client: Any | None,
):
    """Send SSE notification to multiple users via Redis."""
    if not redis_client:
        logger.warning("Redis not available - cannot send SSE notification")
        return

    for user_id in user_ids:
        redis_channel = f"user:{user_id}"
        try:
            await redis_client.publish(redis_channel, json.dumps(notification_data))
            logger.debug(
                f"Sent SSE notification to user {user_id}: {notification_data}"
            )
        except Exception as e:
            logger.error(f"Failed to send SSE notification to user {user_id}: {e}")


async def get_user_id_from_path(user_id: str) -> str:
    """Extract user ID from path parameter (for dependency injection)."""
    return user_id
