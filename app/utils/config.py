from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    app_name: str = "CIIP API"
    app_schema: str = Field(default="public", alias="APP_SCHEMA")
    postgres_url: str = Field(alias="POSTGRES_URL")
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    supabase_jwt_secret: Optional[str] = Field(default=None, alias="SUPABASE_JWT_SECRET")
    supabase_jwks_url: Optional[str] = Field(default=None, alias="SUPABASE_JWKS_URL")
    supabase_audience: Optional[str] = Field(default=None, alias="SUPABASE_AUDIENCE")

    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-5-sonnet-latest", alias="ANTHROPIC_MODEL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
