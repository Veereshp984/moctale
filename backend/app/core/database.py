from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import Settings, get_settings


class MongoManager:
    def __init__(self) -> None:
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self._db_name: Optional[str] = None

    def init(self, settings: Settings | None = None, client: AsyncIOMotorClient | None = None) -> None:
        if settings is None:
            settings = get_settings()
        if client is None:
            client = AsyncIOMotorClient(settings.mongodb_url)
        self._client = client
        self._database = self._client[settings.mongodb_db_name]
        self._db_name = settings.mongodb_db_name

    def get_database(self) -> AsyncIOMotorDatabase:
        if self._database is None:
            raise RuntimeError("Mongo database has not been initialised")
        return self._database

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
        self._client = None
        self._database = None
        self._db_name = None

    def reset(self) -> None:
        self._client = None
        self._database = None
        self._db_name = None


mongo_manager = MongoManager()


def init_database(settings: Settings | None = None, client: AsyncIOMotorClient | None = None) -> None:
    mongo_manager.init(settings=settings, client=client)


def get_database() -> AsyncIOMotorDatabase:
    return mongo_manager.get_database()


def close_database() -> None:
    mongo_manager.close()
