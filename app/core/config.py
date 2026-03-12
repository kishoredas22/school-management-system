"""Application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "School Management System"
    environment: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    secret_key: str = Field(default="change-me-in-production", min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    access_token_expire_minutes: int = 60
    email_login_link_expire_minutes: int = 30
    frontend_app_url: str = "http://localhost:5173"
    database_url: str = "postgresql+psycopg://sms:sms@db:5432/school_management"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    attendance_edit_window_days: int = 3
    default_page_size: int = 20
    max_page_size: int = 100
    log_level: str = "INFO"
    initial_super_admin_username: str = "superadmin"
    initial_super_admin_password: str = "password123"

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on", "debug"}

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


settings = get_settings()
