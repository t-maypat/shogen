from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Shogen Backend")
    environment: str = Field(default="local")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    log_level: str = Field(default="INFO")
    database_url: str = Field(
        default="postgresql+psycopg://shogen:shogen@localhost:5432/shogen"
    )
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    model_provider: Literal["fake", "azure_openai"] = Field(default="fake")
    model_timeout_seconds: float = Field(default=20.0, gt=0)
    azure_openai_endpoint: str | None = Field(default=None)
    azure_openai_api_key: str | None = Field(default=None)
    azure_openai_api_version: str = Field(default="2024-08-01-preview")
    azure_openai_deployment: str | None = Field(default=None)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SHOGEN_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
