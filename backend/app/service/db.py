"""Database helpers for Mongo-backed services."""
from __future__ import annotations

import os
from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

DEFAULT_MONGODB_URI = "mongodb://localhost:27017"
DEFAULT_DATABASE = "soundwave"


@lru_cache()
def _client_factory(uri: str) -> MongoClient:
    """Return a cached MongoDB client for the provided URI."""
    return MongoClient(uri)


def get_database() -> Database:
    """Return the configured MongoDB database instance."""
    uri = os.getenv("MONGODB_URI", DEFAULT_MONGODB_URI)
    database_name = os.getenv("MONGODB_DATABASE", DEFAULT_DATABASE)
    client = _client_factory(uri)
    return client[database_name]


__all__ = ["get_database"]
