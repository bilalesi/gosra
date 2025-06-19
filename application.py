import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from deps import db_manager, redis_manager
from models.schemas.response import Err
from routes import (
    comments_router,
    events_router,
    invites_router,
    sse_router,
    stories_router,
    tasks_router,
    user_settings_router,
    users_router,
)
from settings import settings

# Logging Setup
logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger("sse-server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Server starting up...")

    # Initialize database and Redis
    await db_manager.initialize()
    await redis_manager.initialize()

    yield

    # Shutdown
    logger.info("Server shutting down...")
    await redis_manager.close()
    await db_manager.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(lifespan=lifespan, title="SSE Server with Database", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(  # pyright: ignore[reportUnusedFunction]
        request: Request, exc: HTTPException
    ):
        """Custom exception handler to return error responses in a standard format."""
        return JSONResponse(
            status_code=exc.status_code,
            content=Err(
                status="error",
                message=str(exc.detail),
                error_code=str(exc.status_code),
                details=exc.detail,
            ).model_dump(),
        )

    def configure_routes(app: FastAPI):
        """Include all the API routers."""
        app.include_router(users_router, prefix="/users", tags=["Users"])
        app.include_router(stories_router, prefix="/stories", tags=["Stories"])
        app.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
        app.include_router(comments_router, prefix="/comments", tags=["Comments"])
        app.include_router(invites_router, prefix="/invites", tags=["Invites"])
        app.include_router(events_router, prefix="/events", tags=["Events"])
        app.include_router(sse_router, prefix="/sse", tags=["SSE"])
        app.include_router(
            user_settings_router, prefix="/settings", tags=["User Settings"]
        )

    configure_routes(app)
    return app
