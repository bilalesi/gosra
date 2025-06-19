import json
import logging
from collections.abc import AsyncGenerator
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from deps import get_redis
from deps.sse import sse_event_stream
from models.schemas.response import Ok
from models.schemas.shared import TargetedMessage

logger = logging.getLogger("sse-server")

router = APIRouter(prefix="/sse", tags=["sse"])


@router.get("/sse/{user_id}")
async def sse_endpoint(
    events: Annotated[AsyncGenerator[str, None], Depends(sse_event_stream)],
):
    """The SSE endpoint. Clients connect here to receive real-time updates.

    The `user_id` in the path determines which channel they listen to.
    """
    return StreamingResponse(events, media_type="text/event-stream")


@router.post(
    "/send-to-user/{user_id}",
    response_model=Ok[dict[str, str]],
    status_code=status.HTTP_200_OK,
)
async def send_to_user(
    payload: TargetedMessage,
    user_id: str,
    redis_client: Annotated[aioredis.Redis | None, Depends(get_redis)],
):
    """An endpoint for other services to send a message to a specific user."""
    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot send message, Redis is not available.",
        )

    redis_channel = f"user:{user_id}"
    message_str = json.dumps(payload.message)
    await redis_client.publish(redis_channel, message_str)
    logger.info(f"Message published to channel '{redis_channel}' for user '{user_id}'")
    return Ok(
        status="ok",
        message="Message published successfully.",
        data={"channel": redis_channel},
    )
