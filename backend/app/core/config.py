from functools import lru_cache

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SHOGEN_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
