from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", ".env.local"), env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CacheCraft API"
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./cachecraft.db"
    transformer_delay_seconds: float = Field(default=0, ge=0, le=60)
    cache_cleanup_interval_seconds: int = Field(default=3600, ge=0)
    cache_ttl_seconds: int = Field(default=86400, ge=0)
    api_prefix: str = "/api/v1"

    @field_validator("api_prefix")
    @classmethod
    def normalize_prefix(cls, value: str) -> str:
        value = "/" + value.strip("/")
        return "" if value == "/" else value


@lru_cache
def get_settings() -> Settings:
    return Settings()
