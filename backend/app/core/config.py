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
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings.from_environment()
