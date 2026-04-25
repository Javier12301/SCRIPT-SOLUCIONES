from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "DownloaderYT API"
    env: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8000

    secret_key: str = Field(default="change-me-in-env")
    cookie_secure: bool = False
    session_cookie_name: str = "dlyt_session"
    session_ttl_hours: int = 24

    db_path: str = "./data/app.db"
    downloads_root: str = "./downloads"
    worker_concurrency: int = 1
    transfer_retry_seconds: int = 60
    bootstrap_admin_enabled: bool = True
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = "admin1234"

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
