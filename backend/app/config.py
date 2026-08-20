"""Application settings — all env access lives here."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./dev-fallback.db"
    app_name: str = "AI Business Analytics Platform"
    app_env: str = "development"
    cors_origins: str = "*"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @property
    def sqlalchemy_url(self) -> str:
        url = self.database_url
        if url.startswith("mysql") and "charset" not in url:
            url += "?charset=utf8mb4"
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
