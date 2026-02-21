"""EventIt application configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EVENTIT_", env_file=".env", extra="ignore")

    database_url: str = Field(
        default="postgresql+asyncpg://storeit:storeit_dev@localhost:5433/eventit"
    )
    cors_origins: list[str] = Field(default=["http://localhost:5177", "http://localhost:3000"])
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8005)


settings = Settings()
