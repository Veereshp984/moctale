"""FastAPI service exposing recommendation and playlist endpoints."""
from __future__ import annotations

import os
import secrets
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field
from pymongo.database import Database

from app.model.recommender import RecommendationService
from app.service.activity import log_playlist_activity
from app.service.db import get_database

BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_ROOT = BASE_DIR.parent
DEFAULT_MODEL_DIR = BACKEND_ROOT / "models" / "latest"

app = FastAPI(title="Soundwave Recommendation Service", version="1.0.0")


class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: list[str]
    fallback_used: bool


class PlaylistBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1_000)

    model_config = ConfigDict(extra="forbid")


class PlaylistCreate(PlaylistBase):
    user_id: str = Field(..., min_length=1, max_length=200)
    is_public: bool = False
    invited_users: list[str] = Field(default_factory=list)


class PlaylistUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1_000)

    model_config = ConfigDict(extra="forbid")


class PlaylistItemCreate(BaseModel):
    source_id: str = Field(..., min_length=1, max_length=255, description="External identifier for the media item")
    media_type: Literal["movie", "music"]
    title: str | None = Field(default=None, max_length=255)

    model_config = ConfigDict(extra="forbid")


class PlaylistItemsRequest(BaseModel):
    items: list[PlaylistItemCreate] = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class PlaylistReorderRequest(BaseModel):
    order: list[str] = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class PlaylistItemResponse(BaseModel):
    item_id: str
    source_id: str
    media_type: Literal["movie", "music"]
    title: str | None
    position: int
    added_at: datetime

    model_config = ConfigDict(extra="ignore")


class PlaylistResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: str | None
    is_public: bool
    invited_users: list[str]
    share_token: str | None
    items: list[PlaylistItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(extra="ignore")


class PlaylistShareUpdate(BaseModel):
    is_public: bool | None = None
    invited_users: list[str] | None = None
    generate_invite: bool = False
    revoke_token: bool = False

    model_config = ConfigDict(extra="forbid")


class PlaylistShareResponse(BaseModel):
    id: str
    is_public: bool
    invited_users: list[str]
    share_token: str | None

    model_config = ConfigDict(extra="ignore")


playlist_router = APIRouter(prefix="/playlists", tags=["playlists"])


def _playlist_collection(db: Database):
    return db["playlists"]


def _ensure_object_id(playlist_id: str) -> ObjectId:
    try:
        return ObjectId(playlist_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=404, detail="Playlist not found") from None


def _get_playlist_or_404(db: Database, playlist_id: str) -> dict[str, Any]:
    playlist = _playlist_collection(db).find_one({"_id": _ensure_object_id(playlist_id)})
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist


def _normalise_invited_users(invited: list[str]) -> list[str]:
    seen: set[str] = set()
    normalised: list[str] = []
    for user in invited:
        if not user:
            continue
        if user not in seen:
            seen.add(user)
            normalised.append(user)
    return normalised


def _serialise_playlist(document: dict[str, Any]) -> PlaylistResponse:
    items = sorted(document.get("items", []), key=lambda item: item.get("position", 0))
    serialised_items = [
        PlaylistItemResponse(
            item_id=str(item["item_id"]),
            source_id=item["source_id"],
            media_type=item["media_type"],
            title=item.get("title"),
            position=int(item.get("position", 0)),
            added_at=item["added_at"],
        )
        for item in items
    ]
    return PlaylistResponse(
        id=str(document["_id"]),
        user_id=document["user_id"],
        name=document["name"],
        description=document.get("description"),
        is_public=bool(document.get("is_public", False)),
        invited_users=list(document.get("invited_users", [])),
        share_token=document.get("share_token"),
        items=serialised_items,
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )


@playlist_router.post("", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
def create_playlist(payload: PlaylistCreate, db: Database = Depends(get_database)) -> PlaylistResponse:
    now = datetime.utcnow()
    invited_users = _normalise_invited_users(payload.invited_users)
    document: dict[str, Any] = {
        "user_id": payload.user_id,
        "name": payload.name,
        "description": payload.description,
        "is_public": payload.is_public,
        "invited_users": invited_users,
        "items": [],
        "share_token": None,
        "created_at": now,
        "updated_at": now,
    }
    result = _playlist_collection(db).insert_one(document)
    document["_id"] = result.inserted_id
    log_playlist_activity(
        db,
        event_type="playlist_created",
        playlist_id=str(result.inserted_id),
        user_id=payload.user_id,
        payload={"is_public": payload.is_public, "item_count": 0},
    )
    return _serialise_playlist(document)


@playlist_router.get("/{playlist_id}", response_model=PlaylistResponse)
def get_playlist(playlist_id: str, db: Database = Depends(get_database)) -> PlaylistResponse:
    playlist = _get_playlist_or_404(db, playlist_id)
    return _serialise_playlist(playlist)


@playlist_router.patch("/{playlist_id}", response_model=PlaylistResponse)
def update_playlist(playlist_id: str, payload: PlaylistUpdate, db: Database = Depends(get_database)) -> PlaylistResponse:
    playlist = _get_playlist_or_404(db, playlist_id)
    updates: dict[str, Any] = {}
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.description is not None:
        updates["description"] = payload.description
    if not updates:
        return _serialise_playlist(playlist)
    updates["updated_at"] = datetime.utcnow()
    _playlist_collection(db).update_one({"_id": playlist["_id"]}, {"$set": updates})
    playlist.update(updates)
    log_playlist_activity(
        db,
        event_type="playlist_updated",
        playlist_id=str(playlist["_id"]),
        user_id=playlist["user_id"],
        payload={key: updates[key] for key in updates if key != "updated_at"},
    )
    return _serialise_playlist(playlist)


@playlist_router.post("/{playlist_id}/items", response_model=PlaylistResponse)
def add_playlist_items(
    playlist_id: str,
    request: PlaylistItemsRequest,
    db: Database = Depends(get_database),
) -> PlaylistResponse:
    playlist = _get_playlist_or_404(db, playlist_id)
    items: list[dict[str, Any]] = list(playlist.get("items", []))
    base_position = len(items)
    now = datetime.utcnow()
    new_items: list[dict[str, Any]] = []
    for offset, item_payload in enumerate(request.items):
        new_item = {
            "item_id": uuid4().hex,
            "source_id": item_payload.source_id,
            "media_type": item_payload.media_type,
            "title": item_payload.title,
            "position": base_position + offset,
            "added_at": now,
        }
        new_items.append(new_item)
        items.append(new_item)
    updates = {"items": items, "updated_at": now}
    _playlist_collection(db).update_one({"_id": playlist["_id"]}, {"$set": updates})
    playlist.update(updates)
    log_playlist_activity(
        db,
        event_type="playlist_items_added",
        playlist_id=str(playlist["_id"]),
        user_id=playlist["user_id"],
        payload={"item_ids": [item["item_id"] for item in new_items], "count": len(new_items)},
    )
    return _serialise_playlist(playlist)


@playlist_router.put("/{playlist_id}/items/reorder", response_model=PlaylistResponse)
def reorder_playlist_items(
    playlist_id: str,
    payload: PlaylistReorderRequest,
    db: Database = Depends(get_database),
) -> PlaylistResponse:
    playlist = _get_playlist_or_404(db, playlist_id)
    existing_items: list[dict[str, Any]] = list(playlist.get("items", []))
    if not existing_items:
        raise HTTPException(status_code=400, detail="Playlist has no items to reorder")
    desired_order = payload.order
    existing_ids = [item["item_id"] for item in existing_items]
    if len(desired_order) != len(existing_ids) or set(desired_order) != set(existing_ids):
        raise HTTPException(status_code=400, detail="Order must include each playlist item exactly once")
    item_lookup = {item["item_id"]: item for item in existing_items}
    reordered: list[dict[str, Any]] = []
    for position, item_id in enumerate(desired_order):
        item = item_lookup[item_id]
        item["position"] = position
        reordered.append(item)
    updates = {"items": reordered, "updated_at": datetime.utcnow()}
    _playlist_collection(db).update_one({"_id": playlist["_id"]}, {"$set": updates})
    playlist.update(updates)
    log_playlist_activity(
        db,
        event_type="playlist_items_reordered",
        playlist_id=str(playlist["_id"]),
        user_id=playlist["user_id"],
        payload={"order": desired_order},
    )
    return _serialise_playlist(playlist)


@playlist_router.delete("/{playlist_id}/items/{item_id}", response_model=PlaylistResponse)
def remove_playlist_item(playlist_id: str, item_id: str, db: Database = Depends(get_database)) -> PlaylistResponse:
    playlist = _get_playlist_or_404(db, playlist_id)
    items: list[dict[str, Any]] = list(playlist.get("items", []))
    try:
        index = next(index for index, item in enumerate(items) if item["item_id"] == item_id)
    except StopIteration as exc:
        raise HTTPException(status_code=404, detail="Playlist item not found") from exc
    removed_item = items.pop(index)
    for position, item in enumerate(items):
        item["position"] = position
    updates = {"items": items, "updated_at": datetime.utcnow()}
    _playlist_collection(db).update_one({"_id": playlist["_id"]}, {"$set": updates})
    playlist.update(updates)
    log_playlist_activity(
        db,
        event_type="playlist_item_removed",
        playlist_id=str(playlist["_id"]),
        user_id=playlist["user_id"],
        payload={"removed_item_id": removed_item["item_id"]},
    )
    return _serialise_playlist(playlist)


@playlist_router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_playlist(playlist_id: str, db: Database = Depends(get_database)) -> Response:
    playlist = _get_playlist_or_404(db, playlist_id)
    _playlist_collection(db).delete_one({"_id": playlist["_id"]})
    log_playlist_activity(
        db,
        event_type="playlist_deleted",
        playlist_id=str(playlist["_id"]),
        user_id=playlist["user_id"],
        payload={},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@playlist_router.put("/{playlist_id}/share", response_model=PlaylistShareResponse)
def update_playlist_sharing(
    playlist_id: str,
    payload: PlaylistShareUpdate,
    db: Database = Depends(get_database),
) -> PlaylistShareResponse:
    playlist = _get_playlist_or_404(db, playlist_id)
    if payload.generate_invite and payload.revoke_token:
        raise HTTPException(status_code=400, detail="Cannot generate and revoke an invite in the same request")
    updates: dict[str, Any] = {}
    if payload.is_public is not None:
        updates["is_public"] = payload.is_public
    if payload.invited_users is not None:
        updates["invited_users"] = _normalise_invited_users(payload.invited_users)
    share_token = playlist.get("share_token")
    if payload.generate_invite:
        share_token = secrets.token_urlsafe(10)
        updates["share_token"] = share_token
    if payload.revoke_token:
        share_token = None
        updates["share_token"] = None
    if updates:
        updates["updated_at"] = datetime.utcnow()
        _playlist_collection(db).update_one({"_id": playlist["_id"]}, {"$set": updates})
        playlist.update(updates)
        log_playlist_activity(
            db,
            event_type="playlist_share_updated",
            playlist_id=str(playlist["_id"]),
            user_id=playlist["user_id"],
            payload={key: updates[key] for key in updates if key not in {"updated_at"}},
        )
    return PlaylistShareResponse(
        id=str(playlist["_id"]),
        is_public=playlist.get("is_public", False),
        invited_users=list(playlist.get("invited_users", [])),
        share_token=playlist.get("share_token"),
    )


@playlist_router.get("/public", response_model=list[PlaylistResponse])
def list_public_playlists(db: Database = Depends(get_database)) -> list[PlaylistResponse]:
    cursor = _playlist_collection(db).find({"is_public": True}).sort("updated_at", -1)
    return [_serialise_playlist(document) for document in cursor]


@app.get("/share/{token}", response_model=PlaylistResponse)
def get_shared_playlist(token: str, db: Database = Depends(get_database)) -> PlaylistResponse:
    playlist = _playlist_collection(db).find_one({"share_token": token})
    if not playlist:
        raise HTTPException(status_code=404, detail="Shared playlist not found")
    return _serialise_playlist(playlist)


app.include_router(playlist_router)


@lru_cache()
def _service_factory(model_dir: str) -> RecommendationService:
    return RecommendationService(model_dir)


def get_service() -> RecommendationService:
    model_dir = Path(os.getenv("RECOMMENDER_MODEL_DIR", str(DEFAULT_MODEL_DIR))).resolve()
    try:
        return _service_factory(str(model_dir))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Model artifacts unavailable") from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/recommendations/{user_id}", response_model=RecommendationResponse)
def get_recommendations(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=100, description="Number of recommendations to return"),
    service: RecommendationService = Depends(get_service),
) -> RecommendationResponse:
    try:
        recommendations, fallback_used = service.recommend_for_user(user_id, limit)
    except Exception as exc:  # noqa: BLE001 - surface predictable error payload
        raise HTTPException(status_code=500, detail="Recommendation inference failed") from exc
    if not recommendations:
        raise HTTPException(status_code=404, detail="No recommendations available")
    return RecommendationResponse(user_id=user_id, recommendations=recommendations, fallback_used=fallback_used)
