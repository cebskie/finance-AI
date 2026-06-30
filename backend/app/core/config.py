from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Finance AI System"
    app_version: str = "0.1.0"
    debug: bool = True

    api_v1_prefix: str = "/api/v1"

    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings():
    return Settings()