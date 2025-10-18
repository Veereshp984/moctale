"""Application configuration powered by Pydantic settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Shared configuration values loaded from environment variables."""

    project_name: str = Field(default="Full-Stack Starter API")
    api_prefix: str = Field(default="/api")
    version: str = Field(default="0.1.0")
    mongodb_uri: str = Field(alias="MONGODB_URI", default="mongodb://localhost:27017")
    secret_key: str = Field(alias="SECRET_KEY", default="change-me")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
