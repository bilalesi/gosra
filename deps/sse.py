import asyncio
import logging
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, Request

from deps.redis import get_redis
from settings import settings

logger = logging.getLogger("sse-server")


async def sse_event_stream(
    request: Request,
    user_id: str,
    redis_client: Annotated[aioredis.Redis | None, Depends(get_redis)],
):
    """Listens to a user-specific Redis Pub/Sub channel and yields messages.

    Also sends periodic heartbeats to keep the connection alive.
    """
    if not redis_client:
        error_message = "Server is not connected to Redis. Cannot process SSE."
        logger.error(error_message)
        return

    redis_channel = f"user:{user_id}"
    pubsub = redis_client.pubsub()

    try:
        await pubsub.subscribe(redis_channel)
        logger.info(
            f"Client for user '{user_id}' subscribed to Redis channel: "
            f"'{redis_channel}'"
        )

        while True:
            # Check for client disconnect first
            if await request.is_disconnected():
                logger.info(f"Client for user '{user_id}' disconnected.")
                break

            # Wait for a message from Redis with a timeout for the heartbeat
            try:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=settings.sse_heartbeat_interval,
                )

                if message and message.get("type") == "message":
                    data = message.get("data")
                    logger.debug(f"Publishing message to user '{user_id}': {data}")
                    yield f"data: {data}\n\n"
                else:
                    # No message received, send a heartbeat to keep connection alive
                    logger.debug(f"Sending heartbeat to user '{user_id}'")
                    yield ":heartbeat\n\n"

            except TimeoutError:
                # This is expected if timeout is set in get_message
                logger.debug(f"Timeout, sending heartbeat to user '{user_id}'")
                yield ":heartbeat\n\n"

    except asyncio.CancelledError:
        logger.info(f"Connection cancelled for user '{user_id}'.")
    except Exception as e:
        logger.error(f"An error occurred for user '{user_id}': {e}", exc_info=True)
    finally:
        logger.info(
            f"Closing resources for user '{user_id}'. "
            f"Unsubscribing from '{redis_channel}'"
        )
        await pubsub.close()
