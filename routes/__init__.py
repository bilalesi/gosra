# Routes package

import logging
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, FastAPI

from deps import get_redis

from .comments import router as comments_router
from .events import router as events_router
from .invites import router as invites_router
from .sse import router as sse_router
from .stories import router as stories_router
from .tasks import router as tasks_router
from .user_settings import router as user_settings_router
from .users import router as users_router

logger = logging.getLogger("sse-server")

# Health check router
router = APIRouter()


@router.get("/health")
async def health_check(
    redis_client: Annotated[aioredis.Redis | None, Depends(get_redis)],
):
    """Health check endpoint."""
    redis_status = "ok" if redis_client else "unavailable"
    return {"status": "ok", "redis": redis_status}


def include_routes(app: FastAPI):
    """Include all route modules in the FastAPI app."""
    app.include_router(sse_router)
    app.include_router(users_router)
    app.include_router(events_router)
    app.include_router(tasks_router)
    app.include_router(stories_router)
    app.include_router(comments_router)
    app.include_router(invites_router)
    app.include_router(router)


__all__ = [
    "comments_router",
    "events_router",
    "invites_router",
    "sse_router",
    "stories_router",
    "tasks_router",
    "users_router",
    "user_settings_router",
]
