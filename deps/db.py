import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from models.db.base import Base
from settings import settings

logger = logging.getLogger("sse-server")


class DatabaseManager:
    """Manages database connections and session factory."""

    def __init__(self):
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def initialize(self):
        """Initialize database engine and session factory."""
        self._engine = create_async_engine(settings.database_url, echo=False)
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info(f"Successfully connected to database at {settings.database_url}")

    async def close(self):
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connection closed.")

    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get the session factory."""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized")
        return self._session_factory


db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database dependency for FastAPI routes."""
    session_factory = db_manager.get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
