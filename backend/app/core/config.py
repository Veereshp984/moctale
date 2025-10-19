from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "soundwave"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Discovery settings
    tmdb_api_key: str = ""
    tmdb_api_base: str = "https://api.themoviedb.org/3"

    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_token_url: str = "https://accounts.spotify.com/api/token"
    spotify_api_base: str = "https://api.spotify.com/v1"

    cache_ttl_seconds: int = 60
    log_level: str = "INFO"

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            mongodb_url=os.getenv("MONGODB_URL", cls.model_fields["mongodb_url"].default),
            mongodb_db_name=os.getenv("MONGODB_DB_NAME", cls.model_fields["mongodb_db_name"].default),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", cls.model_fields["jwt_secret_key"].default),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", cls.model_fields["jwt_algorithm"].default),
            access_token_expire_minutes=int(
                os.getenv(
                    "ACCESS_TOKEN_EXPIRE_MINUTES",
                    cls.model_fields["access_token_expire_minutes"].default,
                )
            ),
            tmdb_api_key=os.getenv("TMDB_API_KEY", cls.model_fields["tmdb_api_key"].default),
            tmdb_api_base=os.getenv("TMDB_API_BASE", cls.model_fields["tmdb_api_base"].default),
            spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID", cls.model_fields["spotify_client_id"].default),
            spotify_client_secret=os.getenv(
                "SPOTIFY_CLIENT_SECRET", cls.model_fields["spotify_client_secret"].default
            ),
            spotify_token_url=os.getenv("SPOTIFY_TOKEN_URL", cls.model_fields["spotify_token_url"].default),
            spotify_api_base=os.getenv("SPOTIFY_API_BASE", cls.model_fields["spotify_api_base"].default),
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", cls.model_fields["cache_ttl_seconds"].default)),
            log_level=os.getenv("LOG_LEVEL", cls.model_fields["log_level"].default),
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings.from_environment()
