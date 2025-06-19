from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    database_url: str = "postgresql+asyncpg://postgres:sse@127.0.0.1:5432/sse"
    allowed_origins: str = "*"
    log_level: str = "INFO"
    sse_heartbeat_interval: int = 15  # Seconds

    class Config:
        env_file = ".env"


settings = Settings()
