"""Activity logging helpers for playlist events."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pymongo.database import Database


def log_playlist_activity(
    db: Database,
    event_type: str,
    playlist_id: str,
    user_id: str,
    payload: dict[str, Any] | None = None,
) -> None:
    """Persist playlist activity events for downstream recommendations."""
    record: dict[str, Any] = {
        "playlist_id": playlist_id,
        "event_type": event_type,
        "user_id": user_id,
        "created_at": datetime.utcnow(),
    }
    if payload:
        record["payload"] = payload
    db["playlist_activity"].insert_one(record)


__all__ = ["log_playlist_activity"]
