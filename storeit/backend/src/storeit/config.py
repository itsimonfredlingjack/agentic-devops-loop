"""StoreIt application configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STOREIT_", env_file=".env", extra="ignore")

    database_url: str = Field(
        default="postgresql+asyncpg://storeit:storeit_dev@localhost:5433/storeit"
    )
    test_database_url: str = Field(default="sqlite+aiosqlite:///:memory:")
    cors_origins: list[str] = Field(default=["http://localhost:5175", "http://localhost:3000"])
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8004)

    # Stripe (Phase 3)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_enabled: bool = False
    frontend_url: str = "http://localhost:5175"

    # Inventory reservation TTL
    reservation_ttl_minutes: int = 15


settings = Settings()
