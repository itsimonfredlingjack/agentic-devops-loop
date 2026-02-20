"""Application configuration via Pydantic BaseSettings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """BookIt application settings.

    Values are read from environment variables (case-insensitive).
    Defaults are suitable for local development.
    """

    database_url: str = "bookit.db"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    cancellation_deadline_hours: int = 24

    # SMTP / email settings
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@bookit.local"
    email_enabled: bool = False

    model_config = {"env_prefix": "BOOKIT_", "case_sensitive": False}


settings = Settings()
